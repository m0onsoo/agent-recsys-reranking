# LLM user-simulator bias experiments (Agent4Rec and SimUSER)

This is an aggregate-only publication snapshot. Raw runs, per-user/exposure
records, transcripts, profiles, memories, manifests, and execution logs remain
off GitHub. All analysis was offline; no new model requests were made to prepare
this publication.

These experiments test three things in LLM-based user simulators:

1. whether showing movie ratings makes simulated users favor highly rated movies;
2. how much the "activity" description in the persona controls how much a user watches;
3. whether simulated users favor items shown first (position bias).

They answer Moonsoo's six requested runs on the
[llm-rec-simulator-bias](https://github.com/m0onsoo/llm-rec-simulator-bias) setup.

## Main findings

| # | Question | Answer |
|---|---|---|
| 1 | Does showing ratings push users toward highly rated movies? | **Yes, partly.** Hiding ratings reduces the rating preference by about 22–34% for Infrequent and Occasional users, but it does not remove it. How much users watch barely changes. |
| 2 | Does the activity description control behavior? | **Yes, almost completely.** Swapping the Infrequent and Frequent descriptions flips watch rates (0.21 → 0.82 and 0.72 → 0.19). Users whose description did not change act the same. |
| 3 | Is position bias causal? | **Yes.** With the order on each page randomly shuffled, the first item is still chosen more than the fourth: **+26% in Agent4Rec** and **+9% in SimUSER**. In Agent4Rec, the displayed position matters about 3× more than the item's original recommender rank. |

All results are about simulator behavior, not human behavior.

## Setup

- **Data and recommender:** MovieLens-1M, LightGCN; the same 1,000 users in every run.
- **Session:** 4 movies per page, up to 5 pages; the user can stop early.
- **LLM:** gpt-6-luna, temperature 0, reasoning effort none, simulation seed 101.
- **Disabled:** no ads, PQA or perception modules.
- **Completion:** every run below finished 1,000/1,000 users, exited with code 0 and passed its audit.
- **Analysis:** done offline from saved outputs; it made no extra API calls.

**Runs.** "Reference" runs were provided by Moonsoo and were not re-run.

| Run | Simulator | Activity description | Movie ratings | Item order |
|---|---|---|---|---|
| `shown_included` (reference) | Agent4Rec | included | shown | recommender rank |
| `shown_excluded` (reference) | Agent4Rec | removed | shown | recommender rank |
| R1 | Agent4Rec | included | **hidden** | recommender rank |
| R2 | Agent4Rec | removed | **hidden** | recommender rank |
| R3 | Agent4Rec | **Infrequent ↔ Frequent swapped** | shown | recommender rank |
| R4 | Agent4Rec | **Infrequent ↔ Frequent swapped** | **hidden** | recommender rank |
| P1, P2, P3 | Agent4Rec | included | shown | **random within page**, seeds 20261121 / 22 / 23 |
| S1, S2, S3 | SimUSER | (SimUSER persona) | shown | **random within page**, seeds 20261121 / 22 / 23 |
| vanilla (reference) | Agent4Rec, SimUSER | as above | shown | recommender rank |

**Terms used below**

- **Activity group:** the user's real activity level in MovieLens: Infrequent (539 users), Occasional (352) and Frequent (109). The persona describes the user with this level unless it is swapped.
- **Watch rate:** the share of shown movies the user watches. This is the primary outcome.
- **Rating uplift:** the average rating of movies the user watched minus the average rating of movies shown. A value above 0 means the user favors highly rated movies.
- **Paired comparison:** both runs are compared on exactly the same pages for the same users (the "common prefix", 0 candidate mismatches). Each user acts as their own control.
- **P1/P4:** the selection rate at position 1 divided by the rate at position 4. A value of 1 means no position bias.

## 1. Hiding movie ratings (R1, R2)

**Table 1. Rating uplift: ratings shown vs hidden** (Agent4Rec, watch, identical pages)

| Activity description | Group | Users | Shown | Hidden | Shown − hidden [95% CI] | Reduction |
|---|---|---:|---:|---:|---|---:|
| included | Infrequent | 459 | 0.124 | 0.096 | **+0.028 [+0.011, +0.044]** | 22% |
| included | Occasional | 323 | 0.095 | 0.063 | **+0.032 [+0.019, +0.045]** | 34% |
| included | Frequent | 103 | 0.010 | 0.008 | +0.001 [−0.009, +0.012] | n.s. |
| removed | Infrequent | 496 | 0.059 | 0.037 | **+0.022 [+0.012, +0.032]** | 38% |
| removed | Occasional | 339 | 0.044 | 0.033 | +0.011 [+0.000, +0.021] | 24% |
| removed | Frequent | 105 | 0.034 | 0.022 | +0.012 [−0.002, +0.027] | n.s. |

Users = users who watched something in both runs. Rating uplift is in rating points (1–5 scale).

**Table 2. Watch rate: ratings shown vs hidden** (same pages)

| Activity description | Group | Shown | Hidden | Shown − hidden [95% CI] |
|---|---|---:|---:|---|
| included | Infrequent | 0.210 | 0.219 | −0.009 [−0.018, −0.001] |
| included | Occasional | 0.371 | 0.373 | −0.003 [−0.020, +0.014] |
| included | Frequent | 0.728 | 0.780 | −0.052 [−0.098, −0.006] |
| removed | Infrequent | 0.568 | 0.602 | −0.034 [−0.054, −0.013] |
| removed | Occasional | 0.628 | 0.636 | −0.009 [−0.029, +0.011] |
| removed | Frequent | 0.690 | 0.701 | −0.011 [−0.051, +0.029] |

**Takeaways**

- Showing ratings makes simulated users pick higher-rated movies, but hiding them removes only about a quarter to a third of that preference. The LLM likely still recognizes well-known, acclaimed titles from the title alone.
- Hiding ratings changes how much users watch only slightly. If anything, users watch a little more when ratings are hidden.
- Frequent users show almost no rating preference either way, because they watch most of what they see.

## 2. Swapping activity descriptions (R3, R4)

**Table 3. Watch rate with original vs swapped activity description** (Agent4Rec, same pages)

| Real group | Description given | Original | Swapped | Swapped − original [95% CI] |
|---|---|---:|---:|---|
| Infrequent (539) | Frequent, ratings shown (R3) | 0.210 | **0.823** | +0.613 [+0.593, +0.634] |
| Infrequent (539) | Frequent, ratings hidden (R4) | 0.219 | **0.809** | +0.590 [+0.569, +0.611] |
| Occasional (352), control | unchanged, ratings shown (R3) | 0.369 | 0.370 | +0.000 [−0.015, +0.016] |
| Occasional (352), control | unchanged, ratings hidden (R4) | 0.372 | 0.361 | −0.011 [−0.027, +0.006] |
| Frequent (109) | Infrequent, ratings shown (R3) | 0.722 | **0.188** | −0.533 [−0.599, −0.468] |
| Frequent (109) | Infrequent, ratings hidden (R4) | 0.785 | **0.202** | −0.583 [−0.642, −0.524] |

For comparison, with the activity description removed (R2), watch rates are 0.60 / 0.64 / 0.70 for the three groups.

**Takeaways**

- How much a simulated user watches is set almost entirely by the activity sentence in the prompt, not by the user's real history. Swapping the sentence moves each group almost exactly to the other group's level.
- The unchanged Occasional group is a clean negative control: no change in either run.
- The swap also moves the rating preference: real Frequent users given the Infrequent description start favoring highly rated movies (rating uplift 0.005 → 0.126 with ratings shown). Selective "infrequent" users are the ones who pick by rating.

## 3. Position bias with randomized order (P1–P3, S1–S3)

In the vanilla runs, items are shown in recommender order, so the top position also holds the most relevant item. In P and S runs, the same four items on each page are shown in a random order (3 seeds), which separates the effect of position from relevance.

**Table 4. Selection rate by displayed position**

| Simulator | Order | Pos 1 | Pos 2 | Pos 3 | Pos 4 | P1/P4 [95% CI] | Adjusted OR per step [95% CI] |
|---|---|---:|---:|---:|---:|---|---|
| Agent4Rec | vanilla (recommender rank) | 44.1% | 39.8% | 35.6% | 33.0% | 1.335 [1.264, 1.414] | 0.863 [0.838, 0.889] |
| Agent4Rec | **random, 3 seeds pooled** | 42.8% | 40.2% | 36.4% | 34.1% | **1.255 [1.210, 1.304]** | **0.879 [0.863, 0.896]** |
| SimUSER | vanilla (recommender rank) | 70.3% | 63.6% | 60.9% | 63.8% | 1.102 [1.073, 1.132] | 0.918 [0.895, 0.942] |
| SimUSER | **random, 3 seeds pooled** | 70.0% | 63.7% | 62.1% | 64.6% | **1.085 [1.068, 1.101]** | **0.922 [0.908, 0.935]** |

Adjusted OR per step = the odds of selection each time an item moves one position down. It controls for item popularity, whether the item is a held-out positive, page number, and seed. A value below 1 means a front-position bias.

**Table 5. Displayed position vs original recommender rank** (randomized runs, 3 seeds pooled)

| Simulator | Effect of displayed position (P1/P4) | Effect of original rank (R1/R4) |
|---|---|---|
| Agent4Rec | **1.255 [1.210, 1.304]** | 1.082 [1.034, 1.133] |
| SimUSER | **1.085 [1.069, 1.102]** | 1.016 [0.991, 1.042] (n.s.) |

**Table 6. Each seed separately**

| Simulator | Seed | P1/P4 [95% CI] | Adjusted OR per step [95% CI] |
|---|---|---|---|
| Agent4Rec | 20261121 | 1.282 [1.210, 1.360] | 0.872 [0.846, 0.899] |
| Agent4Rec | 20261122 | 1.230 [1.164, 1.303] | 0.894 [0.867, 0.921] |
| Agent4Rec | 20261123 | 1.256 [1.184, 1.338] | 0.871 [0.844, 0.899] |
| SimUSER | 20261121 | 1.096 [1.068, 1.125] | 0.912 [0.889, 0.934] |
| SimUSER | 20261122 | 1.076 [1.049, 1.104] | 0.929 [0.907, 0.952] |
| SimUSER | 20261123 | 1.083 [1.056, 1.112] | 0.924 [0.902, 0.947] |

**Takeaways**

- Position bias is **causal** in both simulators. All three seeds agree and every interval excludes "no effect".
- In Agent4Rec, the first item is chosen 26% more often than the fourth, and selection falls steadily with position. Most of the vanilla front-position advantage (1.335) remains after shuffling (1.255), so it was mostly position, not relevance.
- In SimUSER the effect is smaller (+9%) and mostly a first-position effect: positions 2–4 are similar.
- Once order is randomized, the recommender's original ranking barely predicts what the simulated user picks (Agent4Rec 1.08, SimUSER not significant). In other words, the simulators react to where an item is shown much more than to how relevant it is.

## Caveats

- These are simulator outcomes with one LLM (gpt-6-luna) at temperature 0. They say nothing directly about human users.
- Rating and activity results are for Agent4Rec only. Conformity was not manipulated.
- Rating uplift only counts users who watched something in both runs, so the user set can differ slightly between rows.
- Paired rating and activity intervals are 95% t-intervals. Position intervals are user-cluster bootstrap intervals (5,000 draws) or cluster-robust logistic intervals. No multiple-comparison correction.
- Pooled position results reuse the same 1,000 users across three seeds. The bootstrap resamples each user's full three-seed record.
- The vanilla position baseline comes from Moonsoo's archived `analysis/position_bias/summary.json`. The raw vanilla SimUSER run is not available locally, so that baseline could not be re-audited here.
- Full-session results, not shown above, include different numbers of pages per user. The paired "common prefix" results above compare identical pages only.

## Folder layout

- [rating_ablation/REPORT.md](rating_ablation/REPORT.md): Tables 1-2, paired comparison and summary CSVs, completed handoff, and page-wise figure.
- [activity_crossover/REPORT.md](activity_crossover/REPORT.md): Table 3, paired comparison and summary CSVs, completed handoff, and page-wise figure.
- [position_bias/REPORT.md](position_bias/REPORT.md): Tables 4-6, all per-seed and pooled effects; [final table](position_bias/final_table.md).
- `position_bias/s2026112{1,2,3}/`: per-seed aggregate position rates and statistical summaries, with no exposure records.
- [position_bias/original_rank_effect.json](position_bias/original_rank_effect.json): supplementary displayed-position versus original-rank effects for Table 5.
- [final_analysis_validation.json](final_analysis_validation.json): audit gates, raw-output integrity checks, baseline provenance, and analysis settings.
- [sanitization_manifest.json](sanitization_manifest.json): local privacy and English-only cleanup receipt; deleted local files were never included in this publication.

The local source branch is `jinyi/bias-runs-20261124` in the separate
`llm-rec-simulator-bias` repository. Final offline-analysis code is recorded in
local source commit `95e1fd2d8076b282524d356f2ed9f3a25d2ef2d5`; this results-only
publication does not push that source repository. The cached-ranking loader
reproduces the reference impressions with zero mismatches.
