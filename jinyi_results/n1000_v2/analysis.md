# 描述性分析

以下为描述性结果；分析在四条件有界恢复和验收结束后进行。
| Condition | Expected | Completed | Missing |
|---|---:|---:|---:|
| full | 3000 | 3000 | 0 |
| no_demographics | 3000 | 3000 | 0 |
| no_persona | 3000 | 3000 | 0 |
| no_interaction_history | 3000 | 3000 | 0 |

The panel is fixed and conditioned on at least one held-out positive in every backbone's Top-20.
Relevance is every held-out interaction, regardless of rating; findings do not generalize to all MovieLens users.
Costs are estimates, not verified proxy bills. Check actual billing on the dashboard.

## Paired User-Clustered Bootstrap

95% percentile intervals; 2,000 resamples of completed user clusters, seed 42.
Each sampled user contributes both baseline and reranked metrics; changes are absolute, not relative.
Same cluster draws are reused within each condition/model across stages and metrics; no multiplicity adjustment.
若存在缺失，各条件/模型的完成用户集合可能不同，跨条件比较不再完全配对；缺失用户不填补。
The sampled_baseline delta and interval are identically zero.

| Condition | Model | Stage | Metric | Change | 95% CI lower | 95% CI upper |
|---|---|---|---|---:|---:|---:|
| full | MF | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | MF | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | MF | click_only | recall@10 | -0.0026255 | -0.0092421 | +0.0042865 |
| full | MF | click_only | ndcg@10 | -0.0026371 | -0.0090644 | +0.0039872 |
| full | MF | converted_then_original | recall@10 | +0.0017556 | +0.0004343 | +0.0031660 |
| full | MF | converted_then_original | ndcg@10 | +0.0030252 | -0.0025061 | +0.0085777 |
| full | MF | three_tier | recall@10 | -0.0026149 | -0.0091942 | +0.0042478 |
| full | MF | three_tier | ndcg@10 | -0.0016807 | -0.0095935 | +0.0067234 |
| full | LightGCN | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | LightGCN | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | LightGCN | click_only | recall@10 | -0.0038607 | -0.0092879 | +0.0018625 |
| full | LightGCN | click_only | ndcg@10 | -0.0106942 | -0.0173041 | -0.0040469 |
| full | LightGCN | converted_then_original | recall@10 | +0.0002990 | -0.0012328 | +0.0019330 |
| full | LightGCN | converted_then_original | ndcg@10 | -0.0050536 | -0.0102727 | -0.0001835 |
| full | LightGCN | three_tier | recall@10 | -0.0042021 | -0.0097774 | +0.0015089 |
| full | LightGCN | three_tier | ndcg@10 | -0.0153542 | -0.0230541 | -0.0075833 |
| full | MultiVAE | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | MultiVAE | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| full | MultiVAE | click_only | recall@10 | -0.0065792 | -0.0124465 | -0.0004562 |
| full | MultiVAE | click_only | ndcg@10 | -0.0071295 | -0.0132809 | -0.0007731 |
| full | MultiVAE | converted_then_original | recall@10 | +0.0001636 | -0.0007800 | +0.0009341 |
| full | MultiVAE | converted_then_original | ndcg@10 | -0.0083535 | -0.0131525 | -0.0033823 |
| full | MultiVAE | three_tier | recall@10 | -0.0064986 | -0.0123057 | -0.0003497 |
| full | MultiVAE | three_tier | ndcg@10 | -0.0149422 | -0.0223099 | -0.0074659 |
| no_demographics | MF | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | MF | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | MF | click_only | recall@10 | -0.0039325 | -0.0109249 | +0.0032355 |
| no_demographics | MF | click_only | ndcg@10 | -0.0031466 | -0.0101644 | +0.0038912 |
| no_demographics | MF | converted_then_original | recall@10 | +0.0013838 | +0.0000946 | +0.0027239 |
| no_demographics | MF | converted_then_original | ndcg@10 | +0.0016253 | -0.0038035 | +0.0070878 |
| no_demographics | MF | three_tier | recall@10 | -0.0037416 | -0.0107441 | +0.0035087 |
| no_demographics | MF | three_tier | ndcg@10 | -0.0032970 | -0.0115820 | +0.0051894 |
| no_demographics | LightGCN | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | LightGCN | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | LightGCN | click_only | recall@10 | -0.0052454 | -0.0109760 | +0.0004695 |
| no_demographics | LightGCN | click_only | ndcg@10 | -0.0107091 | -0.0172913 | -0.0040323 |
| no_demographics | LightGCN | converted_then_original | recall@10 | +0.0002865 | -0.0010264 | +0.0016726 |
| no_demographics | LightGCN | converted_then_original | ndcg@10 | -0.0050219 | -0.0103548 | +0.0001849 |
| no_demographics | LightGCN | three_tier | recall@10 | -0.0052709 | -0.0110227 | +0.0004307 |
| no_demographics | LightGCN | three_tier | ndcg@10 | -0.0159790 | -0.0241891 | -0.0078913 |
| no_demographics | MultiVAE | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | MultiVAE | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_demographics | MultiVAE | click_only | recall@10 | -0.0074303 | -0.0134871 | -0.0013074 |
| no_demographics | MultiVAE | click_only | ndcg@10 | -0.0093290 | -0.0156528 | -0.0030778 |
| no_demographics | MultiVAE | converted_then_original | recall@10 | +0.0001190 | -0.0009254 | +0.0010697 |
| no_demographics | MultiVAE | converted_then_original | ndcg@10 | -0.0072054 | -0.0121879 | -0.0022371 |
| no_demographics | MultiVAE | three_tier | recall@10 | -0.0071506 | -0.0132332 | -0.0009932 |
| no_demographics | MultiVAE | three_tier | ndcg@10 | -0.0153701 | -0.0228951 | -0.0078293 |
| no_persona | MF | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | MF | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | MF | click_only | recall@10 | -0.0019455 | -0.0082901 | +0.0046839 |
| no_persona | MF | click_only | ndcg@10 | +0.0011327 | -0.0048326 | +0.0069971 |
| no_persona | MF | converted_then_original | recall@10 | +0.0014695 | -0.0002603 | +0.0031844 |
| no_persona | MF | converted_then_original | ndcg@10 | +0.0041067 | -0.0012594 | +0.0096308 |
| no_persona | MF | three_tier | recall@10 | -0.0016710 | -0.0081425 | +0.0049434 |
| no_persona | MF | three_tier | ndcg@10 | +0.0018088 | -0.0057491 | +0.0098566 |
| no_persona | LightGCN | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | LightGCN | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | LightGCN | click_only | recall@10 | -0.0041547 | -0.0093243 | +0.0010802 |
| no_persona | LightGCN | click_only | ndcg@10 | -0.0075137 | -0.0131520 | -0.0017070 |
| no_persona | LightGCN | converted_then_original | recall@10 | +0.0002099 | -0.0013789 | +0.0018118 |
| no_persona | LightGCN | converted_then_original | ndcg@10 | -0.0062252 | -0.0112522 | -0.0009073 |
| no_persona | LightGCN | three_tier | recall@10 | -0.0044728 | -0.0096927 | +0.0008715 |
| no_persona | LightGCN | three_tier | ndcg@10 | -0.0138034 | -0.0207551 | -0.0066968 |
| no_persona | MultiVAE | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | MultiVAE | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_persona | MultiVAE | click_only | recall@10 | -0.0054036 | -0.0100829 | -0.0002530 |
| no_persona | MultiVAE | click_only | ndcg@10 | -0.0017868 | -0.0073002 | +0.0038047 |
| no_persona | MultiVAE | converted_then_original | recall@10 | -0.0000622 | -0.0007182 | +0.0004805 |
| no_persona | MultiVAE | converted_then_original | ndcg@10 | -0.0065658 | -0.0113744 | -0.0016337 |
| no_persona | MultiVAE | three_tier | recall@10 | -0.0054728 | -0.0101681 | -0.0003887 |
| no_persona | MultiVAE | three_tier | ndcg@10 | -0.0097624 | -0.0167107 | -0.0026723 |
| no_interaction_history | MF | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | MF | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | MF | click_only | recall@10 | -0.0032327 | -0.0100971 | +0.0040544 |
| no_interaction_history | MF | click_only | ndcg@10 | -0.0034306 | -0.0105568 | +0.0040589 |
| no_interaction_history | MF | converted_then_original | recall@10 | +0.0003222 | -0.0009118 | +0.0014741 |
| no_interaction_history | MF | converted_then_original | ndcg@10 | +0.0009983 | -0.0042101 | +0.0062531 |
| no_interaction_history | MF | three_tier | recall@10 | -0.0034658 | -0.0103391 | +0.0038498 |
| no_interaction_history | MF | three_tier | ndcg@10 | -0.0050354 | -0.0135100 | +0.0040111 |
| no_interaction_history | LightGCN | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | LightGCN | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | LightGCN | click_only | recall@10 | -0.0076311 | -0.0135787 | -0.0015900 |
| no_interaction_history | LightGCN | click_only | ndcg@10 | -0.0144964 | -0.0216895 | -0.0072997 |
| no_interaction_history | LightGCN | converted_then_original | recall@10 | +0.0007261 | -0.0007801 | +0.0023861 |
| no_interaction_history | LightGCN | converted_then_original | ndcg@10 | -0.0058860 | -0.0107151 | -0.0006674 |
| no_interaction_history | LightGCN | three_tier | recall@10 | -0.0075857 | -0.0135164 | -0.0015360 |
| no_interaction_history | LightGCN | three_tier | ndcg@10 | -0.0208886 | -0.0295709 | -0.0125993 |
| no_interaction_history | MultiVAE | sampled_baseline | recall@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | MultiVAE | sampled_baseline | ndcg@10 | +0.0000000 | +0.0000000 | +0.0000000 |
| no_interaction_history | MultiVAE | click_only | recall@10 | -0.0094826 | -0.0153788 | -0.0036703 |
| no_interaction_history | MultiVAE | click_only | ndcg@10 | -0.0159242 | -0.0231150 | -0.0087700 |
| no_interaction_history | MultiVAE | converted_then_original | recall@10 | +0.0000218 | -0.0010912 | +0.0009860 |
| no_interaction_history | MultiVAE | converted_then_original | ndcg@10 | -0.0066681 | -0.0115317 | -0.0017757 |
| no_interaction_history | MultiVAE | three_tier | recall@10 | -0.0092203 | -0.0150442 | -0.0034709 |
| no_interaction_history | MultiVAE | three_tier | ndcg@10 | -0.0200180 | -0.0279186 | -0.0119992 |

