# 1,000-User Agent Reranking Experiment Instructions

## 1. Scope

Run the agent reranking experiment on the fixed 1,000-user MovieLens-1M panel under four conditions:

1. Full input
2. Without demographics
3. Without persona
4. Without interaction history

Use identical profiles, users, candidate slates, and backbone data across the four conditions. The previous legacy MultiVAE experiment is outside this run. Do not use a legacy prompt or `legacy_combined` profile unless separately requested.

## 2. Setup

```bash
git clone https://github.com/m0onsoo/agent-recsys-reranking.git
cd agent-recsys-reranking
git checkout main
git pull --ff-only

python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Never commit `.env`, API keys, generated profiles, or raw experiment outputs.

Record the exact code version used:

```bash
git rev-parse HEAD
git status --short
```

`git status --short` should be empty. Report the actual commit SHA; no SHA is prescribed in advance.

## 3. Fixed conditions

- Dataset: MovieLens-1M
- Split: checkpoint-defined random-order 8:1:1 split
- Users: fixed 1,000-user panel sampled with seed 42
- Backbones: MF, LightGCN, vanilla MultiVAE
- Candidates: precomputed model-specific Top-20
- Evaluation: Recall@10 and NDCG@10
- Positive definition: every held-out interaction, independent of rating
- LLM: `gpt-4o-mini`, temperature 0
- Behavior protocol: `behavior-align-rating-social-traits`
- Primary reranking: converted item first, then original backbone order
- Additional evaluations: sampled baseline, click-only, and three-tier

Normal experiments do not require PyTorch, RecBole, checkpoints, or a separate MovieLens download.

## 4. Validate data before API calls

```bash
agent-reranking validate-bundle \
  --bundle data/derived/ml1m_ro_n1000_seed42
```

Expected:

```text
status: valid
num_users: 1000
models: MF, LightGCN, MultiVAE
candidate_size: 20
num_model_user_cases: 3000
has_social_traits: true
```

Expected identifiers:

```text
bundle_id: d50a678b62a6539147c0a0314ab3fb044a97177c9033fda2e1dbd604e7345ed5
panel_sha256: 76cdc352836afd33e23330affa5da3408756af08fc16bafbd5879a4d09425d3b
```

Check line counts:

```bash
wc -l \
  data/derived/ml1m_ro_n1000_seed42/candidates.jsonl \
  data/derived/ml1m_ro_n1000_seed42/evaluation_labels.jsonl \
  data/derived/ml1m_ro_n1000_seed42/train_interactions.jsonl \
  data/derived/ml1m_ro_n1000_seed42/users.csv
```

Expected counts are 3000, 1000, 1000, and 1001 respectively.

Verify backbone metrics:

```bash
python scripts/evaluate_bundle_baselines.py \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --top-k 10 \
  --output results/ml1m_ro_n1000_seed42_baselines_check.json
```

| Model | Recall@10 | NDCG@10 |
|---|---:|---:|
| MF | 0.1739993 | 0.2814531 |
| LightGCN | 0.2052061 | 0.3441975 |
| MultiVAE | 0.2048144 | 0.3300995 |

Do not start paid experiments if these checks fail or differ materially.

## 5. Generate 1,000 profiles

Use the fixed user file; do not resample.

```bash
agent-reranking generate-profiles \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_1000_seed42.csv \
  --method ours \
  --model gpt-4o-mini \
  --profile-components all \
  --history-size 10 \
  --seed 42 \
  --concurrency 20 \
  --requests-per-minute 300 \
  --tokens-per-minute 1000000 \
  --max-cost-usd 25 \
  --output-dir artifacts/profiles/ours_all_n1000
```

Expected output:

```text
artifacts/profiles/ours_all_n1000/
├── profiles.jsonl
├── profile_manifests.jsonl
└── run_manifest.json
```

Both JSONL files must contain exactly 1,000 lines:

```bash
wc -l \
  artifacts/profiles/ours_all_n1000/profiles.jsonl \
  artifacts/profiles/ours_all_n1000/profile_manifests.jsonl
