# Naturalized-profile 30-user w/o demographics audit

Job: `13697391`  
Run: `results/pilot30_natural_no_demographics/runs/20261103_112817_3d6050ce90`  
Full-input comparison: job `13691697`,
`results/pilot30_natural/runs/20261103_020258_f565e53509`

## Input and payload integrity

This run reuses the full-input pilot's fixed 30-user panel, profile evidence,
precomputed candidates, model list, prompts, and runtime settings. The saved configs
differ only in `output_root` and the intentional removal of `demographics` from
`profile_components`.

All 30 rendered payloads passed these checks:

- exact profile keys are `user_id`, `interaction_history`, `unique_tastes`, and
  `social_traits`;
- `demographics` is absent;
- `unique_tastes` is one natural-language string beginning with `Unique tastes:`;
- `social_traits` is one natural-language string beginning with
  `Social traits: activity is`.

Every successful action's `profile_hash` matches the no-demographics payload rendered
by the current code, and every `candidate_hash` matches the committed bundle slate.

## Run integrity and artifacts

The run completed 89 of 90 expected cases. It failed on exactly `(LightGCN, user 849)`
with the same out-of-slate click-selection error as the full-input run. Consequently,
the successful case sets are identical and all three sampled backbone baselines match
exactly, allowing direct aggregate comparison.

| File | Data rows |
|---|---:|
| `actions.jsonl` | 89 |
| `calls.jsonl` | 179 |
| `failures.jsonl` | 1 |
| `rankings.jsonl` | 89 |
| `per_user_metrics.csv` | 356 |
| `summary.csv` | 12 |
| `rating_stratified_metrics.csv` | 876 |

The recorded behavior-call cost is `$0.11794305`.

## Performance compared with naturalized full input

`Delta vs full` is the no-demographics result minus job `13691697` over the same
successful cases.

| Policy | Model | Recall@10 | Delta vs full | NDCG@10 | Delta vs full |
|---|---|---:|---:|---:|---:|
| converted then original | MF | 0.185255 | -0.000529 | 0.222059 | -0.004465 |
| converted then original | LightGCN | 0.218092 | +0.000000 | 0.269842 | +0.000794 |
| converted then original | MultiVAE | 0.194633 | +0.000000 | 0.236687 | +0.000180 |
| three tier | MF | 0.187967 | -0.003968 | 0.223226 | -0.004762 |
| three tier | LightGCN | 0.219943 | +0.006199 | 0.278331 | +0.008024 |
| three tier | MultiVAE | 0.195025 | -0.004033 | 0.242522 | -0.001371 |
| click only | MF | 0.187967 | -0.003968 | 0.238917 | -0.003079 |
| click only | LightGCN | 0.219943 | +0.006199 | 0.304664 | +0.011671 |
| click only | MultiVAE | 0.195025 | -0.004033 | 0.273853 | -0.000919 |

For the default `converted_then_original` policy, removing demographics has almost no
Recall effect, modestly reduces MF NDCG, and changes LightGCN/MultiVAE NDCG only
slightly in this pilot. Other policy directions remain model-dependent. These n=30
results validate the ablation path but are not population-level estimates.