## Click Counts by Activity

Grouping uses each user's stored Activity level, including in conditions where persona was withheld.
Each case contributes one click count (0-20); percentages use cases within the Activity group.

| Condition | Model | Activity | Click count | Cases | Group cases | Percent |
|---|---|---:|---:|---:|---:|---:|
| full | LightGCN | 1 | 0 | 0 | 484 | 0.00% |
| full | LightGCN | 1 | 1 | 0 | 484 | 0.00% |
| full | LightGCN | 1 | 2 | 1 | 484 | 0.21% |
| full | LightGCN | 1 | 3 | 3 | 484 | 0.62% |
| full | LightGCN | 1 | 4 | 12 | 484 | 2.48% |
| full | LightGCN | 1 | 5 | 80 | 484 | 16.53% |
| full | LightGCN | 1 | 6 | 52 | 484 | 10.74% |
| full | LightGCN | 1 | 7 | 38 | 484 | 7.85% |
| full | LightGCN | 1 | 8 | 36 | 484 | 7.44% |
| full | LightGCN | 1 | 9 | 42 | 484 | 8.68% |
| full | LightGCN | 1 | 10 | 112 | 484 | 23.14% |
| full | LightGCN | 1 | 11 | 28 | 484 | 5.79% |
| full | LightGCN | 1 | 12 | 20 | 484 | 4.13% |
| full | LightGCN | 1 | 13 | 26 | 484 | 5.37% |
| full | LightGCN | 1 | 14 | 14 | 484 | 2.89% |
| full | LightGCN | 1 | 15 | 6 | 484 | 1.24% |
| full | LightGCN | 1 | 16 | 7 | 484 | 1.45% |
| full | LightGCN | 1 | 17 | 5 | 484 | 1.03% |
| full | LightGCN | 1 | 18 | 0 | 484 | 0.00% |
| full | LightGCN | 1 | 19 | 2 | 484 | 0.41% |
| full | LightGCN | 1 | 20 | 0 | 484 | 0.00% |
| full | LightGCN | 2 | 0 | 1 | 367 | 0.27% |
| full | LightGCN | 2 | 1 | 0 | 367 | 0.00% |
| full | LightGCN | 2 | 2 | 2 | 367 | 0.54% |
| full | LightGCN | 2 | 3 | 3 | 367 | 0.82% |
| full | LightGCN | 2 | 4 | 5 | 367 | 1.36% |
| full | LightGCN | 2 | 5 | 56 | 367 | 15.26% |
| full | LightGCN | 2 | 6 | 35 | 367 | 9.54% |
| full | LightGCN | 2 | 7 | 25 | 367 | 6.81% |
| full | LightGCN | 2 | 8 | 35 | 367 | 9.54% |
| full | LightGCN | 2 | 9 | 46 | 367 | 12.53% |
| full | LightGCN | 2 | 10 | 88 | 367 | 23.98% |
| full | LightGCN | 2 | 11 | 20 | 367 | 5.45% |
| full | LightGCN | 2 | 12 | 15 | 367 | 4.09% |
| full | LightGCN | 2 | 13 | 14 | 367 | 3.81% |
| full | LightGCN | 2 | 14 | 9 | 367 | 2.45% |
| full | LightGCN | 2 | 15 | 7 | 367 | 1.91% |
| full | LightGCN | 2 | 16 | 2 | 367 | 0.54% |
| full | LightGCN | 2 | 17 | 3 | 367 | 0.82% |
| full | LightGCN | 2 | 18 | 1 | 367 | 0.27% |
| full | LightGCN | 2 | 19 | 0 | 367 | 0.00% |
| full | LightGCN | 2 | 20 | 0 | 367 | 0.00% |
| full | LightGCN | 3 | 0 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 1 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 2 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 3 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 4 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 5 | 15 | 149 | 10.07% |
| full | LightGCN | 3 | 6 | 9 | 149 | 6.04% |
| full | LightGCN | 3 | 7 | 11 | 149 | 7.38% |
| full | LightGCN | 3 | 8 | 11 | 149 | 7.38% |
| full | LightGCN | 3 | 9 | 18 | 149 | 12.08% |
| full | LightGCN | 3 | 10 | 39 | 149 | 26.17% |
| full | LightGCN | 3 | 11 | 9 | 149 | 6.04% |
| full | LightGCN | 3 | 12 | 12 | 149 | 8.05% |
| full | LightGCN | 3 | 13 | 5 | 149 | 3.36% |
| full | LightGCN | 3 | 14 | 11 | 149 | 7.38% |
| full | LightGCN | 3 | 15 | 3 | 149 | 2.01% |
| full | LightGCN | 3 | 16 | 4 | 149 | 2.68% |
| full | LightGCN | 3 | 17 | 1 | 149 | 0.67% |
| full | LightGCN | 3 | 18 | 1 | 149 | 0.67% |
| full | LightGCN | 3 | 19 | 0 | 149 | 0.00% |
| full | LightGCN | 3 | 20 | 0 | 149 | 0.00% |
| full | MF | 1 | 0 | 1 | 484 | 0.21% |
| full | MF | 1 | 1 | 2 | 484 | 0.41% |
| full | MF | 1 | 2 | 0 | 484 | 0.00% |
| full | MF | 1 | 3 | 6 | 484 | 1.24% |
| full | MF | 1 | 4 | 7 | 484 | 1.45% |
| full | MF | 1 | 5 | 70 | 484 | 14.46% |
| full | MF | 1 | 6 | 33 | 484 | 6.82% |
| full | MF | 1 | 7 | 33 | 484 | 6.82% |
| full | MF | 1 | 8 | 46 | 484 | 9.50% |
| full | MF | 1 | 9 | 41 | 484 | 8.47% |
| full | MF | 1 | 10 | 119 | 484 | 24.59% |
| full | MF | 1 | 11 | 40 | 484 | 8.26% |
| full | MF | 1 | 12 | 27 | 484 | 5.58% |
| full | MF | 1 | 13 | 20 | 484 | 4.13% |
| full | MF | 1 | 14 | 13 | 484 | 2.69% |
| full | MF | 1 | 15 | 12 | 484 | 2.48% |
| full | MF | 1 | 16 | 5 | 484 | 1.03% |
| full | MF | 1 | 17 | 5 | 484 | 1.03% |
| full | MF | 1 | 18 | 2 | 484 | 0.41% |
| full | MF | 1 | 19 | 2 | 484 | 0.41% |
| full | MF | 1 | 20 | 0 | 484 | 0.00% |
| full | MF | 2 | 0 | 1 | 367 | 0.27% |
| full | MF | 2 | 1 | 0 | 367 | 0.00% |
| full | MF | 2 | 2 | 1 | 367 | 0.27% |
| full | MF | 2 | 3 | 1 | 367 | 0.27% |
| full | MF | 2 | 4 | 6 | 367 | 1.63% |
| full | MF | 2 | 5 | 58 | 367 | 15.80% |
| full | MF | 2 | 6 | 24 | 367 | 6.54% |
| full | MF | 2 | 7 | 28 | 367 | 7.63% |
| full | MF | 2 | 8 | 24 | 367 | 6.54% |
| full | MF | 2 | 9 | 36 | 367 | 9.81% |
| full | MF | 2 | 10 | 106 | 367 | 28.88% |
| full | MF | 2 | 11 | 16 | 367 | 4.36% |
| full | MF | 2 | 12 | 21 | 367 | 5.72% |
| full | MF | 2 | 13 | 11 | 367 | 3.00% |
| full | MF | 2 | 14 | 11 | 367 | 3.00% |
| full | MF | 2 | 15 | 10 | 367 | 2.72% |
| full | MF | 2 | 16 | 6 | 367 | 1.63% |
| full | MF | 2 | 17 | 6 | 367 | 1.63% |
| full | MF | 2 | 18 | 1 | 367 | 0.27% |
| full | MF | 2 | 19 | 0 | 367 | 0.00% |
| full | MF | 2 | 20 | 0 | 367 | 0.00% |
| full | MF | 3 | 0 | 0 | 149 | 0.00% |
| full | MF | 3 | 1 | 0 | 149 | 0.00% |
| full | MF | 3 | 2 | 0 | 149 | 0.00% |
| full | MF | 3 | 3 | 2 | 149 | 1.34% |
| full | MF | 3 | 4 | 3 | 149 | 2.01% |
| full | MF | 3 | 5 | 16 | 149 | 10.74% |
| full | MF | 3 | 6 | 6 | 149 | 4.03% |
| full | MF | 3 | 7 | 9 | 149 | 6.04% |
| full | MF | 3 | 8 | 16 | 149 | 10.74% |
| full | MF | 3 | 9 | 5 | 149 | 3.36% |
| full | MF | 3 | 10 | 43 | 149 | 28.86% |
| full | MF | 3 | 11 | 11 | 149 | 7.38% |
| full | MF | 3 | 12 | 12 | 149 | 8.05% |
| full | MF | 3 | 13 | 7 | 149 | 4.70% |
| full | MF | 3 | 14 | 5 | 149 | 3.36% |
| full | MF | 3 | 15 | 9 | 149 | 6.04% |
| full | MF | 3 | 16 | 4 | 149 | 2.68% |
| full | MF | 3 | 17 | 1 | 149 | 0.67% |
| full | MF | 3 | 18 | 0 | 149 | 0.00% |
| full | MF | 3 | 19 | 0 | 149 | 0.00% |
| full | MF | 3 | 20 | 0 | 149 | 0.00% |
| full | MultiVAE | 1 | 0 | 0 | 484 | 0.00% |
| full | MultiVAE | 1 | 1 | 2 | 484 | 0.41% |
| full | MultiVAE | 1 | 2 | 0 | 484 | 0.00% |
| full | MultiVAE | 1 | 3 | 5 | 484 | 1.03% |
| full | MultiVAE | 1 | 4 | 13 | 484 | 2.69% |
| full | MultiVAE | 1 | 5 | 62 | 484 | 12.81% |
| full | MultiVAE | 1 | 6 | 48 | 484 | 9.92% |
| full | MultiVAE | 1 | 7 | 33 | 484 | 6.82% |
| full | MultiVAE | 1 | 8 | 56 | 484 | 11.57% |
| full | MultiVAE | 1 | 9 | 47 | 484 | 9.71% |
| full | MultiVAE | 1 | 10 | 113 | 484 | 23.35% |
| full | MultiVAE | 1 | 11 | 25 | 484 | 5.17% |
| full | MultiVAE | 1 | 12 | 23 | 484 | 4.75% |
| full | MultiVAE | 1 | 13 | 23 | 484 | 4.75% |
| full | MultiVAE | 1 | 14 | 21 | 484 | 4.34% |
| full | MultiVAE | 1 | 15 | 7 | 484 | 1.45% |
| full | MultiVAE | 1 | 16 | 3 | 484 | 0.62% |
| full | MultiVAE | 1 | 17 | 1 | 484 | 0.21% |
| full | MultiVAE | 1 | 18 | 2 | 484 | 0.41% |
| full | MultiVAE | 1 | 19 | 0 | 484 | 0.00% |
| full | MultiVAE | 1 | 20 | 0 | 484 | 0.00% |
| full | MultiVAE | 2 | 0 | 0 | 367 | 0.00% |
| full | MultiVAE | 2 | 1 | 1 | 367 | 0.27% |
| full | MultiVAE | 2 | 2 | 1 | 367 | 0.27% |
| full | MultiVAE | 2 | 3 | 5 | 367 | 1.36% |
| full | MultiVAE | 2 | 4 | 7 | 367 | 1.91% |
| full | MultiVAE | 2 | 5 | 41 | 367 | 11.17% |
| full | MultiVAE | 2 | 6 | 26 | 367 | 7.08% |
| full | MultiVAE | 2 | 7 | 25 | 367 | 6.81% |
| full | MultiVAE | 2 | 8 | 30 | 367 | 8.17% |
| full | MultiVAE | 2 | 9 | 42 | 367 | 11.44% |
| full | MultiVAE | 2 | 10 | 89 | 367 | 24.25% |
| full | MultiVAE | 2 | 11 | 31 | 367 | 8.45% |
| full | MultiVAE | 2 | 12 | 20 | 367 | 5.45% |
| full | MultiVAE | 2 | 13 | 18 | 367 | 4.90% |
| full | MultiVAE | 2 | 14 | 11 | 367 | 3.00% |
| full | MultiVAE | 2 | 15 | 5 | 367 | 1.36% |
| full | MultiVAE | 2 | 16 | 5 | 367 | 1.36% |
| full | MultiVAE | 2 | 17 | 3 | 367 | 0.82% |
| full | MultiVAE | 2 | 18 | 5 | 367 | 1.36% |
| full | MultiVAE | 2 | 19 | 2 | 367 | 0.54% |
| full | MultiVAE | 2 | 20 | 0 | 367 | 0.00% |
| full | MultiVAE | 3 | 0 | 0 | 149 | 0.00% |
| full | MultiVAE | 3 | 1 | 1 | 149 | 0.67% |
| full | MultiVAE | 3 | 2 | 0 | 149 | 0.00% |
| full | MultiVAE | 3 | 3 | 2 | 149 | 1.34% |
| full | MultiVAE | 3 | 4 | 3 | 149 | 2.01% |
| full | MultiVAE | 3 | 5 | 14 | 149 | 9.40% |
| full | MultiVAE | 3 | 6 | 13 | 149 | 8.72% |
| full | MultiVAE | 3 | 7 | 11 | 149 | 7.38% |
| full | MultiVAE | 3 | 8 | 13 | 149 | 8.72% |
| full | MultiVAE | 3 | 9 | 20 | 149 | 13.42% |
| full | MultiVAE | 3 | 10 | 28 | 149 | 18.79% |
| full | MultiVAE | 3 | 11 | 11 | 149 | 7.38% |
| full | MultiVAE | 3 | 12 | 8 | 149 | 5.37% |
| full | MultiVAE | 3 | 13 | 7 | 149 | 4.70% |
| full | MultiVAE | 3 | 14 | 7 | 149 | 4.70% |
| full | MultiVAE | 3 | 15 | 2 | 149 | 1.34% |
| full | MultiVAE | 3 | 16 | 3 | 149 | 2.01% |
| full | MultiVAE | 3 | 17 | 4 | 149 | 2.68% |
| full | MultiVAE | 3 | 18 | 2 | 149 | 1.34% |
| full | MultiVAE | 3 | 19 | 0 | 149 | 0.00% |
| full | MultiVAE | 3 | 20 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 1 | 0 | 0 | 484 | 0.00% |
| no_demographics | LightGCN | 1 | 1 | 0 | 484 | 0.00% |
| no_demographics | LightGCN | 1 | 2 | 3 | 484 | 0.62% |
| no_demographics | LightGCN | 1 | 3 | 8 | 484 | 1.65% |
| no_demographics | LightGCN | 1 | 4 | 6 | 484 | 1.24% |
| no_demographics | LightGCN | 1 | 5 | 83 | 484 | 17.15% |
| no_demographics | LightGCN | 1 | 6 | 41 | 484 | 8.47% |
| no_demographics | LightGCN | 1 | 7 | 44 | 484 | 9.09% |
| no_demographics | LightGCN | 1 | 8 | 45 | 484 | 9.30% |
| no_demographics | LightGCN | 1 | 9 | 45 | 484 | 9.30% |
| no_demographics | LightGCN | 1 | 10 | 104 | 484 | 21.49% |
| no_demographics | LightGCN | 1 | 11 | 37 | 484 | 7.64% |
| no_demographics | LightGCN | 1 | 12 | 23 | 484 | 4.75% |
| no_demographics | LightGCN | 1 | 13 | 13 | 484 | 2.69% |
| no_demographics | LightGCN | 1 | 14 | 15 | 484 | 3.10% |
| no_demographics | LightGCN | 1 | 15 | 7 | 484 | 1.45% |
| no_demographics | LightGCN | 1 | 16 | 5 | 484 | 1.03% |
| no_demographics | LightGCN | 1 | 17 | 3 | 484 | 0.62% |
| no_demographics | LightGCN | 1 | 18 | 2 | 484 | 0.41% |
| no_demographics | LightGCN | 1 | 19 | 0 | 484 | 0.00% |
| no_demographics | LightGCN | 1 | 20 | 0 | 484 | 0.00% |
| no_demographics | LightGCN | 2 | 0 | 1 | 367 | 0.27% |
| no_demographics | LightGCN | 2 | 1 | 0 | 367 | 0.00% |
| no_demographics | LightGCN | 2 | 2 | 1 | 367 | 0.27% |
| no_demographics | LightGCN | 2 | 3 | 4 | 367 | 1.09% |
| no_demographics | LightGCN | 2 | 4 | 6 | 367 | 1.63% |
| no_demographics | LightGCN | 2 | 5 | 40 | 367 | 10.90% |
| no_demographics | LightGCN | 2 | 6 | 39 | 367 | 10.63% |
| no_demographics | LightGCN | 2 | 7 | 26 | 367 | 7.08% |
| no_demographics | LightGCN | 2 | 8 | 44 | 367 | 11.99% |
| no_demographics | LightGCN | 2 | 9 | 39 | 367 | 10.63% |
| no_demographics | LightGCN | 2 | 10 | 94 | 367 | 25.61% |
| no_demographics | LightGCN | 2 | 11 | 25 | 367 | 6.81% |
| no_demographics | LightGCN | 2 | 12 | 14 | 367 | 3.81% |
| no_demographics | LightGCN | 2 | 13 | 11 | 367 | 3.00% |
| no_demographics | LightGCN | 2 | 14 | 13 | 367 | 3.54% |
| no_demographics | LightGCN | 2 | 15 | 6 | 367 | 1.63% |
| no_demographics | LightGCN | 2 | 16 | 2 | 367 | 0.54% |
| no_demographics | LightGCN | 2 | 17 | 2 | 367 | 0.54% |
| no_demographics | LightGCN | 2 | 18 | 0 | 367 | 0.00% |
| no_demographics | LightGCN | 2 | 19 | 0 | 367 | 0.00% |
| no_demographics | LightGCN | 2 | 20 | 0 | 367 | 0.00% |
| no_demographics | LightGCN | 3 | 0 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 1 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 2 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 3 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 4 | 1 | 149 | 0.67% |
| no_demographics | LightGCN | 3 | 5 | 12 | 149 | 8.05% |
| no_demographics | LightGCN | 3 | 6 | 8 | 149 | 5.37% |
| no_demographics | LightGCN | 3 | 7 | 12 | 149 | 8.05% |
| no_demographics | LightGCN | 3 | 8 | 17 | 149 | 11.41% |
| no_demographics | LightGCN | 3 | 9 | 24 | 149 | 16.11% |
| no_demographics | LightGCN | 3 | 10 | 28 | 149 | 18.79% |
| no_demographics | LightGCN | 3 | 11 | 11 | 149 | 7.38% |
| no_demographics | LightGCN | 3 | 12 | 7 | 149 | 4.70% |
| no_demographics | LightGCN | 3 | 13 | 13 | 149 | 8.72% |
| no_demographics | LightGCN | 3 | 14 | 9 | 149 | 6.04% |
| no_demographics | LightGCN | 3 | 15 | 4 | 149 | 2.68% |
| no_demographics | LightGCN | 3 | 16 | 2 | 149 | 1.34% |
| no_demographics | LightGCN | 3 | 17 | 1 | 149 | 0.67% |
| no_demographics | LightGCN | 3 | 18 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 19 | 0 | 149 | 0.00% |
| no_demographics | LightGCN | 3 | 20 | 0 | 149 | 0.00% |
| no_demographics | MF | 1 | 0 | 1 | 484 | 0.21% |
| no_demographics | MF | 1 | 1 | 1 | 484 | 0.21% |
| no_demographics | MF | 1 | 2 | 1 | 484 | 0.21% |
| no_demographics | MF | 1 | 3 | 9 | 484 | 1.86% |
| no_demographics | MF | 1 | 4 | 11 | 484 | 2.27% |
| no_demographics | MF | 1 | 5 | 68 | 484 | 14.05% |
| no_demographics | MF | 1 | 6 | 29 | 484 | 5.99% |
| no_demographics | MF | 1 | 7 | 27 | 484 | 5.58% |
| no_demographics | MF | 1 | 8 | 52 | 484 | 10.74% |
| no_demographics | MF | 1 | 9 | 43 | 484 | 8.88% |
| no_demographics | MF | 1 | 10 | 119 | 484 | 24.59% |
| no_demographics | MF | 1 | 11 | 34 | 484 | 7.02% |
| no_demographics | MF | 1 | 12 | 33 | 484 | 6.82% |
| no_demographics | MF | 1 | 13 | 15 | 484 | 3.10% |
| no_demographics | MF | 1 | 14 | 17 | 484 | 3.51% |
| no_demographics | MF | 1 | 15 | 17 | 484 | 3.51% |
| no_demographics | MF | 1 | 16 | 2 | 484 | 0.41% |
| no_demographics | MF | 1 | 17 | 2 | 484 | 0.41% |
| no_demographics | MF | 1 | 18 | 3 | 484 | 0.62% |
| no_demographics | MF | 1 | 19 | 0 | 484 | 0.00% |
| no_demographics | MF | 1 | 20 | 0 | 484 | 0.00% |
| no_demographics | MF | 2 | 0 | 1 | 367 | 0.27% |
| no_demographics | MF | 2 | 1 | 0 | 367 | 0.00% |
| no_demographics | MF | 2 | 2 | 0 | 367 | 0.00% |
| no_demographics | MF | 2 | 3 | 2 | 367 | 0.54% |
| no_demographics | MF | 2 | 4 | 7 | 367 | 1.91% |
| no_demographics | MF | 2 | 5 | 48 | 367 | 13.08% |
| no_demographics | MF | 2 | 6 | 29 | 367 | 7.90% |
| no_demographics | MF | 2 | 7 | 31 | 367 | 8.45% |
| no_demographics | MF | 2 | 8 | 41 | 367 | 11.17% |
| no_demographics | MF | 2 | 9 | 37 | 367 | 10.08% |
| no_demographics | MF | 2 | 10 | 84 | 367 | 22.89% |
| no_demographics | MF | 2 | 11 | 16 | 367 | 4.36% |
| no_demographics | MF | 2 | 12 | 26 | 367 | 7.08% |
| no_demographics | MF | 2 | 13 | 11 | 367 | 3.00% |
| no_demographics | MF | 2 | 14 | 12 | 367 | 3.27% |
| no_demographics | MF | 2 | 15 | 9 | 367 | 2.45% |
| no_demographics | MF | 2 | 16 | 8 | 367 | 2.18% |
| no_demographics | MF | 2 | 17 | 1 | 367 | 0.27% |
| no_demographics | MF | 2 | 18 | 3 | 367 | 0.82% |
| no_demographics | MF | 2 | 19 | 1 | 367 | 0.27% |
| no_demographics | MF | 2 | 20 | 0 | 367 | 0.00% |
| no_demographics | MF | 3 | 0 | 0 | 149 | 0.00% |
| no_demographics | MF | 3 | 1 | 0 | 149 | 0.00% |
| no_demographics | MF | 3 | 2 | 1 | 149 | 0.67% |
| no_demographics | MF | 3 | 3 | 0 | 149 | 0.00% |
| no_demographics | MF | 3 | 4 | 4 | 149 | 2.68% |
| no_demographics | MF | 3 | 5 | 20 | 149 | 13.42% |
| no_demographics | MF | 3 | 6 | 14 | 149 | 9.40% |
| no_demographics | MF | 3 | 7 | 9 | 149 | 6.04% |
| no_demographics | MF | 3 | 8 | 13 | 149 | 8.72% |
| no_demographics | MF | 3 | 9 | 11 | 149 | 7.38% |
| no_demographics | MF | 3 | 10 | 31 | 149 | 20.81% |
| no_demographics | MF | 3 | 11 | 9 | 149 | 6.04% |
| no_demographics | MF | 3 | 12 | 9 | 149 | 6.04% |
| no_demographics | MF | 3 | 13 | 8 | 149 | 5.37% |
| no_demographics | MF | 3 | 14 | 7 | 149 | 4.70% |
| no_demographics | MF | 3 | 15 | 10 | 149 | 6.71% |
| no_demographics | MF | 3 | 16 | 2 | 149 | 1.34% |
| no_demographics | MF | 3 | 17 | 1 | 149 | 0.67% |
| no_demographics | MF | 3 | 18 | 0 | 149 | 0.00% |
| no_demographics | MF | 3 | 19 | 0 | 149 | 0.00% |
| no_demographics | MF | 3 | 20 | 0 | 149 | 0.00% |
| no_demographics | MultiVAE | 1 | 0 | 0 | 484 | 0.00% |
| no_demographics | MultiVAE | 1 | 1 | 1 | 484 | 0.21% |
| no_demographics | MultiVAE | 1 | 2 | 0 | 484 | 0.00% |
| no_demographics | MultiVAE | 1 | 3 | 4 | 484 | 0.83% |
| no_demographics | MultiVAE | 1 | 4 | 13 | 484 | 2.69% |
| no_demographics | MultiVAE | 1 | 5 | 71 | 484 | 14.67% |
| no_demographics | MultiVAE | 1 | 6 | 51 | 484 | 10.54% |
| no_demographics | MultiVAE | 1 | 7 | 39 | 484 | 8.06% |
| no_demographics | MultiVAE | 1 | 8 | 37 | 484 | 7.64% |
| no_demographics | MultiVAE | 1 | 9 | 50 | 484 | 10.33% |
| no_demographics | MultiVAE | 1 | 10 | 118 | 484 | 24.38% |
| no_demographics | MultiVAE | 1 | 11 | 23 | 484 | 4.75% |
| no_demographics | MultiVAE | 1 | 12 | 19 | 484 | 3.93% |
| no_demographics | MultiVAE | 1 | 13 | 26 | 484 | 5.37% |
| no_demographics | MultiVAE | 1 | 14 | 16 | 484 | 3.31% |
| no_demographics | MultiVAE | 1 | 15 | 5 | 484 | 1.03% |
| no_demographics | MultiVAE | 1 | 16 | 3 | 484 | 0.62% |
| no_demographics | MultiVAE | 1 | 17 | 5 | 484 | 1.03% |
| no_demographics | MultiVAE | 1 | 18 | 3 | 484 | 0.62% |
| no_demographics | MultiVAE | 1 | 19 | 0 | 484 | 0.00% |
| no_demographics | MultiVAE | 1 | 20 | 0 | 484 | 0.00% |
| no_demographics | MultiVAE | 2 | 0 | 0 | 367 | 0.00% |
| no_demographics | MultiVAE | 2 | 1 | 2 | 367 | 0.54% |
| no_demographics | MultiVAE | 2 | 2 | 1 | 367 | 0.27% |
| no_demographics | MultiVAE | 2 | 3 | 0 | 367 | 0.00% |
| no_demographics | MultiVAE | 2 | 4 | 8 | 367 | 2.18% |
| no_demographics | MultiVAE | 2 | 5 | 36 | 367 | 9.81% |
| no_demographics | MultiVAE | 2 | 6 | 29 | 367 | 7.90% |
| no_demographics | MultiVAE | 2 | 7 | 24 | 367 | 6.54% |
| no_demographics | MultiVAE | 2 | 8 | 44 | 367 | 11.99% |
| no_demographics | MultiVAE | 2 | 9 | 34 | 367 | 9.26% |
| no_demographics | MultiVAE | 2 | 10 | 95 | 367 | 25.89% |
| no_demographics | MultiVAE | 2 | 11 | 30 | 367 | 8.17% |
| no_demographics | MultiVAE | 2 | 12 | 16 | 367 | 4.36% |
| no_demographics | MultiVAE | 2 | 13 | 16 | 367 | 4.36% |
| no_demographics | MultiVAE | 2 | 14 | 14 | 367 | 3.81% |
| no_demographics | MultiVAE | 2 | 15 | 7 | 367 | 1.91% |
| no_demographics | MultiVAE | 2 | 16 | 3 | 367 | 0.82% |
| no_demographics | MultiVAE | 2 | 17 | 6 | 367 | 1.63% |
| no_demographics | MultiVAE | 2 | 18 | 2 | 367 | 0.54% |
| no_demographics | MultiVAE | 2 | 19 | 0 | 367 | 0.00% |
| no_demographics | MultiVAE | 2 | 20 | 0 | 367 | 0.00% |
| no_demographics | MultiVAE | 3 | 0 | 0 | 149 | 0.00% |
| no_demographics | MultiVAE | 3 | 1 | 1 | 149 | 0.67% |
| no_demographics | MultiVAE | 3 | 2 | 0 | 149 | 0.00% |
| no_demographics | MultiVAE | 3 | 3 | 2 | 149 | 1.34% |
| no_demographics | MultiVAE | 3 | 4 | 4 | 149 | 2.68% |
| no_demographics | MultiVAE | 3 | 5 | 13 | 149 | 8.72% |
| no_demographics | MultiVAE | 3 | 6 | 15 | 149 | 10.07% |
| no_demographics | MultiVAE | 3 | 7 | 15 | 149 | 10.07% |
| no_demographics | MultiVAE | 3 | 8 | 16 | 149 | 10.74% |
| no_demographics | MultiVAE | 3 | 9 | 8 | 149 | 5.37% |
| no_demographics | MultiVAE | 3 | 10 | 29 | 149 | 19.46% |
| no_demographics | MultiVAE | 3 | 11 | 14 | 149 | 9.40% |
| no_demographics | MultiVAE | 3 | 12 | 9 | 149 | 6.04% |
| no_demographics | MultiVAE | 3 | 13 | 8 | 149 | 5.37% |
| no_demographics | MultiVAE | 3 | 14 | 8 | 149 | 5.37% |
| no_demographics | MultiVAE | 3 | 15 | 2 | 149 | 1.34% |
| no_demographics | MultiVAE | 3 | 16 | 0 | 149 | 0.00% |
| no_demographics | MultiVAE | 3 | 17 | 4 | 149 | 2.68% |
| no_demographics | MultiVAE | 3 | 18 | 0 | 149 | 0.00% |
| no_demographics | MultiVAE | 3 | 19 | 1 | 149 | 0.67% |
| no_demographics | MultiVAE | 3 | 20 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 1 | 0 | 0 | 484 | 0.00% |
| no_interaction_history | LightGCN | 1 | 1 | 1 | 484 | 0.21% |
| no_interaction_history | LightGCN | 1 | 2 | 4 | 484 | 0.83% |
| no_interaction_history | LightGCN | 1 | 3 | 6 | 484 | 1.24% |
| no_interaction_history | LightGCN | 1 | 4 | 22 | 484 | 4.55% |
| no_interaction_history | LightGCN | 1 | 5 | 76 | 484 | 15.70% |
| no_interaction_history | LightGCN | 1 | 6 | 46 | 484 | 9.50% |
| no_interaction_history | LightGCN | 1 | 7 | 44 | 484 | 9.09% |
| no_interaction_history | LightGCN | 1 | 8 | 52 | 484 | 10.74% |
| no_interaction_history | LightGCN | 1 | 9 | 44 | 484 | 9.09% |
| no_interaction_history | LightGCN | 1 | 10 | 77 | 484 | 15.91% |
| no_interaction_history | LightGCN | 1 | 11 | 32 | 484 | 6.61% |
| no_interaction_history | LightGCN | 1 | 12 | 26 | 484 | 5.37% |
| no_interaction_history | LightGCN | 1 | 13 | 15 | 484 | 3.10% |
| no_interaction_history | LightGCN | 1 | 14 | 15 | 484 | 3.10% |
| no_interaction_history | LightGCN | 1 | 15 | 9 | 484 | 1.86% |
| no_interaction_history | LightGCN | 1 | 16 | 9 | 484 | 1.86% |
| no_interaction_history | LightGCN | 1 | 17 | 3 | 484 | 0.62% |
| no_interaction_history | LightGCN | 1 | 18 | 2 | 484 | 0.41% |
| no_interaction_history | LightGCN | 1 | 19 | 1 | 484 | 0.21% |
| no_interaction_history | LightGCN | 1 | 20 | 0 | 484 | 0.00% |
| no_interaction_history | LightGCN | 2 | 0 | 2 | 367 | 0.54% |
| no_interaction_history | LightGCN | 2 | 1 | 1 | 367 | 0.27% |
| no_interaction_history | LightGCN | 2 | 2 | 1 | 367 | 0.27% |
| no_interaction_history | LightGCN | 2 | 3 | 6 | 367 | 1.63% |
| no_interaction_history | LightGCN | 2 | 4 | 11 | 367 | 3.00% |
| no_interaction_history | LightGCN | 2 | 5 | 43 | 367 | 11.72% |
| no_interaction_history | LightGCN | 2 | 6 | 35 | 367 | 9.54% |
| no_interaction_history | LightGCN | 2 | 7 | 37 | 367 | 10.08% |
| no_interaction_history | LightGCN | 2 | 8 | 36 | 367 | 9.81% |
| no_interaction_history | LightGCN | 2 | 9 | 37 | 367 | 10.08% |
| no_interaction_history | LightGCN | 2 | 10 | 69 | 367 | 18.80% |
| no_interaction_history | LightGCN | 2 | 11 | 29 | 367 | 7.90% |
| no_interaction_history | LightGCN | 2 | 12 | 24 | 367 | 6.54% |
| no_interaction_history | LightGCN | 2 | 13 | 15 | 367 | 4.09% |
| no_interaction_history | LightGCN | 2 | 14 | 9 | 367 | 2.45% |
| no_interaction_history | LightGCN | 2 | 15 | 6 | 367 | 1.63% |
| no_interaction_history | LightGCN | 2 | 16 | 3 | 367 | 0.82% |
| no_interaction_history | LightGCN | 2 | 17 | 2 | 367 | 0.54% |
| no_interaction_history | LightGCN | 2 | 18 | 1 | 367 | 0.27% |
| no_interaction_history | LightGCN | 2 | 19 | 0 | 367 | 0.00% |
| no_interaction_history | LightGCN | 2 | 20 | 0 | 367 | 0.00% |
| no_interaction_history | LightGCN | 3 | 0 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 1 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 2 | 1 | 149 | 0.67% |
| no_interaction_history | LightGCN | 3 | 3 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 4 | 4 | 149 | 2.68% |
| no_interaction_history | LightGCN | 3 | 5 | 13 | 149 | 8.72% |
| no_interaction_history | LightGCN | 3 | 6 | 15 | 149 | 10.07% |
| no_interaction_history | LightGCN | 3 | 7 | 11 | 149 | 7.38% |
| no_interaction_history | LightGCN | 3 | 8 | 25 | 149 | 16.78% |
| no_interaction_history | LightGCN | 3 | 9 | 24 | 149 | 16.11% |
| no_interaction_history | LightGCN | 3 | 10 | 24 | 149 | 16.11% |
| no_interaction_history | LightGCN | 3 | 11 | 12 | 149 | 8.05% |
| no_interaction_history | LightGCN | 3 | 12 | 8 | 149 | 5.37% |
| no_interaction_history | LightGCN | 3 | 13 | 7 | 149 | 4.70% |
| no_interaction_history | LightGCN | 3 | 14 | 3 | 149 | 2.01% |
| no_interaction_history | LightGCN | 3 | 15 | 2 | 149 | 1.34% |
| no_interaction_history | LightGCN | 3 | 16 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 17 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 18 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 19 | 0 | 149 | 0.00% |
| no_interaction_history | LightGCN | 3 | 20 | 0 | 149 | 0.00% |
| no_interaction_history | MF | 1 | 0 | 2 | 484 | 0.41% |
| no_interaction_history | MF | 1 | 1 | 1 | 484 | 0.21% |
| no_interaction_history | MF | 1 | 2 | 3 | 484 | 0.62% |
| no_interaction_history | MF | 1 | 3 | 14 | 484 | 2.89% |
| no_interaction_history | MF | 1 | 4 | 13 | 484 | 2.69% |
| no_interaction_history | MF | 1 | 5 | 66 | 484 | 13.64% |
| no_interaction_history | MF | 1 | 6 | 41 | 484 | 8.47% |
| no_interaction_history | MF | 1 | 7 | 41 | 484 | 8.47% |
| no_interaction_history | MF | 1 | 8 | 53 | 484 | 10.95% |
| no_interaction_history | MF | 1 | 9 | 47 | 484 | 9.71% |
| no_interaction_history | MF | 1 | 10 | 88 | 484 | 18.18% |
| no_interaction_history | MF | 1 | 11 | 37 | 484 | 7.64% |
| no_interaction_history | MF | 1 | 12 | 27 | 484 | 5.58% |
| no_interaction_history | MF | 1 | 13 | 19 | 484 | 3.93% |
| no_interaction_history | MF | 1 | 14 | 12 | 484 | 2.48% |
| no_interaction_history | MF | 1 | 15 | 8 | 484 | 1.65% |
| no_interaction_history | MF | 1 | 16 | 5 | 484 | 1.03% |
| no_interaction_history | MF | 1 | 17 | 6 | 484 | 1.24% |
| no_interaction_history | MF | 1 | 18 | 1 | 484 | 0.21% |
| no_interaction_history | MF | 1 | 19 | 0 | 484 | 0.00% |
| no_interaction_history | MF | 1 | 20 | 0 | 484 | 0.00% |
| no_interaction_history | MF | 2 | 0 | 2 | 367 | 0.54% |
| no_interaction_history | MF | 2 | 1 | 0 | 367 | 0.00% |
| no_interaction_history | MF | 2 | 2 | 3 | 367 | 0.82% |
| no_interaction_history | MF | 2 | 3 | 3 | 367 | 0.82% |
| no_interaction_history | MF | 2 | 4 | 13 | 367 | 3.54% |
| no_interaction_history | MF | 2 | 5 | 39 | 367 | 10.63% |
| no_interaction_history | MF | 2 | 6 | 25 | 367 | 6.81% |
| no_interaction_history | MF | 2 | 7 | 35 | 367 | 9.54% |
| no_interaction_history | MF | 2 | 8 | 44 | 367 | 11.99% |
| no_interaction_history | MF | 2 | 9 | 36 | 367 | 9.81% |
| no_interaction_history | MF | 2 | 10 | 64 | 367 | 17.44% |
| no_interaction_history | MF | 2 | 11 | 31 | 367 | 8.45% |
| no_interaction_history | MF | 2 | 12 | 27 | 367 | 7.36% |
| no_interaction_history | MF | 2 | 13 | 16 | 367 | 4.36% |
| no_interaction_history | MF | 2 | 14 | 12 | 367 | 3.27% |
| no_interaction_history | MF | 2 | 15 | 6 | 367 | 1.63% |
| no_interaction_history | MF | 2 | 16 | 7 | 367 | 1.91% |
| no_interaction_history | MF | 2 | 17 | 3 | 367 | 0.82% |
| no_interaction_history | MF | 2 | 18 | 1 | 367 | 0.27% |
| no_interaction_history | MF | 2 | 19 | 0 | 367 | 0.00% |
| no_interaction_history | MF | 2 | 20 | 0 | 367 | 0.00% |
| no_interaction_history | MF | 3 | 0 | 0 | 149 | 0.00% |
| no_interaction_history | MF | 3 | 1 | 0 | 149 | 0.00% |
| no_interaction_history | MF | 3 | 2 | 2 | 149 | 1.34% |
| no_interaction_history | MF | 3 | 3 | 4 | 149 | 2.68% |
| no_interaction_history | MF | 3 | 4 | 3 | 149 | 2.01% |
| no_interaction_history | MF | 3 | 5 | 25 | 149 | 16.78% |
| no_interaction_history | MF | 3 | 6 | 13 | 149 | 8.72% |
| no_interaction_history | MF | 3 | 7 | 10 | 149 | 6.71% |
| no_interaction_history | MF | 3 | 8 | 12 | 149 | 8.05% |
| no_interaction_history | MF | 3 | 9 | 16 | 149 | 10.74% |
| no_interaction_history | MF | 3 | 10 | 28 | 149 | 18.79% |
| no_interaction_history | MF | 3 | 11 | 10 | 149 | 6.71% |
| no_interaction_history | MF | 3 | 12 | 6 | 149 | 4.03% |
| no_interaction_history | MF | 3 | 13 | 11 | 149 | 7.38% |
| no_interaction_history | MF | 3 | 14 | 3 | 149 | 2.01% |
| no_interaction_history | MF | 3 | 15 | 2 | 149 | 1.34% |
| no_interaction_history | MF | 3 | 16 | 3 | 149 | 2.01% |
| no_interaction_history | MF | 3 | 17 | 0 | 149 | 0.00% |
| no_interaction_history | MF | 3 | 18 | 1 | 149 | 0.67% |
| no_interaction_history | MF | 3 | 19 | 0 | 149 | 0.00% |
| no_interaction_history | MF | 3 | 20 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 1 | 0 | 0 | 484 | 0.00% |
| no_interaction_history | MultiVAE | 1 | 1 | 2 | 484 | 0.41% |
| no_interaction_history | MultiVAE | 1 | 2 | 1 | 484 | 0.21% |
| no_interaction_history | MultiVAE | 1 | 3 | 8 | 484 | 1.65% |
| no_interaction_history | MultiVAE | 1 | 4 | 17 | 484 | 3.51% |
| no_interaction_history | MultiVAE | 1 | 5 | 70 | 484 | 14.46% |
| no_interaction_history | MultiVAE | 1 | 6 | 42 | 484 | 8.68% |
| no_interaction_history | MultiVAE | 1 | 7 | 44 | 484 | 9.09% |
| no_interaction_history | MultiVAE | 1 | 8 | 46 | 484 | 9.50% |
| no_interaction_history | MultiVAE | 1 | 9 | 49 | 484 | 10.12% |
| no_interaction_history | MultiVAE | 1 | 10 | 79 | 484 | 16.32% |
| no_interaction_history | MultiVAE | 1 | 11 | 39 | 484 | 8.06% |
| no_interaction_history | MultiVAE | 1 | 12 | 25 | 484 | 5.17% |
| no_interaction_history | MultiVAE | 1 | 13 | 19 | 484 | 3.93% |
| no_interaction_history | MultiVAE | 1 | 14 | 19 | 484 | 3.93% |
| no_interaction_history | MultiVAE | 1 | 15 | 12 | 484 | 2.48% |
| no_interaction_history | MultiVAE | 1 | 16 | 7 | 484 | 1.45% |
| no_interaction_history | MultiVAE | 1 | 17 | 3 | 484 | 0.62% |
| no_interaction_history | MultiVAE | 1 | 18 | 2 | 484 | 0.41% |
| no_interaction_history | MultiVAE | 1 | 19 | 0 | 484 | 0.00% |
| no_interaction_history | MultiVAE | 1 | 20 | 0 | 484 | 0.00% |
| no_interaction_history | MultiVAE | 2 | 0 | 0 | 367 | 0.00% |
| no_interaction_history | MultiVAE | 2 | 1 | 0 | 367 | 0.00% |
| no_interaction_history | MultiVAE | 2 | 2 | 5 | 367 | 1.36% |
| no_interaction_history | MultiVAE | 2 | 3 | 12 | 367 | 3.27% |
| no_interaction_history | MultiVAE | 2 | 4 | 12 | 367 | 3.27% |
| no_interaction_history | MultiVAE | 2 | 5 | 46 | 367 | 12.53% |
| no_interaction_history | MultiVAE | 2 | 6 | 21 | 367 | 5.72% |
| no_interaction_history | MultiVAE | 2 | 7 | 21 | 367 | 5.72% |
| no_interaction_history | MultiVAE | 2 | 8 | 44 | 367 | 11.99% |
| no_interaction_history | MultiVAE | 2 | 9 | 43 | 367 | 11.72% |
| no_interaction_history | MultiVAE | 2 | 10 | 62 | 367 | 16.89% |
| no_interaction_history | MultiVAE | 2 | 11 | 31 | 367 | 8.45% |
| no_interaction_history | MultiVAE | 2 | 12 | 25 | 367 | 6.81% |
| no_interaction_history | MultiVAE | 2 | 13 | 21 | 367 | 5.72% |
| no_interaction_history | MultiVAE | 2 | 14 | 9 | 367 | 2.45% |
| no_interaction_history | MultiVAE | 2 | 15 | 7 | 367 | 1.91% |
| no_interaction_history | MultiVAE | 2 | 16 | 2 | 367 | 0.54% |
| no_interaction_history | MultiVAE | 2 | 17 | 4 | 367 | 1.09% |
| no_interaction_history | MultiVAE | 2 | 18 | 2 | 367 | 0.54% |
| no_interaction_history | MultiVAE | 2 | 19 | 0 | 367 | 0.00% |
| no_interaction_history | MultiVAE | 2 | 20 | 0 | 367 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 0 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 1 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 2 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 3 | 3 | 149 | 2.01% |
| no_interaction_history | MultiVAE | 3 | 4 | 5 | 149 | 3.36% |
| no_interaction_history | MultiVAE | 3 | 5 | 19 | 149 | 12.75% |
| no_interaction_history | MultiVAE | 3 | 6 | 15 | 149 | 10.07% |
| no_interaction_history | MultiVAE | 3 | 7 | 14 | 149 | 9.40% |
| no_interaction_history | MultiVAE | 3 | 8 | 17 | 149 | 11.41% |
| no_interaction_history | MultiVAE | 3 | 9 | 13 | 149 | 8.72% |
| no_interaction_history | MultiVAE | 3 | 10 | 24 | 149 | 16.11% |
| no_interaction_history | MultiVAE | 3 | 11 | 14 | 149 | 9.40% |
| no_interaction_history | MultiVAE | 3 | 12 | 10 | 149 | 6.71% |
| no_interaction_history | MultiVAE | 3 | 13 | 6 | 149 | 4.03% |
| no_interaction_history | MultiVAE | 3 | 14 | 2 | 149 | 1.34% |
| no_interaction_history | MultiVAE | 3 | 15 | 4 | 149 | 2.68% |
| no_interaction_history | MultiVAE | 3 | 16 | 2 | 149 | 1.34% |
| no_interaction_history | MultiVAE | 3 | 17 | 1 | 149 | 0.67% |
| no_interaction_history | MultiVAE | 3 | 18 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 19 | 0 | 149 | 0.00% |
| no_interaction_history | MultiVAE | 3 | 20 | 0 | 149 | 0.00% |
| no_persona | LightGCN | 1 | 0 | 2 | 484 | 0.41% |
| no_persona | LightGCN | 1 | 1 | 0 | 484 | 0.00% |
| no_persona | LightGCN | 1 | 2 | 6 | 484 | 1.24% |
| no_persona | LightGCN | 1 | 3 | 13 | 484 | 2.69% |
| no_persona | LightGCN | 1 | 4 | 21 | 484 | 4.34% |
| no_persona | LightGCN | 1 | 5 | 56 | 484 | 11.57% |
| no_persona | LightGCN | 1 | 6 | 37 | 484 | 7.64% |
| no_persona | LightGCN | 1 | 7 | 47 | 484 | 9.71% |
| no_persona | LightGCN | 1 | 8 | 44 | 484 | 9.09% |
| no_persona | LightGCN | 1 | 9 | 44 | 484 | 9.09% |
| no_persona | LightGCN | 1 | 10 | 118 | 484 | 24.38% |
| no_persona | LightGCN | 1 | 11 | 21 | 484 | 4.34% |
| no_persona | LightGCN | 1 | 12 | 19 | 484 | 3.93% |
| no_persona | LightGCN | 1 | 13 | 18 | 484 | 3.72% |
| no_persona | LightGCN | 1 | 14 | 11 | 484 | 2.27% |
| no_persona | LightGCN | 1 | 15 | 7 | 484 | 1.45% |
| no_persona | LightGCN | 1 | 16 | 4 | 484 | 0.83% |
| no_persona | LightGCN | 1 | 17 | 10 | 484 | 2.07% |
| no_persona | LightGCN | 1 | 18 | 4 | 484 | 0.83% |
| no_persona | LightGCN | 1 | 19 | 2 | 484 | 0.41% |
| no_persona | LightGCN | 1 | 20 | 0 | 484 | 0.00% |
| no_persona | LightGCN | 2 | 0 | 0 | 367 | 0.00% |
| no_persona | LightGCN | 2 | 1 | 0 | 367 | 0.00% |
| no_persona | LightGCN | 2 | 2 | 4 | 367 | 1.09% |
| no_persona | LightGCN | 2 | 3 | 7 | 367 | 1.91% |
| no_persona | LightGCN | 2 | 4 | 17 | 367 | 4.63% |
| no_persona | LightGCN | 2 | 5 | 36 | 367 | 9.81% |
| no_persona | LightGCN | 2 | 6 | 42 | 367 | 11.44% |
| no_persona | LightGCN | 2 | 7 | 37 | 367 | 10.08% |
| no_persona | LightGCN | 2 | 8 | 35 | 367 | 9.54% |
| no_persona | LightGCN | 2 | 9 | 41 | 367 | 11.17% |
| no_persona | LightGCN | 2 | 10 | 72 | 367 | 19.62% |
| no_persona | LightGCN | 2 | 11 | 19 | 367 | 5.18% |
| no_persona | LightGCN | 2 | 12 | 15 | 367 | 4.09% |
| no_persona | LightGCN | 2 | 13 | 13 | 367 | 3.54% |
| no_persona | LightGCN | 2 | 14 | 13 | 367 | 3.54% |
| no_persona | LightGCN | 2 | 15 | 6 | 367 | 1.63% |
| no_persona | LightGCN | 2 | 16 | 6 | 367 | 1.63% |
| no_persona | LightGCN | 2 | 17 | 2 | 367 | 0.54% |
| no_persona | LightGCN | 2 | 18 | 2 | 367 | 0.54% |
| no_persona | LightGCN | 2 | 19 | 0 | 367 | 0.00% |
| no_persona | LightGCN | 2 | 20 | 0 | 367 | 0.00% |
| no_persona | LightGCN | 3 | 0 | 0 | 149 | 0.00% |
| no_persona | LightGCN | 3 | 1 | 0 | 149 | 0.00% |
| no_persona | LightGCN | 3 | 2 | 1 | 149 | 0.67% |
| no_persona | LightGCN | 3 | 3 | 1 | 149 | 0.67% |
| no_persona | LightGCN | 3 | 4 | 8 | 149 | 5.37% |
| no_persona | LightGCN | 3 | 5 | 16 | 149 | 10.74% |
| no_persona | LightGCN | 3 | 6 | 10 | 149 | 6.71% |
| no_persona | LightGCN | 3 | 7 | 21 | 149 | 14.09% |
| no_persona | LightGCN | 3 | 8 | 19 | 149 | 12.75% |
| no_persona | LightGCN | 3 | 9 | 13 | 149 | 8.72% |
| no_persona | LightGCN | 3 | 10 | 27 | 149 | 18.12% |
| no_persona | LightGCN | 3 | 11 | 9 | 149 | 6.04% |
| no_persona | LightGCN | 3 | 12 | 4 | 149 | 2.68% |
| no_persona | LightGCN | 3 | 13 | 7 | 149 | 4.70% |
| no_persona | LightGCN | 3 | 14 | 7 | 149 | 4.70% |
| no_persona | LightGCN | 3 | 15 | 2 | 149 | 1.34% |
| no_persona | LightGCN | 3 | 16 | 2 | 149 | 1.34% |
| no_persona | LightGCN | 3 | 17 | 2 | 149 | 1.34% |
| no_persona | LightGCN | 3 | 18 | 0 | 149 | 0.00% |
| no_persona | LightGCN | 3 | 19 | 0 | 149 | 0.00% |
| no_persona | LightGCN | 3 | 20 | 0 | 149 | 0.00% |
| no_persona | MF | 1 | 0 | 4 | 484 | 0.83% |
| no_persona | MF | 1 | 1 | 3 | 484 | 0.62% |
| no_persona | MF | 1 | 2 | 6 | 484 | 1.24% |
| no_persona | MF | 1 | 3 | 7 | 484 | 1.45% |
| no_persona | MF | 1 | 4 | 14 | 484 | 2.89% |
| no_persona | MF | 1 | 5 | 52 | 484 | 10.74% |
| no_persona | MF | 1 | 6 | 26 | 484 | 5.37% |
| no_persona | MF | 1 | 7 | 37 | 484 | 7.64% |
| no_persona | MF | 1 | 8 | 56 | 484 | 11.57% |
| no_persona | MF | 1 | 9 | 45 | 484 | 9.30% |
| no_persona | MF | 1 | 10 | 124 | 484 | 25.62% |
| no_persona | MF | 1 | 11 | 17 | 484 | 3.51% |
| no_persona | MF | 1 | 12 | 27 | 484 | 5.58% |
| no_persona | MF | 1 | 13 | 21 | 484 | 4.34% |
| no_persona | MF | 1 | 14 | 12 | 484 | 2.48% |
| no_persona | MF | 1 | 15 | 12 | 484 | 2.48% |
| no_persona | MF | 1 | 16 | 7 | 484 | 1.45% |
| no_persona | MF | 1 | 17 | 7 | 484 | 1.45% |
| no_persona | MF | 1 | 18 | 3 | 484 | 0.62% |
| no_persona | MF | 1 | 19 | 4 | 484 | 0.83% |
| no_persona | MF | 1 | 20 | 0 | 484 | 0.00% |
| no_persona | MF | 2 | 0 | 1 | 367 | 0.27% |
| no_persona | MF | 2 | 1 | 1 | 367 | 0.27% |
| no_persona | MF | 2 | 2 | 2 | 367 | 0.54% |
| no_persona | MF | 2 | 3 | 4 | 367 | 1.09% |
| no_persona | MF | 2 | 4 | 13 | 367 | 3.54% |
| no_persona | MF | 2 | 5 | 41 | 367 | 11.17% |
| no_persona | MF | 2 | 6 | 31 | 367 | 8.45% |
| no_persona | MF | 2 | 7 | 26 | 367 | 7.08% |
| no_persona | MF | 2 | 8 | 34 | 367 | 9.26% |
| no_persona | MF | 2 | 9 | 30 | 367 | 8.17% |
| no_persona | MF | 2 | 10 | 95 | 367 | 25.89% |
| no_persona | MF | 2 | 11 | 24 | 367 | 6.54% |
| no_persona | MF | 2 | 12 | 27 | 367 | 7.36% |
| no_persona | MF | 2 | 13 | 11 | 367 | 3.00% |
| no_persona | MF | 2 | 14 | 10 | 367 | 2.72% |
| no_persona | MF | 2 | 15 | 7 | 367 | 1.91% |
| no_persona | MF | 2 | 16 | 1 | 367 | 0.27% |
| no_persona | MF | 2 | 17 | 6 | 367 | 1.63% |
| no_persona | MF | 2 | 18 | 3 | 367 | 0.82% |
| no_persona | MF | 2 | 19 | 0 | 367 | 0.00% |
| no_persona | MF | 2 | 20 | 0 | 367 | 0.00% |
| no_persona | MF | 3 | 0 | 0 | 149 | 0.00% |
| no_persona | MF | 3 | 1 | 0 | 149 | 0.00% |
| no_persona | MF | 3 | 2 | 0 | 149 | 0.00% |
| no_persona | MF | 3 | 3 | 3 | 149 | 2.01% |
| no_persona | MF | 3 | 4 | 4 | 149 | 2.68% |
| no_persona | MF | 3 | 5 | 20 | 149 | 13.42% |
| no_persona | MF | 3 | 6 | 14 | 149 | 9.40% |
| no_persona | MF | 3 | 7 | 11 | 149 | 7.38% |
| no_persona | MF | 3 | 8 | 19 | 149 | 12.75% |
| no_persona | MF | 3 | 9 | 9 | 149 | 6.04% |
| no_persona | MF | 3 | 10 | 35 | 149 | 23.49% |
| no_persona | MF | 3 | 11 | 9 | 149 | 6.04% |
| no_persona | MF | 3 | 12 | 9 | 149 | 6.04% |
| no_persona | MF | 3 | 13 | 5 | 149 | 3.36% |
| no_persona | MF | 3 | 14 | 2 | 149 | 1.34% |
| no_persona | MF | 3 | 15 | 3 | 149 | 2.01% |
| no_persona | MF | 3 | 16 | 4 | 149 | 2.68% |
| no_persona | MF | 3 | 17 | 0 | 149 | 0.00% |
| no_persona | MF | 3 | 18 | 1 | 149 | 0.67% |
| no_persona | MF | 3 | 19 | 0 | 149 | 0.00% |
| no_persona | MF | 3 | 20 | 1 | 149 | 0.67% |
| no_persona | MultiVAE | 1 | 0 | 2 | 484 | 0.41% |
| no_persona | MultiVAE | 1 | 1 | 0 | 484 | 0.00% |
| no_persona | MultiVAE | 1 | 2 | 4 | 484 | 0.83% |
| no_persona | MultiVAE | 1 | 3 | 19 | 484 | 3.93% |
| no_persona | MultiVAE | 1 | 4 | 24 | 484 | 4.96% |
| no_persona | MultiVAE | 1 | 5 | 45 | 484 | 9.30% |
| no_persona | MultiVAE | 1 | 6 | 42 | 484 | 8.68% |
| no_persona | MultiVAE | 1 | 7 | 45 | 484 | 9.30% |
| no_persona | MultiVAE | 1 | 8 | 49 | 484 | 10.12% |
| no_persona | MultiVAE | 1 | 9 | 47 | 484 | 9.71% |
| no_persona | MultiVAE | 1 | 10 | 96 | 484 | 19.83% |
| no_persona | MultiVAE | 1 | 11 | 30 | 484 | 6.20% |
| no_persona | MultiVAE | 1 | 12 | 22 | 484 | 4.55% |
| no_persona | MultiVAE | 1 | 13 | 19 | 484 | 3.93% |
| no_persona | MultiVAE | 1 | 14 | 7 | 484 | 1.45% |
| no_persona | MultiVAE | 1 | 15 | 8 | 484 | 1.65% |
| no_persona | MultiVAE | 1 | 16 | 10 | 484 | 2.07% |
| no_persona | MultiVAE | 1 | 17 | 8 | 484 | 1.65% |
| no_persona | MultiVAE | 1 | 18 | 2 | 484 | 0.41% |
| no_persona | MultiVAE | 1 | 19 | 5 | 484 | 1.03% |
| no_persona | MultiVAE | 1 | 20 | 0 | 484 | 0.00% |
| no_persona | MultiVAE | 2 | 0 | 2 | 367 | 0.54% |
| no_persona | MultiVAE | 2 | 1 | 1 | 367 | 0.27% |
| no_persona | MultiVAE | 2 | 2 | 4 | 367 | 1.09% |
| no_persona | MultiVAE | 2 | 3 | 3 | 367 | 0.82% |
| no_persona | MultiVAE | 2 | 4 | 13 | 367 | 3.54% |
| no_persona | MultiVAE | 2 | 5 | 30 | 367 | 8.17% |
| no_persona | MultiVAE | 2 | 6 | 37 | 367 | 10.08% |
| no_persona | MultiVAE | 2 | 7 | 30 | 367 | 8.17% |
| no_persona | MultiVAE | 2 | 8 | 35 | 367 | 9.54% |
| no_persona | MultiVAE | 2 | 9 | 41 | 367 | 11.17% |
| no_persona | MultiVAE | 2 | 10 | 101 | 367 | 27.52% |
| no_persona | MultiVAE | 2 | 11 | 12 | 367 | 3.27% |
| no_persona | MultiVAE | 2 | 12 | 10 | 367 | 2.72% |
| no_persona | MultiVAE | 2 | 13 | 14 | 367 | 3.81% |
| no_persona | MultiVAE | 2 | 14 | 12 | 367 | 3.27% |
| no_persona | MultiVAE | 2 | 15 | 8 | 367 | 2.18% |
| no_persona | MultiVAE | 2 | 16 | 7 | 367 | 1.91% |
| no_persona | MultiVAE | 2 | 17 | 2 | 367 | 0.54% |
| no_persona | MultiVAE | 2 | 18 | 3 | 367 | 0.82% |
| no_persona | MultiVAE | 2 | 19 | 2 | 367 | 0.54% |
| no_persona | MultiVAE | 2 | 20 | 0 | 367 | 0.00% |
| no_persona | MultiVAE | 3 | 0 | 2 | 149 | 1.34% |
| no_persona | MultiVAE | 3 | 1 | 1 | 149 | 0.67% |
| no_persona | MultiVAE | 3 | 2 | 0 | 149 | 0.00% |
| no_persona | MultiVAE | 3 | 3 | 10 | 149 | 6.71% |
| no_persona | MultiVAE | 3 | 4 | 6 | 149 | 4.03% |
| no_persona | MultiVAE | 3 | 5 | 13 | 149 | 8.72% |
| no_persona | MultiVAE | 3 | 6 | 10 | 149 | 6.71% |
| no_persona | MultiVAE | 3 | 7 | 13 | 149 | 8.72% |
| no_persona | MultiVAE | 3 | 8 | 16 | 149 | 10.74% |
| no_persona | MultiVAE | 3 | 9 | 21 | 149 | 14.09% |
| no_persona | MultiVAE | 3 | 10 | 25 | 149 | 16.78% |
| no_persona | MultiVAE | 3 | 11 | 12 | 149 | 8.05% |
| no_persona | MultiVAE | 3 | 12 | 5 | 149 | 3.36% |
| no_persona | MultiVAE | 3 | 13 | 5 | 149 | 3.36% |
| no_persona | MultiVAE | 3 | 14 | 4 | 149 | 2.68% |
| no_persona | MultiVAE | 3 | 15 | 5 | 149 | 3.36% |
| no_persona | MultiVAE | 3 | 16 | 1 | 149 | 0.67% |
| no_persona | MultiVAE | 3 | 17 | 0 | 149 | 0.00% |
| no_persona | MultiVAE | 3 | 18 | 0 | 149 | 0.00% |
| no_persona | MultiVAE | 3 | 19 | 0 | 149 | 0.00% |
| no_persona | MultiVAE | 3 | 20 | 0 | 149 | 0.00% |

