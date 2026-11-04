# n1000 full condition — offline analysis

Run: `20261103_193255_9637d5eded` · status: **partial** · completed cases: 2979 / 3000 · failure rows: 21

Primary metrics recomputed from actions.jsonl with the repo's definitions (all held-out items are positives). CIs: user-cluster percentile bootstrap, 2,000 resamples. Cases missing because of failures are excluded per model, and the backbone is evaluated on the same cases.

## 1. Effect vs backbone (same cases)

| Model | Policy | n | Recall@10 | NDCG@10 | ΔRecall (95% CI) | ΔNDCG (95% CI) |
|---|---|---:|---:|---:|---|---|
| MF | click_only | 993 | 0.1718 (base 0.1742) | 0.2794 (base 0.2819) | -0.0025 [-0.0095, +0.0044] (-1.4%) | -0.0025 [-0.0088, +0.0036] (-0.9%) |
| MF | converted_then_original | 993 | 0.1760 (base 0.1742) | 0.2844 (base 0.2819) | +0.0017 [+0.0004, +0.0032] (+1.0%) | +0.0025 [-0.0032, +0.0081] (+0.9%) |
| MF | three_tier | 993 | 0.1718 (base 0.1742) | 0.2800 (base 0.2819) | -0.0025 [-0.0097, +0.0042] (-1.4%) | -0.0020 [-0.0098, +0.0059] (-0.7%) |
| LightGCN | click_only | 991 | 0.2003 (base 0.2045) | 0.3321 (base 0.3431) | -0.0042 [-0.0101, +0.0017] (-2.0%) | -0.0110 [-0.0174, -0.0042] (-3.2%) |
| LightGCN | converted_then_original | 991 | 0.2048 (base 0.2045) | 0.3382 (base 0.3431) | +0.0003 [-0.0013, +0.0020] (+0.1%) | -0.0049 [-0.0099, +0.0003] (-1.4%) |
| LightGCN | three_tier | 991 | 0.2000 (base 0.2045) | 0.3275 (base 0.3431) | -0.0045 [-0.0106, +0.0015] (-2.2%) | -0.0156 [-0.0232, -0.0077] (-4.5%) |
| MultiVAE | click_only | 995 | 0.1983 (base 0.2051) | 0.3234 (base 0.3307) | -0.0067 [-0.0124, -0.0007] (-3.3%) | -0.0074 [-0.0137, -0.0011] (-2.2%) |
| MultiVAE | converted_then_original | 995 | 0.2052 (base 0.2051) | 0.3225 (base 0.3307) | +0.0002 [-0.0007, +0.0010] (+0.1%) | -0.0083 [-0.0132, -0.0034] (-2.5%) |
| MultiVAE | three_tier | 995 | 0.1984 (base 0.2051) | 0.3156 (base 0.3307) | -0.0067 [-0.0125, -0.0010] (-3.2%) | -0.0151 [-0.0225, -0.0077] (-4.6%) |

Pooled over backbones (each user's mean ΔNDCG across available backbones):

- **click_only**: ΔNDCG@10 -0.0068 [-0.0119, -0.0023]
- **converted_then_original**: ΔNDCG@10 -0.0036 [-0.0073, -0.0001]
- **three_tier**: ΔNDCG@10 -0.0109 [-0.0164, -0.0048]

## 2. Why the conversion policy moves NDCG

| Model | P(converted is positive) | P(backbone rank-1 is positive) | conv. original rank: median / share >10 | cases DCG up / down / same | P(pos) clicked / unclicked / slate |
|---|---:|---:|---|---|---|
| MF | 0.321 | 0.338 | 5 / 0.16 | 224 / 360 / 360 | 0.230 / 0.162 / 0.192 |
| LightGCN | 0.374 | 0.438 | 4 / 0.12 | 212 / 353 / 381 | 0.266 / 0.184 / 0.218 |
| MultiVAE | 0.347 | 0.419 | 4 / 0.16 | 224 / 396 / 339 | 0.259 / 0.174 / 0.211 |
| all | 0.347 | 0.398 | 4 / 0.15 | 660 / 1109 / 1080 | 0.251 / 0.173 / 0.207 |

Selection bias: mean aggregate rating of converted items 4.25 vs held-out positives 3.80 vs whole slate 3.79; train popularity (1,000-user panel) 295 vs 216 vs 199.

Backbone P(positive) by original rank: 1:0.39, 2:0.32, 3:0.29, 4:0.26, 5:0.25, 6:0.23, 7:0.21, 8:0.22, 9:0.20, 10:0.19, 11:0.19, 12:0.18, 13:0.18, 14:0.17, 15:0.16, 16:0.16, 17:0.15, 18:0.13, 19:0.15, 20:0.13

## 3. Behavior

Mean clicks 9.02 (median 9); not_ready rate 0.044; zero-click cases 3.

Alignment labels: strong 61.1%, none 25.8%, adjacent 13.1%

Conversion-stage outcomes: insufficient 56.9%, confirmed 42.7%, contradicted 0.4%

| Trait level | Activity: mean clicks | Diversity: adjacent share of clicks | Conformity: mean |pred − avg rating| |
|---|---:|---:|---:|
| 1 | 8.861 (n=1443) | 0.002 (n=489) | 0.390 (n=6978) |
| 2 | 8.996 (n=1091) | 0.003 (n=1063) | 0.409 (n=14325) |
| 3 | 9.589 (n=445) | 0.003 (n=1424) | 0.420 (n=5565) |

Expected directions: clicks rise with Activity; adjacent share rises with Diversity; |pred − avg| rises with Conformity (level 1 follower → level 3 independent critic). Descriptive only; trait groups differ in histories and slates.

## 4. Exploratory alternative policies (split-half, not pre-registered)

Score = −log(original rank) + w_click·clicked + w_conv·converted + w_strong·strong − w_none·none, grid of 192 weightings.
Best weights on half A (500 users): (0.25, 1, 0, 0.5); ΔNDCG@10 on half A +0.0037, **on held-out half B (500 users) +0.0095**. (converted_then_original on half B: -0.0020)

Use half-B numbers only as a hint; any policy carried into the paper must be fixed on a validation split, not on test labels.

## 5. Failures

21 failure rows (historical rows stay even after a case is recovered): candidate_assessments[*].evidence must be a nonempty string ×21
By model: LightGCN 9, MF 7, MultiVAE 5

Cases without an action record: 21 (e.g. [('MF', 754), ('MF', 1433), ('MF', 1466), ('MF', 2085), ('MF', 3903), ('MF', 4748), ('MF', 5218), ('LightGCN', 77)])

