# Legacy experiment to GitHub pipeline mapping

This document maps the original `click_conversion_reranker` experiment path to
`agent-reranking-bench`. It separates the audited 50-user legacy reproduction
path from the new 1,000-user default path. Those two profile protocols are not
the same experiment.

## Result being reproduced

The quoted no-demographics row is composite:

| Backbone | Source run | Converted-first Recall@10 / NDCG@10 |
|---|---|---:|
| MF | `20261025_2257_mf-lightgcn-multivae_gpt-4o-mini_c73f80e4` | 0.155263 / 0.232017 |
| LightGCN | same run | 0.188296 / 0.279746 |
| vanilla MultiVAE | `20261029_0002_multivae_gpt-4o-mini_8656a32e` | 0.186272 / 0.265941 |

The MF/LightGCN run contained the older non-vanilla MultiVAE checkpoint, so its
MultiVAE row is not used. The vanilla MultiVAE number comes from the later
replacement run.

## One-to-one execution mapping

| Stage | Original code | GitHub code | Audited status for 50-user no-demographics |
|---|---|---|---|
| Slurm entry | `slurm/run_50user_all_ratings_ro_mf_v4_ablation.sbatch` | `scripts/reproduce_50user_ablations.sbatch` task 1 | Same condition, models, n=50, k=20, concurrency=20 |
| CLI/config override | `run_m4.main` | `agent_reranking.cli.main` | Same effective legacy settings; names differ |
| Main orchestration | `reranker.experiment.run_experiment` and `run_cases` | `agent_reranking.runner.run` | Model-by-model, batches of 20 restored in `a13b49a` |
| User panel | `reranker.panel.load_panel` | materialized `data/derived/repro50/users.csv` | Same ordered panel; SHA-256 `8bb9fad4...` |
| Checkpoint load | `reranker.checkpoints.CheckpointAdapter` | `agent_reranking.checkpoints.CheckpointAdapter`, invoked by `prepare_bundle` | Same checkpoint SHA, mapping hash, and split hash |
| Model registry | config paths plus validation report | `registry/models.yaml` | Same MF, LightGCN, vanilla MultiVAE artifacts |
| Top-20 inference | `CheckpointAdapter.candidates` at run time | same algorithm during `prepare_bundle`, then `candidates.jsonl` | 150/150 candidate ID lists and orders equal |
| Candidate scores | live tensors converted to floats | materialized JSON floats | max absolute difference `3.814697e-06`; order unchanged |
| Held-out labels | `adapter.test_positives` | `evaluation_labels.jsonl` | Equal; all three baselines reproduce to about 1e-9 |
| Runtime history sampling | `ProfileBuilder.history_rows` | `_runtime_history_sample` | Same SHA-256-derived per-user seed; 50/50 item sequences equal |
| History metadata | `ProfileBuilder.build` + `MovieMetadata.detail` | imported bundle + `generate_profiles` | 50/50 serialized profiles equal in legacy no-demographics mode |
| Persona | `ProfileBuilder._load_personas` using v3 persona file | `generate_profiles(..., persona_file=...)` | Same imported `summary`; no persona API calls |
| Profile payload | `TwoStageAgent.simulate` filters to `user_id`, history, `persona_summary` | `_profile_payload(..., protocol="legacy_combined")` | 50/50 equal; demographics absent |
| Click prompt loader | `BehaviorPromptTemplates` | `TwoStageAgent.__init__` | Same file, `.strip()`, and history substitution after `ed2efa1` |
| Conversion prompt | `BehaviorPromptTemplates.render` | `TwoStageAgent.simulate` | Exact original full-slate substitution restored in `ed2efa1` |
| Prompt files | parent `prompts/click_behavior_v4_motive_assessment.txt` and conversion counterpart | copied files under repository `prompts/` | SHA-256 equal |
| Basic candidate JSON | `MovieMetadata.basic` | bundle catalog projection | 150/150 full click user payloads equal |
| Clicked detail JSON | `MovieMetadata.detail` | catalog projection with explicit legacy defaults | Missing `unknown`/`[]` fields restored in `c66bf34` |
| HTTP request | `OpenAICompatibleChatClient.respond` | `OpenAICompatibleClient.respond_json` | model, temperature, messages, and response format byte-equal in frozen normal/retry tests |
| Click response mode | `json_object` | `json_object` | Equal |
| Conversion schema | dynamic strict JSON schema keyed by clicked IDs | same | Equal, including retry enum |
| Local validation | Draft 2020-12 schema + motive key/sentence checks | same after `a13b49a` | Equal validation and feedback rules |
| Retry instruction | appended to system prompt; feedback also in user JSON | same after `ed2efa1`/`a13b49a` | Frozen click and conversion retry requests byte-equal |
| Conversion policy | `policy.rerank(..., "converted_then_original")` | `rerank(..., "converted_then_original")` | Equal: converted first, original score order for remainder |
| Click policy | `policy.rerank(..., stage="click")` | `all_rankings(...)["click_only"]` | Equal tier and score ordering |
| Recall/NDCG | RecBole-backed `RankingEvaluator` | dependency-free `metrics.evaluate` | Replaying original actions reproduces metrics to floating-point precision |
| Aggregate | `RunArtifacts.write_metrics` | `results.summarize` | Arithmetic mean over the same 50 per-user metrics |

