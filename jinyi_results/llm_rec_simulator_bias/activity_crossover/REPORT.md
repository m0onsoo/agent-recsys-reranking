# Activity Crossover

FINAL. All four treatment runs have 1,000 users, exit 0, and passed audits. Both reference runs passed transfer validation. Stored paired statistics were recomputed from raw behavior and agree to numerical tolerance.

Common-prefix candidate/order mismatches: 0. Watch is primary; like is secondary. Selection rates retain zero-selection users. Uplift means are undefined without selection, and paired uplift inference includes users selecting in both conditions. All intervals below are paired-user 95% t intervals; p-values are raw two-sided paired tests.

Effects are shown minus hidden for rating ablation and swapped minus identity for crossover. Groups are original activity groups. The unchanged Occasional prompt is the crossover negative control.

## Identical-Exposure Primary Effects

| scope | activity_group | event | left | right | metric | paired_users | left_mean | right_mean | mean_difference | ci_low | ci_high | cohens_dz | p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common_prefix | 1 | watch | R3 | shown_included | selection_rate | 539 | 0.822588 | 0.209609 | 0.612979 | 0.592474 | 0.633484 | 2.529413 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | popularity_uplift_pp | 471 | 0.065774 | 1.341390 | -1.275616 | -1.724484 | -0.826748 | -0.257311 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | rating_uplift | 471 | 0.003242 | 0.125347 | -0.122105 | -0.140960 | -0.103250 | -0.586352 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | selected_count | 539 | 6.371058 | 1.690167 | 4.680891 | 4.435556 | 4.926225 | 1.614362 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | selection_rate | 539 | 0.808905 | 0.219156 | 0.589750 | 0.568634 | 0.610865 | 2.363198 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | popularity_uplift_pp | 486 | 0.046922 | 0.954296 | -0.907374 | -1.389117 | -0.425630 | -0.167875 | 0.000239 |
| common_prefix | 1 | watch | R4 | R1 | rating_uplift | 486 | 0.002858 | 0.095954 | -0.093095 | -0.111154 | -0.075037 | -0.459470 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | selected_count | 539 | 6.269017 | 1.727273 | 4.541744 | 4.298624 | 4.784864 | 1.580643 | 0.000000 |
| common_prefix | 2 | watch | R3 | shown_included | selection_rate | 352 | 0.369721 | 0.369271 | 0.000450 | -0.014912 | 0.015812 | 0.003069 | 0.954109 |
| common_prefix | 2 | watch | R3 | shown_included | popularity_uplift_pp | 323 | 0.943505 | 0.969898 | -0.026393 | -0.272538 | 0.219752 | -0.011738 | 0.833059 |
| common_prefix | 2 | watch | R3 | shown_included | rating_uplift | 323 | 0.098633 | 0.094127 | 0.004507 | -0.006983 | 0.015996 | 0.042937 | 0.440873 |
| common_prefix | 2 | watch | R3 | shown_included | selected_count | 352 | 5.210227 | 5.196023 | 0.014205 | -0.165624 | 0.194033 | 0.008280 | 0.876633 |
| common_prefix | 2 | watch | R4 | R1 | selection_rate | 352 | 0.361375 | 0.371863 | -0.010488 | -0.026754 | 0.005778 | -0.067589 | 0.205609 |
| common_prefix | 2 | watch | R4 | R1 | popularity_uplift_pp | 320 | 0.877712 | 0.792117 | 0.085595 | -0.178400 | 0.349589 | 0.035660 | 0.523998 |
| common_prefix | 2 | watch | R4 | R1 | rating_uplift | 320 | 0.066023 | 0.064977 | 0.001046 | -0.012230 | 0.014321 | 0.008662 | 0.876960 |
| common_prefix | 2 | watch | R4 | R1 | selected_count | 352 | 5.053977 | 5.173295 | -0.119318 | -0.309804 | 0.071168 | -0.065663 | 0.218794 |
| common_prefix | 3 | watch | R3 | shown_included | selection_rate | 109 | 0.188073 | 0.721521 | -0.533448 | -0.599435 | -0.467461 | -1.534846 | 0.000000 |
| common_prefix | 3 | watch | R3 | shown_included | popularity_uplift_pp | 82 | 1.899109 | 0.267613 | 1.631496 | 0.677127 | 2.585865 | 0.375619 | 0.001044 |
| common_prefix | 3 | watch | R3 | shown_included | rating_uplift | 82 | 0.126226 | 0.004700 | 0.121526 | 0.075911 | 0.167141 | 0.585383 | 0.000001 |
| common_prefix | 3 | watch | R3 | shown_included | selected_count | 109 | 1.779817 | 6.238532 | -4.458716 | -5.059950 | -3.857481 | -1.407974 | 0.000000 |
| common_prefix | 3 | watch | R4 | R1 | selection_rate | 109 | 0.202408 | 0.785168 | -0.582760 | -0.641901 | -0.523619 | -1.870811 | 0.000000 |
| common_prefix | 3 | watch | R4 | R1 | popularity_uplift_pp | 91 | 1.526876 | 0.094296 | 1.432581 | 0.279497 | 2.585665 | 0.258740 | 0.015468 |
| common_prefix | 3 | watch | R4 | R1 | rating_uplift | 91 | 0.091366 | 0.005493 | 0.085873 | 0.039192 | 0.132553 | 0.383113 | 0.000433 |
| common_prefix | 3 | watch | R4 | R1 | selected_count | 109 | 1.788991 | 6.917431 | -5.128440 | -5.810100 | -4.446781 | -1.428388 | 0.000000 |

