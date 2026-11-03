# Naturalized 30-user behavior v1 vs v2 audit

V1 job: `13697460`  
V1 run: `results/pilot30_natural_v1/runs/20261103_113700_2481aec53a`  
V2 comparison: job `13691697`,
`results/pilot30_natural/runs/20261103_020258_f565e53509`

## Treatment and integrity

The saved configurations differ only in `output_root` and `prompt_version`. V1 omits
candidate `average_rating` and its explanatory prompt text at click and conversion;
V2 supplies the train-only aggregate mean rating at both stages. Both runs use the
same users, naturalized profile payloads, candidate slates, GPT-4o-mini alias, and all
other runtime settings.

V1 completed 90/90 cases with no failures. V2 completed 89/90 because
`(LightGCN, user 849)` returned an out-of-slate click. Every V1 action has the expected
current profile and candidate hash. All 89 common cases have identical profile and
candidate hashes between versions.

LightGCN comparisons below use only the 29 users common to both runs. MF and MultiVAE
each use all 30 users.

## Paired performance: V1 minus V2

| Policy | Model | V1 Recall@10 | Delta vs V2 | V1 NDCG@10 | Delta vs V2 |
|---|---|---:|---:|---:|---:|
| converted then original | MF | 0.192397 | +0.006614 | 0.239811 | +0.013286 |
| converted then original | LightGCN | 0.216009 | -0.002084 | 0.294279 | +0.025230 |
| converted then original | MultiVAE | 0.191603 | -0.003030 | 0.248384 | +0.011877 |
| three tier | MF | 0.180930 | -0.011005 | 0.234545 | +0.006558 |
| three tier | LightGCN | 0.208498 | -0.005247 | 0.283804 | +0.013498 |
| three tier | MultiVAE | 0.189260 | -0.009799 | 0.248516 | +0.004623 |
| click only | MF | 0.180930 | -0.011005 | 0.239531 | -0.002464 |
| click only | LightGCN | 0.208498 | -0.005247 | 0.288167 | -0.004826 |
| click only | MultiVAE | 0.189260 | -0.009799 | 0.276806 | +0.002034 |

For the default `converted_then_original` policy, V1 improves NDCG over V2 for all
three models. Recall improves for MF but is slightly lower for LightGCN and MultiVAE.

Relative to its own paired backbone baseline, V1 default-policy changes are:

| Model | Recall change | NDCG change |
|---|---:|---:|
| MF | +0.00% | -0.51% |
| LightGCN | +0.25% | approximately 0.00% |
| MultiVAE | -1.56% | -8.96% |

V1 therefore largely removes the severe MF and LightGCN NDCG losses seen under V2,
but MultiVAE remains substantially worse than its backbone on NDCG.

## Observable reasoning shift

The behavior artifacts contain short click motives and conversion decision notes, not
private chain-of-thought. Keyword auditing of those observable texts gives:

| Version | Reason texts | Rating references | Preference/taste references | Trait-label references |
|---|---:|---:|---:|---:|
| V1, no aggregate rating | 1,114 | 7 | 536 | 0 |
| V2, aggregate rating | 982 | 783 | 279 | 0 |

The few V1 rating words can originate from natural-language taste evidence derived
from historical ratings; V1 does not expose a candidate `average_rating` field. V2's
aggregate-rating signal dominates its observable justifications and coincides with
worse default-policy NDCG in this pilot. Neither version explicitly cites the supplied
Activity, Conformity, or Diversity labels.

The versions change almost every click set in the paired sample: 30/30 MF, 29/29
LightGCN, and 30/30 MultiVAE cases. Conversion sets change in 25/30, 26/29, and 22/30
cases respectively. Results remain exploratory because n=30 is small and the live
GPT-4o-mini alias is not seed- or revision-pinned.