## Effective no-demographics settings

| Setting | Value |
|---|---|
| users | fixed ordered legacy panel of 50 |
| backbones | MF, LightGCN, vanilla MultiVAE |
| split | MovieLens-1M all-rating RO |
| candidates | each backbone's original Top-20 |
| final ranking | Top-10 |
| relevance | every held-out test interaction, independent of rating |
| profile | unordered 10-item checkpoint-train sample + imported v3 persona summary |
| demographics | disabled |
| click input | user profile + basic metadata for the complete Top-20 |
| conversion input | same complete basic slate + details for clicked items + click motives |
| LLM | `gpt-4o-mini`, temperature 0, no seed parameter |
| prompt | `behavior-v4-motive-assessment` |
| local LLM cache | disabled in fresh comparisons; GitHub runner has no response reuse cache |
| retry count | 2 |
| concurrency | 20, model-by-model batches |
| conversion rerank | converted item first; all others retain backbone order |

## Evidence that the metric difference comes from actions

Original-code actions replayed through the migrated post-processing and metric
code produce the original-code metrics exactly. Checkpoints, candidates,
labels, reranking, and evaluation therefore do not explain the discrepancy.

Recall@10 changes are extremely sparse:

| Run | Backbone | users improved / unchanged / harmed |
|---|---|---:|
| earlier reported | MF | 3 / 46 / 1 |
| earlier reported | LightGCN | 2 / 48 / 0 |
| earlier reported | vanilla MultiVAE | 1 / 48 / 1 |
| final migrated run | MF | 1 / 48 / 1 |
| final migrated run | LightGCN | 1 / 49 / 0 |
| final migrated run | vanilla MultiVAE | 0 / 49 / 1 |

Thus one or two changed conversion choices can move the 50-user aggregate and
its relative percentage substantially. Between the fresh original-code run and
the final migrated run, exact converted sets match for only 25/50 MF, 29/50
LightGCN, and 27/50 MultiVAE cases despite equivalent request construction.

## Remaining differences and non-equivalences

These must not be confused with the audited legacy no-demographics path:

1. **The default 1,000-user profile protocol is intentionally different.** It
   sends `unique_tastes`, `social_traits`, and `demographics` as separate keys.
   The historical experiment sent one combined `persona_summary` string.
2. **Fresh `ours` profile generation is not yet an exact port of persona v3.**
   Its sampling hash namespace, prompt whitespace handling, shown fields
   (`preference_label`), response validation, retry behavior, and output
   provenance differ. The 50-user reproduction avoids this path by importing
   the original persona file.
3. **Demographic values differ outside no-demographics mode.** The original
   runtime maps MovieLens codes to readable labels; the bundle currently stores
   raw codes. This does not affect the no-demographics condition.
4. **Bundle metadata preparation is less defensive.** The original
   `MovieMetadata` audits duplicate IDs, title/year consistency, and mapping
   status. The materializer currently joins extended data directly by MovieID.
   The audited 50-user candidate/profile payloads match after default-field
   restoration, but a new 1,000-user bundle needs the same mapping audit.
5. **The GitHub client has rate/cost circuit breakers.** At the configured
   limits they do not alter request bodies, but they can alter request timing.
6. **Failure-attempt logging differs.** The original logs every attempt
   immediately; the GitHub runner currently persists call rows after a case
   succeeds. This affects audit artifacts for terminal failures, not successful
   actions.
7. **The live model is not pinned to a revision.** Both paths request the alias
   `gpt-4o-mini` without a seed. Temperature zero does not guarantee identical
   responses, and the clients do not retain the API `system_fingerprint`.

## Review order

For manual review, inspect in this order:

1. `scripts/reproduce_50user_ablations.sbatch`
2. `configs/default.yaml` and `registry/models.yaml`
3. `agent_reranking/runner.py::_profile_payload` and `run`
4. `agent_reranking/agent.py::TwoStageAgent`
5. `agent_reranking/client.py::OpenAICompatibleClient`
6. the two v4 motive-assessment prompt files
7. `agent_reranking/rerank.py`
8. `agent_reranking/metrics.py`
9. `tests/test_legacy_request_parity.py`

The corresponding original files are `run_m4.py`, `reranker/experiment.py`,
`reranker/profiles.py`, `reranker/prompts.py`, `reranker/openai_client.py`,
`reranker/agent.py`, `reranker/policy.py`, and `reranker/evaluation.py`.