## Outcomes and Watch Rates

Outcomes are per clicked-item assessment; watch rates are per model-user case.
Zero-click cases are deterministically not_ready and have no item-level outcomes.

| Condition | Model | Confirmed | Contradicted | Insufficient | Assessed items | Watch | Not ready | Watch rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | LightGCN | 3893 (43.90%) | 33 (0.37%) | 4942 (55.73%) | 8868 | 953 | 47 | 95.30% |
| full | MF | 3793 (41.47%) | 37 (0.40%) | 5317 (58.13%) | 9147 | 951 | 49 | 95.10% |
| full | MultiVAE | 3863 (42.74%) | 34 (0.38%) | 5141 (56.88%) | 9038 | 962 | 38 | 96.20% |
| no_demographics | LightGCN | 3984 (45.17%) | 34 (0.39%) | 4802 (54.44%) | 8820 | 955 | 45 | 95.50% |
| no_demographics | MF | 3800 (41.98%) | 34 (0.38%) | 5218 (57.64%) | 9052 | 952 | 48 | 95.20% |
| no_demographics | MultiVAE | 4127 (45.95%) | 30 (0.33%) | 4824 (53.71%) | 8981 | 944 | 56 | 94.40% |
| no_interaction_history | LightGCN | 4516 (52.57%) | 58 (0.68%) | 4016 (46.75%) | 8590 | 770 | 230 | 77.00% |
| no_interaction_history | MF | 4442 (50.91%) | 55 (0.63%) | 4229 (48.46%) | 8726 | 786 | 214 | 78.60% |
| no_interaction_history | MultiVAE | 4727 (53.98%) | 59 (0.67%) | 3971 (45.35%) | 8757 | 772 | 228 | 77.20% |
| no_persona | LightGCN | 2639 (30.55%) | 24 (0.28%) | 5975 (69.17%) | 8638 | 960 | 40 | 96.00% |
| no_persona | MF | 2657 (29.68%) | 24 (0.27%) | 6270 (70.05%) | 8951 | 961 | 39 | 96.10% |
| no_persona | MultiVAE | 2639 (30.24%) | 14 (0.16%) | 6074 (69.60%) | 8727 | 960 | 40 | 96.00% |

