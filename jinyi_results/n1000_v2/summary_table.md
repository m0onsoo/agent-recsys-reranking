# 1,000 用户实验汇总

四个条件均已完成有界恢复与验收；最终缺失案例有单独清单，不以零分填补。
| Condition | Expected | Completed | Missing |
|---|---:|---:|---:|
| full | 3000 | 3000 | 0 |
| no_demographics | 3000 | 3000 | 0 |
| no_persona | 3000 | 3000 | 0 |
| no_interaction_history | 3000 | 3000 | 0 |

Changes are absolute differences against the same model's sampled backbone baseline.
Failures 是历史失败记录数，可能包含已恢复的案例；最终缺失数见上表。
Recorded cost is model-specific calls.jsonl cost, repeated across stages (do not sum stage rows).
See run_info.md for the more complete all-request ledger and profile costs.

| Condition | Model | Stage | Cases | Failures | Recorded cost | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | MF | sampled_baseline | 1000 | 7 | $1.957225 | 0.1739993 | 0.2814531 | +0.0000000 | +0.0000000 |
| full | MF | click_only | 1000 | 7 | $1.957225 | 0.1713738 | 0.2788160 | -0.0026255 | -0.0026371 |
| full | MF | converted_then_original | 1000 | 7 | $1.957225 | 0.1757549 | 0.2844783 | +0.0017556 | +0.0030252 |
| full | MF | three_tier | 1000 | 7 | $1.957225 | 0.1713844 | 0.2797724 | -0.0026149 | -0.0016807 |
| full | LightGCN | sampled_baseline | 1000 | 9 | $1.939790 | 0.2052061 | 0.3441975 | +0.0000000 | +0.0000000 |
| full | LightGCN | click_only | 1000 | 9 | $1.939790 | 0.2013455 | 0.3335033 | -0.0038607 | -0.0106942 |
| full | LightGCN | converted_then_original | 1000 | 9 | $1.939790 | 0.2055051 | 0.3391440 | +0.0002990 | -0.0050536 |
| full | LightGCN | three_tier | 1000 | 9 | $1.939790 | 0.2010041 | 0.3288434 | -0.0042021 | -0.0153542 |
| full | MultiVAE | sampled_baseline | 1000 | 5 | $1.949965 | 0.2048144 | 0.3300995 | +0.0000000 | +0.0000000 |
| full | MultiVAE | click_only | 1000 | 5 | $1.949965 | 0.1982353 | 0.3229700 | -0.0065792 | -0.0071295 |
| full | MultiVAE | converted_then_original | 1000 | 5 | $1.949965 | 0.2049780 | 0.3217460 | +0.0001636 | -0.0083535 |
| full | MultiVAE | three_tier | 1000 | 5 | $1.949965 | 0.1983158 | 0.3151574 | -0.0064986 | -0.0149422 |
| no_demographics | MF | sampled_baseline | 1000 | 0 | $1.943404 | 0.1739993 | 0.2814531 | +0.0000000 | +0.0000000 |
| no_demographics | MF | click_only | 1000 | 0 | $1.943404 | 0.1700668 | 0.2783065 | -0.0039325 | -0.0031466 |
| no_demographics | MF | converted_then_original | 1000 | 0 | $1.943404 | 0.1753831 | 0.2830784 | +0.0013838 | +0.0016253 |
| no_demographics | MF | three_tier | 1000 | 0 | $1.943404 | 0.1702577 | 0.2781561 | -0.0037416 | -0.0032970 |
| no_demographics | LightGCN | sampled_baseline | 1000 | 0 | $1.940099 | 0.2052061 | 0.3441975 | +0.0000000 | +0.0000000 |
| no_demographics | LightGCN | click_only | 1000 | 0 | $1.940099 | 0.1999608 | 0.3334885 | -0.0052454 | -0.0107091 |
| no_demographics | LightGCN | converted_then_original | 1000 | 0 | $1.940099 | 0.2054926 | 0.3391756 | +0.0002865 | -0.0050219 |
| no_demographics | LightGCN | three_tier | 1000 | 0 | $1.940099 | 0.1999352 | 0.3282185 | -0.0052709 | -0.0159790 |
| no_demographics | MultiVAE | sampled_baseline | 1000 | 0 | $1.944222 | 0.2048144 | 0.3300995 | +0.0000000 | +0.0000000 |
| no_demographics | MultiVAE | click_only | 1000 | 0 | $1.944222 | 0.1973841 | 0.3207705 | -0.0074303 | -0.0093290 |
| no_demographics | MultiVAE | converted_then_original | 1000 | 0 | $1.944222 | 0.2049334 | 0.3228941 | +0.0001190 | -0.0072054 |
| no_demographics | MultiVAE | three_tier | 1000 | 0 | $1.944222 | 0.1976639 | 0.3147294 | -0.0071506 | -0.0153701 |
| no_persona | MF | sampled_baseline | 1000 | 0 | $1.905828 | 0.1739993 | 0.2814531 | +0.0000000 | +0.0000000 |
| no_persona | MF | click_only | 1000 | 0 | $1.905828 | 0.1720538 | 0.2825858 | -0.0019455 | +0.0011327 |
| no_persona | MF | converted_then_original | 1000 | 0 | $1.905828 | 0.1754688 | 0.2855598 | +0.0014695 | +0.0041067 |
| no_persona | MF | three_tier | 1000 | 0 | $1.905828 | 0.1723283 | 0.2832618 | -0.0016710 | +0.0018088 |
| no_persona | LightGCN | sampled_baseline | 1000 | 0 | $1.894551 | 0.2052061 | 0.3441975 | +0.0000000 | +0.0000000 |
| no_persona | LightGCN | click_only | 1000 | 0 | $1.894551 | 0.2010515 | 0.3366838 | -0.0041547 | -0.0075137 |
| no_persona | LightGCN | converted_then_original | 1000 | 0 | $1.894551 | 0.2054161 | 0.3379723 | +0.0002099 | -0.0062252 |
| no_persona | LightGCN | three_tier | 1000 | 0 | $1.894551 | 0.2007333 | 0.3303941 | -0.0044728 | -0.0138034 |
| no_persona | MultiVAE | sampled_baseline | 1000 | 0 | $1.894149 | 0.2048144 | 0.3300995 | +0.0000000 | +0.0000000 |
| no_persona | MultiVAE | click_only | 1000 | 0 | $1.894149 | 0.1994109 | 0.3283128 | -0.0054036 | -0.0017868 |
| no_persona | MultiVAE | converted_then_original | 1000 | 0 | $1.894149 | 0.2047522 | 0.3235337 | -0.0000622 | -0.0065658 |
| no_persona | MultiVAE | three_tier | 1000 | 0 | $1.894149 | 0.1993416 | 0.3203371 | -0.0054728 | -0.0097624 |
| no_interaction_history | MF | sampled_baseline | 1000 | 0 | $1.469770 | 0.1739993 | 0.2814531 | +0.0000000 | +0.0000000 |
| no_interaction_history | MF | click_only | 1000 | 0 | $1.469770 | 0.1707666 | 0.2780224 | -0.0032327 | -0.0034306 |
| no_interaction_history | MF | converted_then_original | 1000 | 0 | $1.469770 | 0.1743215 | 0.2824513 | +0.0003222 | +0.0009983 |
| no_interaction_history | MF | three_tier | 1000 | 0 | $1.469770 | 0.1705335 | 0.2764176 | -0.0034658 | -0.0050354 |
| no_interaction_history | LightGCN | sampled_baseline | 1000 | 0 | $1.472223 | 0.2052061 | 0.3441975 | +0.0000000 | +0.0000000 |
| no_interaction_history | LightGCN | click_only | 1000 | 0 | $1.472223 | 0.1975750 | 0.3297011 | -0.0076311 | -0.0144964 |
| no_interaction_history | LightGCN | converted_then_original | 1000 | 0 | $1.472223 | 0.2059322 | 0.3383115 | +0.0007261 | -0.0058860 |
| no_interaction_history | LightGCN | three_tier | 1000 | 0 | $1.472223 | 0.1976205 | 0.3233089 | -0.0075857 | -0.0208886 |
| no_interaction_history | MultiVAE | sampled_baseline | 1000 | 0 | $1.474190 | 0.2048144 | 0.3300995 | +0.0000000 | +0.0000000 |
| no_interaction_history | MultiVAE | click_only | 1000 | 0 | $1.474190 | 0.1953318 | 0.3141753 | -0.0094826 | -0.0159242 |
| no_interaction_history | MultiVAE | converted_then_original | 1000 | 0 | $1.474190 | 0.2048362 | 0.3234314 | +0.0000218 | -0.0066681 |
| no_interaction_history | MultiVAE | three_tier | 1000 | 0 | $1.474190 | 0.1955941 | 0.3100815 | -0.0092203 | -0.0200180 |

## 最终缺失案例

- full: 0 个；清单 unrecovered_cases_full.json。
- no_demographics: 0 个；清单 unrecovered_cases_no_demographics.json。
- no_persona: 0 个；清单 unrecovered_cases_no_persona.json。
- no_interaction_history: 0 个；清单 unrecovered_cases_no_interaction_history.json。
