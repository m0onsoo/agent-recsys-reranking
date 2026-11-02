# Agent Reranking Bench

Reproducible MovieLens-1M experiments for LLM-agent click/conversion simulation and
post-hoc reranking. A fixed user panel, registered checkpoints, generated profiles,
raw actions, and metrics are kept as separate versioned artifacts so the same agent
actions can be evaluated under every reranking policy without paying for another run.

## What is fixed

- Dataset: MovieLens 1M, random-order (`RO`) split from the registered checkpoints.
- Eligible users: at least 10 train interactions and at least one held-out item in
  every registered model's full-sort Top-20. Eligibility must hold jointly for MF,
  LightGCN, and vanilla MultiVAE.
- Panel: the already sampled 1,000 users in
  `data/panels/users_1000_seed42.csv`. This repository never resamples it.
- Primary relevance: every held-out interaction, independent of rating. Rating
  strata are additionally written for secondary analysis.
- Candidate order: the registered backbone model's score order.
- Default reranking: converted items first; all remaining items retain backbone
  order. `click_only` and `three_tier` are computed from the same action record.

The fixed CSV should contain `user_id` and `raw_user_id`. Keep provenance columns
such as seed, train count, and each model's Top-20 positive count when available.
`prepare-bundle` independently rejects a panel member who violates joint Top-20
eligibility, preventing a stale or incompatible panel from silently running.

## Data and environment

MovieLens 1M's official source is:

`https://files.grouplens.org/datasets/movielens/ml-1m.zip`

GroupLens asks users not to redistribute the dataset without separate permission.
Raw and derived interaction files are therefore ignored by Git; every collaborator
downloads the official archive locally.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
agent-reranking download-data --output-root data/raw --convert-root data/recbole
```

Checkpoint loading also needs the environment used to train the RecBole models.
Set these site-specific paths before materializing a bundle:

```bash
export MODEL_ARTIFACT_ROOT=/path/to/checkpoints
agent-reranking prepare-bundle \
  --panel data/panels/users_1000_seed42.csv \
  --registry registry/models.yaml \
  --recbole-root /path/to/RecBole \
  --recbole-debias-root /path/to/Recbole-Debias \
  --dataset-root data/recbole \
  --extended-movie-path /optional/path/ml1m_extended_movie.csv \
  --candidate-size 20 \
  --output-dir data/derived/ml1m_ro_n1000_seed42
```

This reconstructs each checkpoint's exact train/test split, verifies checkpoint,
mapping, and split hashes, and writes local JSONL inputs. Social-trait thresholds
are calculated over all checkpoint train users—not just the selected panel.

## Profile generation

```bash
cp .env.example .env                 # then set OPENAI_API_KEY
agent-reranking generate-profiles \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --method ours \
  --num-users 1000 \
  --concurrency 20 \
  --output-dir artifacts/profiles/ours_all
```

Methods:

- `ours` (default): the current controlled pipeline. Taste extraction uses the
  existing Agent4Rec-style rating rule (rating >= 3 is positive), exact v3 prompt,
  and a deterministic unordered 25-item train sample. Runtime inputs use independent
  `unique_tastes`, `social_traits`, `interaction_history`, and `demographics` keys.
- `agent4rec`: a separately labeled Agent4Rec-inspired profile adapter.
- `simuser`: a three-call SimUSER-inspired taste, candidate-persona, and consistency
  adapter. It is an auditable adaptation, not a claim of bit-for-bit reproduction of
  the authors' private serving environment.

Thus our current taste-summary logic is Agent4Rec-derived, but the complete profile
is not identical to Agent4Rec because it adds controlled components and uses the
current action prompts. Keep `method`, components, and prompt versions in comparisons.

Profile input ablations accept either a component allow-list or `--no-use-*` flags:

```bash
# w/o demographics
agent-reranking generate-profiles --bundle data/derived/ml1m_ro_n1000_seed42 \
  --method ours --no-use-demographics --output-dir artifacts/profiles/ours_no_demo

# unique tastes and history only
agent-reranking generate-profiles --bundle data/derived/ml1m_ro_n1000_seed42 \
  --profile-components unique_tastes,history --output-dir artifacts/profiles/tastes_history
