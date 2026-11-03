# Pilot-30 social-trait counterfactual audit

## Integrity

- Completed actions: 807/810
- Failures: 3
- Estimated API cost: $1.104175

## Design

Same users, profiles, backbone candidates, and action prompt; one social-trait level is assigned at a time. Confidence intervals use a user-cluster bootstrap.

## Activity

Common cases: 90. Runs: L1 `20261103_130843_d9c739bd7f`, L2 `20261103_131204_cd74c002cf`, L3 `20261103_131602_5fe03767ee`

| Metric | Level 1 | Level 2 | Level 3 |
|---|---:|---:|---:|
| click_count | 5.1778 | 5.1333 | 5.5667 |
| conversion_abstention | 0.0000 | 0.0000 | 0.0000 |
| unique_clicked_genres | 5.5111 | 5.4778 | 5.6778 |
| novel_genre_fraction | 0.2099 | 0.2108 | 0.2104 |
| clicked_average_rating | 4.0667 | 4.0619 | 4.0593 |
| rating_selection_lift | 0.2647 | 0.2599 | 0.2573 |
| top_bottom_rating_click_gap | 0.4907 | 0.4704 | 0.5000 |

Primary measure: `click_count`.

Expected-direction L3-L1: 0.3889 (95% user-cluster bootstrap CI [0.0778, 0.7444]).

Case-level non-strict monotonicity: 71.1%.

## Conformity

Common cases: 89. Runs: L1 `20261103_131443_803709e288`, L2 `20261103_131833_192d962da9`, L3 `20261103_131051_f518b5e6a4`

| Metric | Level 1 | Level 2 | Level 3 |
|---|---:|---:|---:|
| click_count | 5.3483 | 5.0787 | 5.0899 |
| conversion_abstention | 0.0000 | 0.0000 | 0.0000 |
| unique_clicked_genres | 5.5843 | 5.4382 | 5.4157 |
| novel_genre_fraction | 0.2155 | 0.2178 | 0.2135 |
| clicked_average_rating | 4.0696 | 4.0640 | 4.0722 |
| rating_selection_lift | 0.2645 | 0.2589 | 0.2671 |
| top_bottom_rating_click_gap | 0.4963 | 0.4700 | 0.4906 |

Primary measure: `rating_selection_lift`.

Expected-direction L1-L3: -0.0026 (95% user-cluster bootstrap CI [-0.0113, 0.0065]).

Case-level non-strict monotonicity: 41.6%.

## Diversity

Common cases: 89. Runs: L1 `20261103_131717_95ad783039`, L2 `20261103_130930_2171c3cc51`, L3 `20261103_131350_0561dca894`

| Metric | Level 1 | Level 2 | Level 3 |
|---|---:|---:|---:|
| click_count | 5.2247 | 5.2360 | 5.3146 |
| conversion_abstention | 0.0000 | 0.0000 | 0.0000 |
| unique_clicked_genres | 5.5393 | 5.5169 | 5.5506 |
| novel_genre_fraction | 0.2104 | 0.2289 | 0.2195 |
| clicked_average_rating | 4.0658 | 4.0602 | 4.0675 |
| rating_selection_lift | 0.2619 | 0.2563 | 0.2636 |
| top_bottom_rating_click_gap | 0.4813 | 0.4738 | 0.4775 |

Primary measure: `novel_genre_fraction`.

Expected-direction L3-L1: 0.0090 (95% user-cluster bootstrap CI [-0.0074, 0.0257]).

Case-level non-strict monotonicity: 67.4%.

## Interpretation

- Activity shows a positive endpoint effect: level 3 produces 0.389 more clicks than
  level 1, and the user-cluster confidence interval excludes zero. Level 2 is slightly
  below level 1, so the mean response is not fully monotonic. Conversion abstention is
  zero at every level, meaning activity affects exploration count but not conversion
  readiness under the current one-choice prompt.
- Conformity is not causally reflected by the preregistered rating-selection measure.
  The endpoint effect is near zero, points in the wrong direction, and its confidence
  interval contains zero.
- Diversity is directionally positive from level 1 to level 3, but the confidence
  interval contains zero and level 2 exceeds level 3. This is insufficient evidence of
  reliable causal adherence.

The social-trait prompt should therefore remain opt-in rather than become the default.
Only activity has clear intervention evidence, and none of the traits changes the
model's universal one-item conversion behavior.