## Full-Session and Common-Prefix Summaries

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 480 | 0.205898 | 2.278293 | 2.278293 | 5.842301 | 1.983302 | 94.045689 | 95.486934 | 1.441245 | 3.938684 | 4.067715 | 0.129031 |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 323 | 0.120207 | 2.278293 | 2.278293 | 5.842301 | 1.170686 | 95.010208 | 96.699245 | 1.689037 | 4.005171 | 4.205676 | 0.200505 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 333 | 0.367566 | 3.892045 | 3.892045 | 6.900568 | 6.056818 | 93.690463 | 94.719142 | 1.028678 | 3.854038 | 3.950029 | 0.095991 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 272 | 0.173627 | 3.892045 | 3.892045 | 6.900568 | 2.852273 | 94.096226 | 96.468399 | 2.372173 | 3.888820 | 4.145448 | 0.256628 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 108 | 0.743578 | 4.761468 | 4.761468 | 8.247706 | 14.229358 | 91.609339 | 91.773639 | 0.164300 | 3.780910 | 3.787070 | 0.006160 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 96 | 0.269495 | 4.761468 | 4.761468 | 8.247706 | 5.128440 | 91.960126 | 94.105021 | 2.144895 | 3.805988 | 4.032861 | 0.226872 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 503 | 0.212430 | 2.499072 | 2.499072 | 5.858998 | 2.202226 | 93.908492 | 94.969694 | 1.061203 | 3.940480 | 4.032958 | 0.092478 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 316 | 0.116922 | 2.499072 | 2.499072 | 5.858998 | 1.235622 | 94.676255 | 96.070711 | 1.394456 | 3.988056 | 4.133776 | 0.145721 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 334 | 0.366832 | 3.934659 | 3.934659 | 6.971591 | 6.071023 | 93.506963 | 94.325807 | 0.818844 | 3.849015 | 3.916430 | 0.067415 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 286 | 0.191489 | 3.934659 | 3.934659 | 6.971591 | 3.170455 | 93.801972 | 96.091520 | 2.289548 | 3.873180 | 4.059229 | 0.186049 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 109 | 0.772018 | 4.697248 | 4.697248 | 8.541284 | 14.550459 | 91.807616 | 91.984702 | 0.177086 | 3.784423 | 3.795143 | 0.010720 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 103 | 0.334518 | 4.697248 | 4.697248 | 8.541284 | 6.302752 | 91.711331 | 94.342980 | 2.631649 | 3.794519 | 3.999220 | 0.204701 |
| full_session | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | watch | 539 | 539 | 0.765724 | 4.727273 | 4.727273 | 8.384045 | 14.558442 | 93.247115 | 93.411647 | 0.164532 | 3.904643 | 3.915854 | 0.011211 |
| full_session | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | like | 539 | 525 | 0.364634 | 4.727273 | 4.727273 | 8.384045 | 6.940631 | 93.314260 | 95.743587 | 2.429327 | 3.907064 | 4.120877 | 0.213813 |
| full_session | R3 | 2 | Occasional | Included | True | Unchanged Occasional | watch | 352 | 336 | 0.370502 | 3.900568 | 3.900568 | 7.039773 | 6.122159 | 93.722457 | 94.693225 | 0.970769 | 3.852195 | 3.954621 | 0.102426 |
| full_session | R3 | 2 | Occasional | Included | True | Unchanged Occasional | like | 352 | 275 | 0.183984 | 3.900568 | 3.900568 | 7.039773 | 3.053977 | 94.157529 | 96.654680 | 2.497151 | 3.890748 | 4.138800 | 0.248052 |
| full_session | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | watch | 109 | 89 | 0.185589 | 2.486239 | 2.486239 | 5.788991 | 2.082569 | 92.413690 | 94.022579 | 1.608890 | 3.801638 | 3.923391 | 0.121753 |
| full_session | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | like | 109 | 44 | 0.060398 | 2.486239 | 2.486239 | 5.788991 | 0.660550 | 92.500688 | 96.278196 | 3.777509 | 3.858714 | 4.165985 | 0.307271 |
| full_session | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | watch | 539 | 539 | 0.737137 | 4.730983 | 4.730983 | 8.443414 | 14.014842 | 93.226788 | 93.341842 | 0.115054 | 3.904188 | 3.911092 | 0.006904 |
| full_session | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | like | 539 | 514 | 0.395841 | 4.730983 | 4.730983 | 8.443414 | 7.558442 | 93.327992 | 95.373098 | 2.045105 | 3.913885 | 4.071962 | 0.158077 |
| full_session | R4 | 2 | Occasional | Included | False | Unchanged Occasional | watch | 352 | 335 | 0.356558 | 3.906250 | 3.906250 | 6.946023 | 5.877841 | 93.624644 | 94.445934 | 0.821289 | 3.849034 | 3.913795 | 0.064760 |
| full_session | R4 | 2 | Occasional | Included | False | Unchanged Occasional | like | 352 | 283 | 0.185239 | 3.906250 | 3.906250 | 6.946023 | 3.099432 | 93.829345 | 96.166395 | 2.337051 | 3.873499 | 4.070406 | 0.196907 |
| full_session | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | watch | 109 | 97 | 0.192278 | 2.706422 | 2.706422 | 5.880734 | 2.247706 | 92.390246 | 93.729527 | 1.339281 | 3.796917 | 3.876848 | 0.079931 |
| full_session | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | like | 109 | 43 | 0.058295 | 2.706422 | 2.706422 | 5.880734 | 0.706422 | 91.395631 | 93.348186 | 1.952555 | 3.813933 | 4.087750 | 0.273817 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 471 | 0.209609 | 1.935065 | 2.278293 | 5.842301 | 1.690167 | 94.223406 | 95.564796 | 1.341390 | 3.950954 | 4.076301 | 0.125347 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 303 | 0.123183 | 1.935065 | 2.278293 | 5.842301 | 1.005566 | 95.167903 | 96.676019 | 1.508116 | 4.017325 | 4.204523 | 0.187198 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 323 | 0.369271 | 3.309659 | 3.892045 | 6.900568 | 5.196023 | 93.961135 | 94.931033 | 0.969898 | 3.863350 | 3.957476 | 0.094127 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 243 | 0.172100 | 3.309659 | 3.892045 | 6.900568 | 2.468750 | 94.433172 | 96.759590 | 2.326418 | 3.902253 | 4.155359 | 0.253105 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 82 | 0.721521 | 2.128440 | 4.761468 | 8.247706 | 6.238532 | 92.318519 | 92.586132 | 0.267613 | 3.794727 | 3.799426 | 0.004700 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 36 | 0.246942 | 2.128440 | 4.761468 | 8.247706 | 2.155963 | 92.700036 | 95.347045 | 2.647009 | 3.856535 | 4.061735 | 0.205200 |
| common_prefix | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | watch | 539 | 471 | 0.822588 | 1.935065 | 4.727273 | 8.384045 | 6.371058 | 94.223406 | 94.289180 | 0.065774 | 3.950954 | 3.954195 | 0.003242 |
| common_prefix | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | like | 539 | 303 | 0.385397 | 1.935065 | 4.727273 | 8.384045 | 3.070501 | 95.167903 | 96.599246 | 1.431343 | 4.017325 | 4.179212 | 0.161887 |
| common_prefix | R3 | 2 | Occasional | Included | True | Unchanged Occasional | watch | 352 | 323 | 0.369721 | 3.309659 | 3.900568 | 7.039773 | 5.210227 | 93.961135 | 94.904640 | 0.943505 | 3.863350 | 3.961983 | 0.098633 |
| common_prefix | R3 | 2 | Occasional | Included | True | Unchanged Occasional | like | 352 | 243 | 0.185144 | 3.309659 | 3.900568 | 7.039773 | 2.650568 | 94.433172 | 96.901224 | 2.468053 | 3.902253 | 4.144657 | 0.242404 |
| common_prefix | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | watch | 109 | 82 | 0.188073 | 2.128440 | 2.486239 | 5.788991 | 1.779817 | 92.318519 | 94.217628 | 1.899109 | 3.794727 | 3.920952 | 0.126226 |
| common_prefix | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | like | 109 | 36 | 0.060971 | 2.128440 | 2.486239 | 5.788991 | 0.568807 | 92.700036 | 96.474232 | 3.774196 | 3.856535 | 4.178204 | 0.321669 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 486 | 0.219156 | 1.935065 | 2.499072 | 5.858998 | 1.727273 | 94.053364 | 95.007660 | 0.954296 | 3.949187 | 4.045141 | 0.095954 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 296 | 0.121947 | 1.935065 | 2.499072 | 5.858998 | 0.981447 | 94.881191 | 96.130331 | 1.249140 | 4.001868 | 4.137382 | 0.135514 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 320 | 0.371863 | 3.309659 | 3.934659 | 6.971591 | 5.173295 | 93.986229 | 94.778346 | 0.792117 | 3.862236 | 3.927213 | 0.064977 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 259 | 0.194851 | 3.309659 | 3.934659 | 6.971591 | 2.761364 | 94.316100 | 96.467509 | 2.151409 | 3.892501 | 4.070022 | 0.177521 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 91 | 0.785168 | 2.128440 | 4.697248 | 8.541284 | 6.917431 | 92.462563 | 92.556858 | 0.094296 | 3.801087 | 3.806580 | 0.005493 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 40 | 0.329702 | 2.128440 | 4.697248 | 8.541284 | 2.880734 | 91.548482 | 93.634196 | 2.085714 | 3.811470 | 4.038582 | 0.227112 |
| common_prefix | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | watch | 539 | 486 | 0.808905 | 1.935065 | 4.730983 | 8.443414 | 6.269017 | 94.053364 | 94.100287 | 0.046922 | 3.949187 | 3.952046 | 0.002858 |
| common_prefix | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | like | 539 | 296 | 0.431161 | 1.935065 | 4.730983 | 8.443414 | 3.410019 | 94.881191 | 96.045878 | 1.164687 | 4.001868 | 4.121863 | 0.119995 |
| common_prefix | R4 | 2 | Occasional | Included | False | Unchanged Occasional | watch | 352 | 320 | 0.361375 | 3.309659 | 3.906250 | 6.946023 | 5.053977 | 93.986229 | 94.863940 | 0.877712 | 3.862236 | 3.928258 | 0.066023 |
| common_prefix | R4 | 2 | Occasional | Included | False | Unchanged Occasional | like | 352 | 259 | 0.186553 | 3.309659 | 3.906250 | 6.946023 | 2.690341 | 94.316100 | 96.527822 | 2.211722 | 3.892501 | 4.084165 | 0.191664 |
| common_prefix | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | watch | 109 | 91 | 0.202408 | 2.128440 | 2.706422 | 5.880734 | 1.788991 | 92.462563 | 93.989439 | 1.526876 | 3.801087 | 3.892453 | 0.091366 |
| common_prefix | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | like | 109 | 40 | 0.062882 | 2.128440 | 2.706422 | 5.880734 | 0.633028 | 91.548482 | 93.341655 | 1.793173 | 3.811470 | 4.078536 | 0.267066 |

## Caveats

Full-session results include differential page reach and are total effects, not identical-exposure comparisons. Uplift is conditional on selection and can change with the selected-user subset. Conformity was not manipulated. Confidence intervals are not multiplicity-adjusted; these are simulator outcomes, not human-behavior estimates.

See JINYI_RATING_ABLATION_HANDOFF.md and the per-user/paired CSVs for all secondary outcomes, paired coverage, means, Cohen's dz, and raw p-values.
