# Rating-Cue Ablation

FINAL. All four treatment runs have 1,000 users, exit 0, and passed audits. Both reference runs passed transfer validation. Stored paired statistics were recomputed from raw behavior and agree to numerical tolerance.

Common-prefix candidate/order mismatches: 0. Watch is primary; like is secondary. Selection rates retain zero-selection users. Uplift means are undefined without selection, and paired uplift inference includes users selecting in both conditions. All intervals below are paired-user 95% t intervals; p-values are raw two-sided paired tests.

Effects are shown minus hidden for rating ablation and swapped minus identity for crossover. Groups are original activity groups. The unchanged Occasional prompt is the crossover negative control.

## Identical-Exposure Primary Effects

| scope | activity_group | event | left | right | metric | paired_users | left_mean | right_mean | mean_difference | ci_low | ci_high | cohens_dz | p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common_prefix | 1 | watch | shown_included | R1 | selection_rate | 539 | 0.209841 | 0.219156 | -0.009315 | -0.017506 | -0.001124 | -0.096221 | 0.025900 |
| common_prefix | 1 | watch | shown_included | R1 | popularity_uplift_pp | 459 | 1.331709 | 0.987504 | 0.344206 | -0.071288 | 0.759699 | 0.075988 | 0.104216 |
| common_prefix | 1 | watch | shown_included | R1 | rating_uplift | 459 | 0.123803 | 0.096260 | 0.027543 | 0.010992 | 0.044094 | 0.152645 | 0.001155 |
| common_prefix | 1 | watch | shown_included | R1 | selected_count | 539 | 1.686456 | 1.721707 | -0.035250 | -0.082297 | 0.011796 | -0.063397 | 0.141645 |
| common_prefix | 1 | watch | shown_excluded | R2 | selection_rate | 539 | 0.568220 | 0.601848 | -0.033627 | -0.054201 | -0.013054 | -0.138297 | 0.001403 |
| common_prefix | 1 | watch | shown_excluded | R2 | popularity_uplift_pp | 496 | 0.605162 | 0.371274 | 0.233888 | -0.006023 | 0.473799 | 0.086006 | 0.056012 |
| common_prefix | 1 | watch | shown_excluded | R2 | rating_uplift | 496 | 0.059271 | 0.036983 | 0.022288 | 0.012264 | 0.032313 | 0.196151 | 0.000015 |
| common_prefix | 1 | watch | shown_excluded | R2 | selected_count | 539 | 4.489796 | 4.721707 | -0.231911 | -0.375529 | -0.088293 | -0.136630 | 0.001600 |
| common_prefix | 2 | watch | shown_included | R1 | selection_rate | 352 | 0.370656 | 0.373284 | -0.002628 | -0.019585 | 0.014330 | -0.016245 | 0.760713 |
| common_prefix | 2 | watch | shown_included | R1 | popularity_uplift_pp | 323 | 1.015415 | 0.757395 | 0.258020 | -0.008211 | 0.524251 | 0.106091 | 0.057452 |
| common_prefix | 2 | watch | shown_included | R1 | rating_uplift | 323 | 0.095448 | 0.063436 | 0.032012 | 0.018774 | 0.045250 | 0.264711 | 0.000003 |
| common_prefix | 2 | watch | shown_included | R1 | selected_count | 352 | 5.403409 | 5.357955 | 0.045455 | -0.154672 | 0.245581 | 0.023809 | 0.655364 |
| common_prefix | 2 | watch | shown_excluded | R2 | selection_rate | 352 | 0.627557 | 0.636210 | -0.008653 | -0.028551 | 0.011245 | -0.045586 | 0.392983 |
| common_prefix | 2 | watch | shown_excluded | R2 | popularity_uplift_pp | 339 | 0.489782 | 0.421063 | 0.068719 | -0.141746 | 0.279185 | 0.034882 | 0.521146 |
| common_prefix | 2 | watch | shown_excluded | R2 | rating_uplift | 339 | 0.043797 | 0.033164 | 0.010633 | 0.000048 | 0.021217 | 0.107323 | 0.048966 |
| common_prefix | 2 | watch | shown_excluded | R2 | selected_count | 352 | 9.008523 | 9.071023 | -0.062500 | -0.323425 | 0.198425 | -0.025110 | 0.637862 |
| common_prefix | 3 | watch | shown_included | R1 | selection_rate | 109 | 0.727982 | 0.779931 | -0.051950 | -0.097931 | -0.005968 | -0.214499 | 0.027177 |
| common_prefix | 3 | watch | shown_included | R1 | popularity_uplift_pp | 103 | 0.105003 | 0.072126 | 0.032876 | -0.143146 | 0.208899 | 0.036503 | 0.711806 |
| common_prefix | 3 | watch | shown_included | R1 | rating_uplift | 103 | 0.009601 | 0.008108 | 0.001493 | -0.008531 | 0.011518 | 0.029111 | 0.768255 |
| common_prefix | 3 | watch | shown_included | R1 | selected_count | 109 | 11.366972 | 11.935780 | -0.568807 | -1.202387 | 0.064772 | -0.170448 | 0.077966 |
| common_prefix | 3 | watch | shown_excluded | R2 | selection_rate | 109 | 0.690099 | 0.701109 | -0.011009 | -0.050676 | 0.028658 | -0.052693 | 0.583362 |
| common_prefix | 3 | watch | shown_excluded | R2 | popularity_uplift_pp | 105 | 0.324886 | 0.204623 | 0.120263 | -0.266712 | 0.507237 | 0.060143 | 0.539055 |
| common_prefix | 3 | watch | shown_excluded | R2 | rating_uplift | 105 | 0.034188 | 0.021735 | 0.012453 | -0.002183 | 0.027089 | 0.164654 | 0.094562 |
| common_prefix | 3 | watch | shown_excluded | R2 | selected_count | 109 | 10.825688 | 11.055046 | -0.229358 | -0.766750 | 0.308034 | -0.081031 | 0.399430 |

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
| full_session | shown_excluded | 1 | Infrequent | Excluded | True | Identity | watch | 539 | 531 | 0.538397 | 4.150278 | 4.150278 | 7.406308 | 9.307978 | 93.353964 | 93.946688 | 0.592725 | 3.909847 | 3.967637 | 0.057789 |
| full_session | shown_excluded | 1 | Infrequent | Excluded | True | Identity | like | 539 | 492 | 0.294612 | 4.150278 | 4.150278 | 7.406308 | 5.172542 | 93.640742 | 95.578641 | 1.937899 | 3.926705 | 4.116952 | 0.190247 |
| full_session | shown_excluded | 2 | Occasional | Excluded | True | Identity | watch | 352 | 346 | 0.617969 | 4.318182 | 4.318182 | 7.875000 | 11.031250 | 93.490581 | 93.996820 | 0.506239 | 3.845416 | 3.891870 | 0.046454 |
| full_session | shown_excluded | 2 | Occasional | Excluded | True | Identity | like | 352 | 315 | 0.294188 | 4.318182 | 4.318182 | 7.875000 | 5.281250 | 93.848984 | 95.686712 | 1.837728 | 3.872456 | 4.082661 | 0.210205 |
| full_session | shown_excluded | 3 | Frequent | Excluded | True | Identity | watch | 109 | 108 | 0.701644 | 4.330275 | 4.330275 | 7.926606 | 12.394495 | 91.946468 | 92.207534 | 0.261066 | 3.790209 | 3.816569 | 0.026360 |
| full_session | shown_excluded | 3 | Frequent | Excluded | True | Identity | like | 109 | 96 | 0.285665 | 4.330275 | 4.330275 | 7.926606 | 5.174312 | 92.128633 | 94.601093 | 2.472460 | 3.815085 | 4.039928 | 0.224843 |
| full_session | R2 | 1 | Infrequent | Excluded | False | Identity | watch | 539 | 535 | 0.552381 | 4.235622 | 4.235622 | 7.625232 | 9.612245 | 93.363827 | 93.832479 | 0.468651 | 3.906613 | 3.949550 | 0.042937 |
| full_session | R2 | 1 | Infrequent | Excluded | False | Identity | like | 539 | 492 | 0.315484 | 4.235622 | 4.235622 | 7.625232 | 5.538033 | 93.512130 | 95.290396 | 1.778266 | 3.926169 | 4.081088 | 0.154919 |
| full_session | R2 | 2 | Occasional | Excluded | False | Identity | watch | 352 | 346 | 0.627320 | 4.312500 | 4.312500 | 7.934659 | 11.130682 | 93.582840 | 94.017762 | 0.434922 | 3.853490 | 3.884846 | 0.031356 |
| full_session | R2 | 2 | Occasional | Excluded | False | Identity | like | 352 | 316 | 0.324621 | 4.312500 | 4.312500 | 7.934659 | 5.775568 | 93.668140 | 95.401392 | 1.733252 | 3.867566 | 4.027036 | 0.159469 |
| full_session | R2 | 3 | Frequent | Excluded | False | Identity | watch | 109 | 106 | 0.703020 | 4.229358 | 4.229358 | 8.174312 | 12.284404 | 91.855912 | 92.106716 | 0.250804 | 3.789572 | 3.812395 | 0.022823 |
| full_session | R2 | 3 | Frequent | Excluded | False | Identity | like | 109 | 98 | 0.316743 | 4.229358 | 4.229358 | 8.174312 | 5.623853 | 91.902840 | 94.381253 | 2.478413 | 3.800534 | 3.990988 | 0.190454 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 459 | 0.209841 | 1.929499 | 2.278293 | 5.842301 | 1.686456 | 94.191488 | 95.523197 | 1.331709 | 3.948309 | 4.072112 | 0.123803 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 240 | 0.122720 | 1.929499 | 2.278293 | 5.842301 | 1.001855 | 95.025342 | 96.260822 | 1.235480 | 4.010741 | 4.178592 | 0.167851 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 323 | 0.370656 | 3.426136 | 3.892045 | 6.900568 | 5.403409 | 93.842729 | 94.858144 | 1.015415 | 3.858778 | 3.954225 | 0.095448 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 248 | 0.172680 | 3.426136 | 3.892045 | 6.900568 | 2.568182 | 94.441297 | 96.522914 | 2.081616 | 3.895710 | 4.136311 | 0.240601 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 103 | 0.727982 | 3.788991 | 4.761468 | 8.247706 | 11.366972 | 92.031780 | 92.136782 | 0.105003 | 3.792003 | 3.801604 | 0.009601 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 90 | 0.258410 | 3.788991 | 4.761468 | 8.247706 | 4.174312 | 92.370930 | 94.463162 | 2.092232 | 3.818433 | 4.043010 | 0.224577 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 459 | 0.219156 | 1.929499 | 2.499072 | 5.858998 | 1.721707 | 94.191488 | 95.178991 | 0.987504 | 3.948309 | 4.044569 | 0.096260 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 240 | 0.121715 | 1.929499 | 2.499072 | 5.858998 | 0.979592 | 95.025342 | 96.246372 | 1.221030 | 4.010741 | 4.160784 | 0.150043 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 323 | 0.373284 | 3.426136 | 3.934659 | 6.971591 | 5.357955 | 93.842729 | 94.600123 | 0.757395 | 3.858778 | 3.922214 | 0.063436 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 248 | 0.195762 | 3.426136 | 3.934659 | 6.971591 | 2.863636 | 94.441297 | 96.554108 | 2.112811 | 3.895710 | 4.085223 | 0.189513 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 103 | 0.779931 | 3.788991 | 4.697248 | 8.541284 | 11.935780 | 92.031780 | 92.103906 | 0.072126 | 3.792003 | 3.800111 | 0.008108 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 90 | 0.340023 | 3.788991 | 4.697248 | 8.541284 | 5.376147 | 92.370930 | 94.318137 | 1.947207 | 3.818433 | 4.010710 | 0.192277 |
| common_prefix | shown_excluded | 1 | Infrequent | Excluded | True | Identity | watch | 539 | 496 | 0.568220 | 1.929499 | 4.150278 | 7.406308 | 4.489796 | 94.227717 | 94.832878 | 0.605162 | 3.951757 | 4.011028 | 0.059271 |
| common_prefix | shown_excluded | 1 | Infrequent | Excluded | True | Identity | like | 539 | 429 | 0.308867 | 1.929499 | 4.150278 | 7.406308 | 2.499072 | 94.505942 | 96.003081 | 1.497139 | 3.980744 | 4.145903 | 0.165159 |
| common_prefix | shown_excluded | 2 | Occasional | Excluded | True | Identity | watch | 352 | 339 | 0.627557 | 3.426136 | 4.318182 | 7.875000 | 9.008523 | 94.008131 | 94.497913 | 0.489782 | 3.864150 | 3.907947 | 0.043797 |
| common_prefix | shown_excluded | 2 | Occasional | Excluded | True | Identity | like | 352 | 290 | 0.297597 | 3.426136 | 4.318182 | 7.875000 | 4.326705 | 94.317851 | 95.995894 | 1.678043 | 3.890597 | 4.088421 | 0.197824 |
| common_prefix | shown_excluded | 3 | Frequent | Excluded | True | Identity | watch | 109 | 105 | 0.690099 | 3.788991 | 4.330275 | 7.926606 | 10.825688 | 92.138468 | 92.463353 | 0.324886 | 3.794121 | 3.828310 | 0.034188 |
| common_prefix | shown_excluded | 3 | Frequent | Excluded | True | Identity | like | 109 | 91 | 0.278861 | 3.788991 | 4.330275 | 7.926606 | 4.559633 | 92.318225 | 94.538456 | 2.220231 | 3.819589 | 4.047682 | 0.228092 |
| common_prefix | R2 | 1 | Infrequent | Excluded | False | Identity | watch | 539 | 496 | 0.601848 | 1.929499 | 4.235622 | 7.625232 | 4.721707 | 94.227717 | 94.598990 | 0.371274 | 3.951757 | 3.988740 | 0.036983 |
| common_prefix | R2 | 1 | Infrequent | Excluded | False | Identity | like | 539 | 429 | 0.341759 | 1.929499 | 4.235622 | 7.625232 | 2.734694 | 94.505942 | 95.847896 | 1.341954 | 3.980744 | 4.120364 | 0.139620 |
| common_prefix | R2 | 2 | Occasional | Excluded | False | Identity | watch | 352 | 339 | 0.636210 | 3.426136 | 4.312500 | 7.934659 | 9.071023 | 94.008131 | 94.429193 | 0.421063 | 3.864150 | 3.897315 | 0.033164 |
| common_prefix | R2 | 2 | Occasional | Excluded | False | Identity | like | 352 | 290 | 0.331214 | 3.426136 | 4.312500 | 7.934659 | 4.772727 | 94.317851 | 95.938086 | 1.620235 | 3.890597 | 4.050451 | 0.159854 |
| common_prefix | R2 | 3 | Frequent | Excluded | False | Identity | watch | 109 | 105 | 0.701109 | 3.788991 | 4.229358 | 8.174312 | 11.055046 | 92.138468 | 92.343091 | 0.204623 | 3.794121 | 3.815857 | 0.021735 |
| common_prefix | R2 | 3 | Frequent | Excluded | False | Identity | like | 109 | 91 | 0.317469 | 3.788991 | 4.229358 | 8.174312 | 5.165138 | 92.318225 | 94.462970 | 2.144744 | 3.819589 | 4.010541 | 0.190952 |

## Caveats

Full-session results include differential page reach and are total effects, not identical-exposure comparisons. Uplift is conditional on selection and can change with the selected-user subset. Conformity was not manipulated. Confidence intervals are not multiplicity-adjusted; these are simulator outcomes, not human-behavior estimates.

See JINYI_RATING_ABLATION_HANDOFF.md and the per-user/paired CSVs for all secondary outcomes, paired coverage, means, Cohen's dz, and raw p-values.