## Adjacent Clicks by Diversity

Pooled fraction weights clicked items; mean case fraction excludes zero-click cases.

| Condition | Model | Diversity | Clicked items | Adjacent items | Pooled adjacent fraction | Mean case fraction |
|---|---|---:|---:|---:|---:|---:|
| full | LightGCN | 1 | 1390 | 0 | 0.000000 | 0.000000 |
| full | LightGCN | 2 | 3112 | 13 | 0.004177 | 0.004925 |
| full | LightGCN | 3 | 4366 | 13 | 0.002978 | 0.003401 |
| full | MF | 1 | 1397 | 0 | 0.000000 | 0.000000 |
| full | MF | 2 | 3265 | 5 | 0.001531 | 0.002167 |
| full | MF | 3 | 4485 | 8 | 0.001784 | 0.002112 |
| full | MultiVAE | 1 | 1426 | 5 | 0.003506 | 0.004697 |
| full | MultiVAE | 2 | 3133 | 6 | 0.001915 | 0.001958 |
| full | MultiVAE | 3 | 4479 | 8 | 0.001786 | 0.003418 |
| no_demographics | LightGCN | 1 | 1359 | 1 | 0.000736 | 0.001212 |
| no_demographics | LightGCN | 2 | 3065 | 11 | 0.003589 | 0.004603 |
| no_demographics | LightGCN | 3 | 4396 | 7 | 0.001592 | 0.001496 |
| no_demographics | MF | 1 | 1426 | 4 | 0.002805 | 0.005839 |
| no_demographics | MF | 2 | 3262 | 9 | 0.002759 | 0.003589 |
| no_demographics | MF | 3 | 4364 | 15 | 0.003437 | 0.003884 |
| no_demographics | MultiVAE | 1 | 1437 | 8 | 0.005567 | 0.007208 |
| no_demographics | MultiVAE | 2 | 3070 | 5 | 0.001629 | 0.001459 |
| no_demographics | MultiVAE | 3 | 4474 | 7 | 0.001565 | 0.002346 |
| no_interaction_history | LightGCN | 1 | 1367 | 4 | 0.002926 | 0.003168 |
| no_interaction_history | LightGCN | 2 | 2965 | 7 | 0.002361 | 0.003970 |
| no_interaction_history | LightGCN | 3 | 4258 | 7 | 0.001644 | 0.002608 |
| no_interaction_history | MF | 1 | 1407 | 10 | 0.007107 | 0.006860 |
| no_interaction_history | MF | 2 | 3095 | 20 | 0.006462 | 0.008070 |
| no_interaction_history | MF | 3 | 4224 | 5 | 0.001184 | 0.001549 |
| no_interaction_history | MultiVAE | 1 | 1437 | 7 | 0.004871 | 0.006414 |
| no_interaction_history | MultiVAE | 2 | 3064 | 8 | 0.002611 | 0.004284 |
| no_interaction_history | MultiVAE | 3 | 4256 | 13 | 0.003055 | 0.004142 |
| no_persona | LightGCN | 1 | 1421 | 4 | 0.002815 | 0.008130 |
| no_persona | LightGCN | 2 | 2974 | 10 | 0.003362 | 0.004139 |
| no_persona | LightGCN | 3 | 4243 | 12 | 0.002828 | 0.004576 |
| no_persona | MF | 1 | 1499 | 2 | 0.001334 | 0.001481 |
| no_persona | MF | 2 | 3121 | 12 | 0.003845 | 0.005063 |
| no_persona | MF | 3 | 4331 | 13 | 0.003002 | 0.005327 |
| no_persona | MultiVAE | 1 | 1408 | 6 | 0.004261 | 0.004818 |
| no_persona | MultiVAE | 2 | 3125 | 12 | 0.003840 | 0.005731 |
| no_persona | MultiVAE | 3 | 4194 | 12 | 0.002861 | 0.002812 |