```

Every profile must contain `user_id`, `raw_user_id`, `interaction_history`, `unique_tastes`, `social_traits`, and `demographics`. Each interaction history should contain 10 movies.

Profile generation currently has no durable partial resume. Run it on a stable connection. If it fails, preserve the logs and do not manually combine incomplete artifacts. Share generated profiles separately through secure storage rather than Git.

## 6. Full-input experiment

```bash
agent-reranking run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_1000_seed42.csv \
  --profiles artifacts/profiles/ours_all_n1000/profiles.jsonl \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-align-rating-social-traits \
  --profile-components all \
  --profile-protocol separated \
  --concurrency 20 \
  --requests-per-minute 300 \
  --tokens-per-minute 1000000 \
  --max-cost-usd 25 \
  --output-root results/n1000_align_rating/full/runs
```

The final manifest must report `status: complete` and `completed_cases: 3000`.

## 7. Without demographics

```bash
agent-reranking run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_1000_seed42.csv \
  --profiles artifacts/profiles/ours_all_n1000/profiles.jsonl \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-align-rating-social-traits \
  --profile-components history,unique_tastes,social_traits \
  --profile-protocol separated \
  --concurrency 20 \
  --requests-per-minute 300 \
  --tokens-per-minute 1000000 \
  --max-cost-usd 25 \
  --output-root results/n1000_align_rating/no_demographics/runs
```

## 8. Without persona

Here persona means the externally constructed `unique_tastes` and `social_traits`. Demographics and raw history remain available.

```bash
agent-reranking run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_1000_seed42.csv \
  --profiles artifacts/profiles/ours_all_n1000/profiles.jsonl \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-align-rating-social-traits \
  --profile-components history,demographics \
  --profile-protocol separated \
  --concurrency 20 \
  --requests-per-minute 300 \
  --tokens-per-minute 1000000 \
  --max-cost-usd 25 \
  --output-root results/n1000_align_rating/no_persona/runs
```

## 9. Without interaction history

```bash
agent-reranking run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_1000_seed42.csv \
  --profiles artifacts/profiles/ours_all_n1000/profiles.jsonl \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-align-rating-social-traits \
  --profile-components unique_tastes,social_traits,demographics \
  --profile-protocol separated \
  --concurrency 20 \
  --requests-per-minute 300 \
  --tokens-per-minute 1000000 \
  --max-cost-usd 25 \
  --output-root results/n1000_align_rating/no_interaction_history/runs
```

Do not run combined ablations unless separately requested. All four conditions reuse the same generated profile file.

## 10. Resume and sharding

For a partial agent run, repeat the exact original command and add:

```text
--resume /absolute/path/to/the/existing/run
```

Do not change any other setting. Historical rows may remain in `failures.jsonl`; verify that the manifest is complete, `completed_cases` is 3000, and `actions.jsonl` has 3,000 unique `(model, user_id)` pairs.

For distributed execution, use `--num-shards N` and `--shard-index I`. RPM, TPM, concurrency, and cost limits are process-local, so their totals across simultaneous shards must remain within the API provider limits.

Merge compatible completed shards with:

```bash
agent-reranking merge-runs \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --profiles artifacts/profiles/ours_all_n1000/profiles.jsonl \
  --runs RUN_DIR_0 RUN_DIR_1 RUN_DIR_2 RUN_DIR_3 RUN_DIR_4 \
  --output-root results/n1000_align_rating/CONDITION/merged
```

Never merge shards with different prompts, profiles, components, bundles, or model settings.

## 11. Required artifacts

Return the complete profile directory and, for each condition, all of:

```text
config.yaml
run_manifest.json
actions.jsonl
calls.jsonl
failures.jsonl
rankings.jsonl
per_user_metrics.csv
rating_stratified_metrics.csv
summary.csv
```

Also return:

- stdout and stderr logs
- `git rev-parse HEAD` and `git status --short`
- actual provider billing or dashboard cost
- execution start and completion times
- exact LLM model alias
- all shard directories, if applicable
- SHA-256 hashes for returned profiles and run artifacts

Do not commit generated profiles or raw experiment outputs.

## 12. Required summary

Provide a table with these columns:

| Condition | Model | Stage | Cases | Failures | Recorded cost | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|

Report `sampled_baseline`, `click_only`, `converted_then_original`, and `three_tier` separately.

Raw `actions.jsonl` is required to analyze:

- click-count distribution by Activity
- adjacent-click fraction by Diversity
- predicted-rating relationship with aggregate rating by Conformity
- confirmed/contradicted/insufficient outcomes
- watch/not-ready rate
- user-clustered bootstrap confidence intervals

Do not draw final conclusions until all four conditions are complete and all 3,000 model-user cases per condition have been verified.
