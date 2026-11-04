# n1000 full condition — offline analysis

Run: `20261103_193255_9637d5eded` · status: **complete** · completed cases: 3000 / 3000 · failure rows: 21

Primary metrics recomputed from actions.jsonl with the repo's definitions (all held-out items are positives). CIs: user-cluster percentile bootstrap, 2,000 resamples. Cases missing because of failures are excluded per model, and the backbone is evaluated on the same cases.

## 1. Effect vs backbone (same cases)

| Model | Policy | n | Recall@10 | NDCG@10 | ΔRecall (95% CI) | ΔNDCG (95% CI) |
|---|---|---:|---:|---:|---|---|
| MF | click_only | 1000 | 0.1714 (base 0.1740) | 0.2788 (base 0.2815) | -0.0026 [-0.0092, +0.0045] (-1.5%) | -0.0026 [-0.0089, +0.0042] (-0.9%) |
| MF | converted_then_original | 1000 | 0.1758 (base 0.1740) | 0.2845 (base 0.2815) | +0.0018 [+0.0004, +0.0032] (+1.0%) | +0.0030 [-0.0025, +0.0084] (+1.1%) |
| MF | three_tier | 1000 | 0.1714 (base 0.1740) | 0.2798 (base 0.2815) | -0.0026 [-0.0091, +0.0045] (-1.5%) | -0.0017 [-0.0096, +0.0062] (-0.6%) |
| LightGCN | click_only | 1000 | 0.2013 (base 0.2052) | 0.3335 (base 0.3442) | -0.0039 [-0.0097, +0.0017] (-1.9%) | -0.0107 [-0.0180, -0.0042] (-3.1%) |
| LightGCN | converted_then_original | 1000 | 0.2055 (base 0.2052) | 0.3391 (base 0.3442) | +0.0003 [-0.0012, +0.0020] (+0.1%) | -0.0051 [-0.0100, +0.0002] (-1.5%) |
| LightGCN | three_tier | 1000 | 0.2010 (base 0.2052) | 0.3288 (base 0.3442) | -0.0042 [-0.0101, +0.0015] (-2.0%) | -0.0154 [-0.0230, -0.0076] (-4.5%) |
| MultiVAE | click_only | 1000 | 0.1982 (base 0.2048) | 0.3230 (base 0.3301) | -0.0066 [-0.0128, -0.0006] (-3.2%) | -0.0071 [-0.0134, -0.0010] (-2.2%) |
| MultiVAE | converted_then_original | 1000 | 0.2050 (base 0.2048) | 0.3217 (base 0.3301) | +0.0002 [-0.0007, +0.0010] (+0.1%) | -0.0084 [-0.0134, -0.0034] (-2.5%) |
| MultiVAE | three_tier | 1000 | 0.1983 (base 0.2048) | 0.3152 (base 0.3301) | -0.0065 [-0.0122, -0.0005] (-3.2%) | -0.0149 [-0.0228, -0.0075] (-4.5%) |

Pooled over backbones (each user's mean ΔNDCG across available backbones):

- **click_only**: ΔNDCG@10 -0.0068 [-0.0111, -0.0022]
- **converted_then_original**: ΔNDCG@10 -0.0035 [-0.0070, +0.0001]
- **three_tier**: ΔNDCG@10 -0.0107 [-0.0167, -0.0047]

## 2. Why the conversion policy moves NDCG

| Model | P(converted is positive) | P(backbone rank-1 is positive) | conv. original rank: median / share >10 | cases DCG up / down / same | P(pos) clicked / unclicked / slate |
|---|---:|---:|---|---|---|
| MF | 0.323 | 0.336 | 5 / 0.16 | 228 / 362 / 361 | 0.229 / 0.162 / 0.192 |
| LightGCN | 0.374 | 0.439 | 4 / 0.12 | 213 / 357 / 383 | 0.267 / 0.184 / 0.218 |
| MultiVAE | 0.346 | 0.419 | 4 / 0.16 | 224 / 398 / 340 | 0.259 / 0.173 / 0.211 |
| all | 0.348 | 0.398 | 4 / 0.15 | 665 / 1117 / 1084 | 0.252 / 0.173 / 0.207 |

Selection bias: mean aggregate rating of converted items 4.25 vs held-out positives 3.80 vs whole slate 3.79; train popularity (1,000-user panel) 295 vs 216 vs 199.

Backbone P(positive) by original rank: 1:0.39, 2:0.32, 3:0.29, 4:0.26, 5:0.24, 6:0.23, 7:0.21, 8:0.22, 9:0.20, 10:0.19, 11:0.19, 12:0.18, 13:0.17, 14:0.17, 15:0.16, 16:0.16, 17:0.15, 18:0.13, 19:0.15, 20:0.13

## 3. Behavior

Mean clicks 9.02 (median 9); not_ready rate 0.045; zero-click cases 3.

Alignment labels: strong 61.1%, none 25.9%, adjacent 13.1%

Conversion-stage outcomes: insufficient 56.9%, confirmed 42.7%, contradicted 0.4%

| Trait level | Activity: mean clicks | Diversity: adjacent share of clicks | Conformity: mean |pred − avg rating| |
|---|---:|---:|---:|
| 1 | 8.855 (n=1452) | 0.002 (n=494) | 0.390 (n=6994) |
| 2 | 8.996 (n=1101) | 0.003 (n=1067) | 0.409 (n=14461) |
| 3 | 9.597 (n=447) | 0.003 (n=1436) | 0.420 (n=5598) |

Expected directions: clicks rise with Activity; adjacent share rises with Diversity; |pred − avg| rises with Conformity (level 1 follower → level 3 independent critic). Descriptive only; trait groups differ in histories and slates.

## 4. Exploratory alternative policies (split-half, not pre-registered)

Score = −log(original rank) + w_click·clicked + w_conv·converted + w_strong·strong − w_none·none, grid of 192 weightings.
Best weights on half A (500 users): (0.25, 1, 0, 0.5); ΔNDCG@10 on half A +0.0037, **on held-out half B (500 users) +0.0095**. (converted_then_original on half B: -0.0021)

Use half-B numbers only as a hint; any policy carried into the paper must be fixed on a validation split, not on test labels.

## 5. Failures

21 failure rows (historical rows stay even after a case is recovered): candidate_assessments[*].evidence must be a nonempty string ×21
By model: LightGCN 9, MF 7, MultiVAE 5

Cases without an action record: 0