```

Available components are `history`, `unique_tastes`, `social_traits`, and `demographics`;
all are enabled by default. Pickiness is deliberately excluded because it was not
part of the established profile protocol. To reproduce an earlier experiment
without regenerating personas, add `--persona-file /path/to/personas.jsonl`. Users
are matched by raw MovieLens user ID and missing users cause a hard failure.

The default `separated` profile protocol sends those components as distinct JSON keys
and never repeats social traits inside a combined summary. `--profile-protocol
legacy_combined` is reserved for historical reproduction: it reconstructs the old
single `persona_summary` string and must not be used as the new 1,000-user default.

`prepare-bundle --allow-ineligible` exists only for regression-testing a historical
panel that predates the current registry. Never use it to create the 1,000-user study
bundle; the default joint-positive check is part of that study's inclusion criteria.

## Run the agent

```bash
agent-reranking run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --profiles artifacts/profiles/ours_all/profiles.jsonl
```

Defaults live in `configs/default.yaml`: `num_users=1000`, `candidate_size=20`,
`top_k=10`, `concurrency=20`, `requests_per_minute=300`,
`tokens_per_minute=1,000,000`, `max_cost_usd=25`, two validation retries, and one
shard. The safety controls mean:

- `--concurrency`: maximum simultaneous API workers; lower it after 429/timeouts.
- `--requests-per-minute`: sliding-window request cap shared by workers.
- `--tokens-per-minute`: estimated input/output token admission cap.
- `--max-cost-usd`: process-level circuit breaker based on API token usage.
- `--case-limit`: run only this many model-user cases, useful for smoke tests.
- `--resume RUN_DIR`: skip already durable `(model,user)` action records. The saved
  configuration must match exactly.
- `--num-shards N --shard-index I`: deterministic disjoint partition where
  `0 <= I < N`; use the same bundle/config on each machine.

After every shard finishes, merge the durable actions and recompute one global table
without API calls:

```bash
agent-reranking merge-runs \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --profiles artifacts/profiles/ours_all/profiles.jsonl \
  --runs results/runs/SHARD_0 results/runs/SHARD_1 \
  --output-root results/runs
```

The merger requires exactly all shard indices, rejects configuration differences and
conflicting duplicate actions, and writes a normal combined run directory.

`--no-use-demographics` and the other component flags also work at run time. This
lets one generated superset profile support controlled input ablations, though a
taste profile that was originally generated from different inputs must not be mislabeled.

Every successful model-user case is flushed and fsynced immediately. A run directory
contains `actions.jsonl`, `calls.jsonl`, `failures.jsonl`, `rankings.jsonl`,
`per_user_metrics.csv`, `rating_stratified_metrics.csv`, `summary.csv`, its exact
configuration, and a manifest. `results/index.csv` is created on the first run and
upserted thereafter. `actions.jsonl` is the costly artifact; all four rankings are
deterministic post-processing of it:

- `sampled_baseline`: original backbone order
- `click_only`: clicked, then unclicked in backbone order
- `converted_then_original`: converted, then everything else in backbone order
- `three_tier`: converted, clicked-but-not-converted, then unclicked

## Smoke tests and collaboration

```bash
python -m unittest discover -s tests -v
agent-reranking generate-profiles --client mock --num-users 2 \
  --bundle data/derived/ml1m_ro_n1000_seed42 --output-dir /tmp/mock_profiles
agent-reranking run --llm-provider mock --num-users 2 --case-limit 3 \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --profiles /tmp/mock_profiles/profiles.jsonl --output-root /tmp/mock_runs
```

Do not commit `.env`, API keys, raw MovieLens rows, derived bundles, or raw API
transcripts. Do commit the fixed panel, registry changes, prompts, code, tests, and
small aggregate metric tables. Make one commit per logical experiment change and
record the resulting commit SHA with any shared result.

For 50-user reproduction on the original machine, see
`scripts/reproduce_50user.sh`. It imports the existing personas, removes demographics,
and uses the latest registered checkpoints and current v4 action prompts. On the USC
cluster, submit `sbatch scripts/reproduce_50user.sbatch` after materialization because
the login node cannot resolve the API endpoint.

To reproduce the four historical 50-user input conditions as a Slurm array, submit
`sbatch scripts/reproduce_50user_ablations.sbatch`. Array indices correspond to full,
w/o demographics, w/o persona (both tastes and embedded social traits removed), and
w/o interaction history.