## Predicted and Aggregate Ratings by Conformity

Aggregate ratings use checkpoint-training interactions only. Pearson correlation is descriptive
over pooled clicked-item assessments; repeated users/items are not independent observations.

| Condition | Model | Conformity | Items with aggregate rating | Mean predicted | Mean aggregate | Mean absolute difference | Pearson r |
|---|---|---:|---:|---:|---:|---:|---:|
| full | LightGCN | 1 | 2274 | 4.058487 | 4.046909 | 0.388879 | 0.672333 |
| full | LightGCN | 2 | 4780 | 4.001674 | 3.981383 | 0.407341 | 0.676551 |
| full | LightGCN | 3 | 1814 | 3.981257 | 3.896803 | 0.420364 | 0.710349 |
| full | MF | 1 | 2386 | 4.060352 | 4.037087 | 0.393248 | 0.678372 |
| full | MF | 2 | 4842 | 3.977489 | 3.952177 | 0.412458 | 0.686023 |
| full | MF | 3 | 1919 | 3.897863 | 3.854825 | 0.416764 | 0.717764 |
| full | MultiVAE | 1 | 2334 | 4.079263 | 4.065261 | 0.386812 | 0.675649 |
| full | MultiVAE | 2 | 4839 | 4.004340 | 3.978419 | 0.406214 | 0.676961 |
| full | MultiVAE | 3 | 1865 | 3.998928 | 3.906118 | 0.422879 | 0.700019 |
| no_demographics | LightGCN | 1 | 2245 | 4.083296 | 4.050891 | 0.398855 | 0.646393 |
| no_demographics | LightGCN | 2 | 4729 | 4.033199 | 3.980385 | 0.412569 | 0.683227 |
| no_demographics | LightGCN | 3 | 1846 | 3.988624 | 3.895720 | 0.432416 | 0.697677 |
| no_demographics | MF | 1 | 2330 | 4.079399 | 4.039845 | 0.405571 | 0.671413 |
| no_demographics | MF | 2 | 4843 | 4.000000 | 3.963269 | 0.414976 | 0.677540 |
| no_demographics | MF | 3 | 1879 | 3.927089 | 3.864795 | 0.412331 | 0.708105 |
| no_demographics | MultiVAE | 1 | 2302 | 4.101216 | 4.068445 | 0.395569 | 0.657165 |
| no_demographics | MultiVAE | 2 | 4827 | 4.036047 | 3.987713 | 0.417470 | 0.678060 |
| no_demographics | MultiVAE | 3 | 1852 | 3.991361 | 3.911712 | 0.417187 | 0.696853 |
| no_interaction_history | LightGCN | 1 | 2237 | 4.035762 | 4.054032 | 0.404019 | 0.690424 |
| no_interaction_history | LightGCN | 2 | 4648 | 4.014415 | 3.995654 | 0.411687 | 0.677389 |
| no_interaction_history | LightGCN | 3 | 1705 | 3.973607 | 3.899150 | 0.432850 | 0.722493 |
| no_interaction_history | MF | 1 | 2236 | 4.065295 | 4.049718 | 0.407518 | 0.669665 |
| no_interaction_history | MF | 2 | 4732 | 3.986686 | 3.976729 | 0.417126 | 0.682383 |
| no_interaction_history | MF | 3 | 1758 | 3.942548 | 3.869101 | 0.418111 | 0.724268 |
| no_interaction_history | MultiVAE | 1 | 2258 | 4.090788 | 4.072653 | 0.404513 | 0.682914 |
| no_interaction_history | MultiVAE | 2 | 4751 | 4.013050 | 3.999688 | 0.418800 | 0.678710 |
| no_interaction_history | MultiVAE | 3 | 1748 | 3.995995 | 3.923238 | 0.435870 | 0.669162 |
| no_persona | LightGCN | 1 | 2230 | 4.057848 | 4.098022 | 0.359045 | 0.653886 |
| no_persona | LightGCN | 2 | 4644 | 3.970715 | 4.017771 | 0.381135 | 0.683554 |
| no_persona | LightGCN | 3 | 1764 | 3.904762 | 3.919535 | 0.400556 | 0.700359 |
| no_persona | MF | 1 | 2325 | 4.055914 | 4.067798 | 0.369880 | 0.684034 |
| no_persona | MF | 2 | 4722 | 3.986235 | 3.997706 | 0.385597 | 0.688795 |
| no_persona | MF | 3 | 1904 | 3.870273 | 3.874196 | 0.387453 | 0.718067 |
| no_persona | MultiVAE | 1 | 2257 | 4.048737 | 4.097093 | 0.366035 | 0.658356 |
| no_persona | MultiVAE | 2 | 4641 | 4.010343 | 4.023452 | 0.381013 | 0.673708 |
| no_persona | MultiVAE | 3 | 1829 | 3.937671 | 3.927808 | 0.380558 | 0.706880 |

## 最终缺失案例

- full: 0 个；清单 unrecovered_cases_full.json。
- no_demographics: 0 个；清单 unrecovered_cases_no_demographics.json。
- no_persona: 0 个；清单 unrecovered_cases_no_persona.json。
- no_interaction_history: 0 个；清单 unrecovered_cases_no_interaction_history.json。
