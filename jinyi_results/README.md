Code for these results: branch `jinyi` (commit 71186c5). Raw artifacts are stored off GitHub.

# Jinyi's experiment results — agent reranking (MovieLens-1M)

Last updated: 2026-11-04 (PT). Code includes handoff commit `ec7fac9` plus
`56ba845`, `f217db1`, `0765faf`, and `71186c5` (see Notes). This directory contains
reports and aggregate numbers only; raw run directories are in the off-repo archive.

Local storage cleanup (2026-11-04): all eight API transcript files, duplicate
profile checkpoints, and Python caches were removed from the local raw-result
directory. Reports, metrics, actions, and merged profiles were preserved unchanged.
The removed files were never included in this branch. Raw API audit or replay now
requires a separately retained complete copy; historical checksum manifests may
still list the removed files.

## Status

| Experiment | Users | LLM | Status | Recorded cost |
|---|---:|---|---|---:|
| 1,000-user handoff run, 4 conditions | 1,000 | gpt-4o-mini | **complete** — 3,000 / 3,000 cases per condition, 0 missing | $22.17 total (profiles $0.33; full $5.85, no_demographics $5.83, no_persona $5.70, no_interaction_history $4.42) |
| v3 debiased protocol (full input) | 1,000 | gpt-4o-mini | complete (3,000 / 3,000) — see the v3 section below | $6.83 incl. profiles + pilot |
| 50-user LLM comparison | 50 | gpt-4o-mini vs gpt-5-mini | complete (150 / 150 each) | $0.30 / $0.90 |
| 30-user pilot | 30 | gpt-4o-mini | complete (90 / 90) | $0.18 |

Costs are token-rate estimates, not the proxy bill.

## Main results: 1,000 users

Prompt `behavior-align-rating-social-traits`, profile protocol `separated`, gpt-4o-mini,
temperature 0, Top-20 candidates, Top-10 evaluation, every held-out interaction counts as a
positive. Percentages are relative change vs. each backbone. Bold = best per column.

**Table 1. Ablation of agent input** (policy: click + conversion = `converted_then_original`)

| | MF | | LightGCN | | MultiVAE | |
|---|---:|---:|---:|---:|---:|---:|
| | Recall@10 | NDCG@10 | Recall@10 | NDCG@10 | Recall@10 | NDCG@10 |
| Backbone | 0.1740 | 0.2815 | 0.2052 | **0.3442** | 0.2048 | **0.3301** |
| AgentRerank (full) | **0.1758 (+1.01%)** | 0.2845 (+1.07%) | 0.2055 (+0.15%) | 0.3391 (-1.47%) | **0.2050 (+0.08%)** | 0.3217 (-2.53%) |
| w/o demographics | 0.1754 (+0.80%) | 0.2831 (+0.58%) | 0.2055 (+0.14%) | 0.3392 (-1.46%) | 0.2049 (+0.06%) | 0.3229 (-2.18%) |
| w/o persona | 0.1755 (+0.84%) | **0.2856 (+1.46%)** | 0.2054 (+0.10%) | 0.3380 (-1.81%) | 0.2048 (-0.03%) | 0.3235 (-1.99%) |
| w/o interaction history | 0.1743 (+0.19%) | 0.2825 (+0.35%) | **0.2059 (+0.35%)** | 0.3383 (-1.71%) | 0.2048 (+0.01%) | 0.3234 (-2.02%) |

**Table 2. Funnel stages, full input**

| | MF | | LightGCN | | MultiVAE | |
|---|---:|---:|---:|---:|---:|---:|
| | Recall@10 | NDCG@10 | Recall@10 | NDCG@10 | Recall@10 | NDCG@10 |
| Backbone | 0.1740 | 0.2815 | 0.2052 | 0.3442 | 0.2048 | 0.3301 |
| AgentRerank (click) | 0.1714 (-1.51%) | 0.2788 (-0.94%) | 0.2013 (-1.88%) | 0.3335 (-3.11%) | 0.1982 (-3.21%) | 0.3230 (-2.16%) |
| AgentRerank (click + conversion) | 0.1758 (+1.01%) | 0.2845 (+1.07%) | 0.2055 (+0.15%) | 0.3391 (-1.47%) | 0.2050 (+0.08%) | 0.3217 (-2.53%) |
| AgentRerank (three-tier) | 0.1714 (-1.50%) | 0.2798 (-0.60%) | 0.2010 (-2.05%) | 0.3288 (-4.46%) | 0.1983 (-3.17%) | 0.3152 (-4.53%) |

`click` = all clicked items first (`click_only`); `click + conversion` = the single converted item
first, everything else in backbone order; `three-tier` = converted, then clicked, then unclicked.
Within each tier the backbone order is kept.

**Table 3. NDCG@10 change pooled over the three backbones** (user-clustered bootstrap, 2,000 resamples, 95% CI)

| Condition | click | click + conversion | three-tier |
|---|---|---|---|
| full | −0.0068 [−0.0115, −0.0020] | −0.0035 [−0.0072, +0.0001] | −0.0107 [−0.0164, −0.0051] |
| w/o demographics | −0.0077 [−0.0125, −0.0029] | −0.0035 [−0.0072, +0.0000] | −0.0115 [−0.0174, −0.0060] |
| w/o persona | −0.0027 [−0.0067, +0.0015] | −0.0029 [−0.0067, +0.0010] | −0.0073 [−0.0126, −0.0016] |
| w/o interaction history | −0.0113 [−0.0165, −0.0059] | −0.0039 [−0.0073, −0.0004] | −0.0153 [−0.0215, −0.0092] |

Per-model CIs for every condition and stage: [`n1000_v2/analysis.md`](n1000_v2/analysis.md).
Diagnostics for `full`: [`n1000_v2/analysis_full/report_full.md`](n1000_v2/analysis_full/report_full.md).

<details>
<summary>Table 4. Handoff summary format (all conditions, models, stages)</summary>

"Failures" counts historical failure rows; all of them were later recovered, so 0 cases are missing.
Recorded cost is per backbone and is shared by the four stages (one LLM run per case).

| Condition | Model | Stage | Cases | Failures | Recorded cost | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | MF | sampled_baseline | 1000 | 7 | $1.96 | 0.1740 | 0.2815 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | MF | click_only | 1000 | 7 | $1.96 | 0.1714 | 0.2788 | -0.0026 (-1.51%) | -0.0026 (-0.94%) |
| full | MF | converted_then_original | 1000 | 7 | $1.96 | 0.1758 | 0.2845 | +0.0018 (+1.01%) | +0.0030 (+1.07%) |
| full | MF | three_tier | 1000 | 7 | $1.96 | 0.1714 | 0.2798 | -0.0026 (-1.50%) | -0.0017 (-0.60%) |
| full | LightGCN | sampled_baseline | 1000 | 9 | $1.94 | 0.2052 | 0.3442 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | LightGCN | click_only | 1000 | 9 | $1.94 | 0.2013 | 0.3335 | -0.0039 (-1.88%) | -0.0107 (-3.11%) |
| full | LightGCN | converted_then_original | 1000 | 9 | $1.94 | 0.2055 | 0.3391 | +0.0003 (+0.15%) | -0.0051 (-1.47%) |
| full | LightGCN | three_tier | 1000 | 9 | $1.94 | 0.2010 | 0.3288 | -0.0042 (-2.05%) | -0.0154 (-4.46%) |
| full | MultiVAE | sampled_baseline | 1000 | 5 | $1.95 | 0.2048 | 0.3301 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | MultiVAE | click_only | 1000 | 5 | $1.95 | 0.1982 | 0.3230 | -0.0066 (-3.21%) | -0.0071 (-2.16%) |
| full | MultiVAE | converted_then_original | 1000 | 5 | $1.95 | 0.2050 | 0.3217 | +0.0002 (+0.08%) | -0.0084 (-2.53%) |
| full | MultiVAE | three_tier | 1000 | 5 | $1.95 | 0.1983 | 0.3152 | -0.0065 (-3.17%) | -0.0149 (-4.53%) |
| no_demographics | MF | sampled_baseline | 1000 | 0 | $1.94 | 0.1740 | 0.2815 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_demographics | MF | click_only | 1000 | 0 | $1.94 | 0.1701 | 0.2783 | -0.0039 (-2.26%) | -0.0031 (-1.12%) |
| no_demographics | MF | converted_then_original | 1000 | 0 | $1.94 | 0.1754 | 0.2831 | +0.0014 (+0.80%) | +0.0016 (+0.58%) |
| no_demographics | MF | three_tier | 1000 | 0 | $1.94 | 0.1703 | 0.2782 | -0.0037 (-2.15%) | -0.0033 (-1.17%) |
| no_demographics | LightGCN | sampled_baseline | 1000 | 0 | $1.94 | 0.2052 | 0.3442 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_demographics | LightGCN | click_only | 1000 | 0 | $1.94 | 0.2000 | 0.3335 | -0.0052 (-2.56%) | -0.0107 (-3.11%) |
| no_demographics | LightGCN | converted_then_original | 1000 | 0 | $1.94 | 0.2055 | 0.3392 | +0.0003 (+0.14%) | -0.0050 (-1.46%) |
| no_demographics | LightGCN | three_tier | 1000 | 0 | $1.94 | 0.1999 | 0.3282 | -0.0053 (-2.57%) | -0.0160 (-4.64%) |
| no_demographics | MultiVAE | sampled_baseline | 1000 | 0 | $1.94 | 0.2048 | 0.3301 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_demographics | MultiVAE | click_only | 1000 | 0 | $1.94 | 0.1974 | 0.3208 | -0.0074 (-3.63%) | -0.0093 (-2.83%) |
| no_demographics | MultiVAE | converted_then_original | 1000 | 0 | $1.94 | 0.2049 | 0.3229 | +0.0001 (+0.06%) | -0.0072 (-2.18%) |
| no_demographics | MultiVAE | three_tier | 1000 | 0 | $1.94 | 0.1977 | 0.3147 | -0.0072 (-3.49%) | -0.0154 (-4.66%) |
| no_persona | MF | sampled_baseline | 1000 | 0 | $1.91 | 0.1740 | 0.2815 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_persona | MF | click_only | 1000 | 0 | $1.91 | 0.1721 | 0.2826 | -0.0019 (-1.12%) | +0.0011 (+0.40%) |
| no_persona | MF | converted_then_original | 1000 | 0 | $1.91 | 0.1755 | 0.2856 | +0.0015 (+0.84%) | +0.0041 (+1.46%) |
| no_persona | MF | three_tier | 1000 | 0 | $1.91 | 0.1723 | 0.2833 | -0.0017 (-0.96%) | +0.0018 (+0.64%) |
| no_persona | LightGCN | sampled_baseline | 1000 | 0 | $1.89 | 0.2052 | 0.3442 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_persona | LightGCN | click_only | 1000 | 0 | $1.89 | 0.2011 | 0.3367 | -0.0042 (-2.02%) | -0.0075 (-2.18%) |
| no_persona | LightGCN | converted_then_original | 1000 | 0 | $1.89 | 0.2054 | 0.3380 | +0.0002 (+0.10%) | -0.0062 (-1.81%) |
| no_persona | LightGCN | three_tier | 1000 | 0 | $1.89 | 0.2007 | 0.3304 | -0.0045 (-2.18%) | -0.0138 (-4.01%) |
| no_persona | MultiVAE | sampled_baseline | 1000 | 0 | $1.89 | 0.2048 | 0.3301 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_persona | MultiVAE | click_only | 1000 | 0 | $1.89 | 0.1994 | 0.3283 | -0.0054 (-2.64%) | -0.0018 (-0.54%) |
| no_persona | MultiVAE | converted_then_original | 1000 | 0 | $1.89 | 0.2048 | 0.3235 | -0.0001 (-0.03%) | -0.0066 (-1.99%) |
| no_persona | MultiVAE | three_tier | 1000 | 0 | $1.89 | 0.1993 | 0.3203 | -0.0055 (-2.67%) | -0.0098 (-2.96%) |
| no_interaction_history | MF | sampled_baseline | 1000 | 0 | $1.47 | 0.1740 | 0.2815 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_interaction_history | MF | click_only | 1000 | 0 | $1.47 | 0.1708 | 0.2780 | -0.0032 (-1.86%) | -0.0034 (-1.22%) |
| no_interaction_history | MF | converted_then_original | 1000 | 0 | $1.47 | 0.1743 | 0.2825 | +0.0003 (+0.19%) | +0.0010 (+0.35%) |
| no_interaction_history | MF | three_tier | 1000 | 0 | $1.47 | 0.1705 | 0.2764 | -0.0035 (-1.99%) | -0.0050 (-1.79%) |
| no_interaction_history | LightGCN | sampled_baseline | 1000 | 0 | $1.47 | 0.2052 | 0.3442 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_interaction_history | LightGCN | click_only | 1000 | 0 | $1.47 | 0.1976 | 0.3297 | -0.0076 (-3.72%) | -0.0145 (-4.21%) |
| no_interaction_history | LightGCN | converted_then_original | 1000 | 0 | $1.47 | 0.2059 | 0.3383 | +0.0007 (+0.35%) | -0.0059 (-1.71%) |
| no_interaction_history | LightGCN | three_tier | 1000 | 0 | $1.47 | 0.1976 | 0.3233 | -0.0076 (-3.70%) | -0.0209 (-6.07%) |
| no_interaction_history | MultiVAE | sampled_baseline | 1000 | 0 | $1.47 | 0.2048 | 0.3301 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| no_interaction_history | MultiVAE | click_only | 1000 | 0 | $1.47 | 0.1953 | 0.3142 | -0.0095 (-4.63%) | -0.0159 (-4.82%) |
| no_interaction_history | MultiVAE | converted_then_original | 1000 | 0 | $1.47 | 0.2048 | 0.3234 | +0.0000 (+0.01%) | -0.0067 (-2.02%) |
| no_interaction_history | MultiVAE | three_tier | 1000 | 0 | $1.47 | 0.1956 | 0.3101 | -0.0092 (-4.50%) | -0.0200 (-6.06%) |

</details>

## v3 debiased protocol (1,000 users, full input)

Run `20261104_110320_6d635fc772` (raw run directory, not in repo; see the off-repo archive),
code commit `71186c5`, prompt
`behavior-v3-debiased`. Same 1,000 users, Top-20 slates, backbones, 10-movie history sample,
gpt-4o-mini and temperature 0 as the reference `full` run above. The prompt was frozen after a
100-user pilot that checked only format and bias (no accuracy metrics were computed on the pilot).
3,000 / 3,000 cases, 0 missing. The 802 historical failure rows are cases interrupted by safety
stops (proxy HTTP 429 at the per-user limit of 600 requests per window, and one timeout); all of
them were re-run. Recorded cost: $5.88 for the behavior run, $6.83 including profiles and pilot.

All of these changes were applied together, so the effects cannot be attributed to single
changes:

| Area | Reference | v3 |
|---|---|---|
| Aggregate rating (`average_rating`) | shown at both stages | removed |
| Candidate order | backbone rank order | deterministic shuffle per (seed, model, user), stated as random |
| History | 10 movies, no user rating | same 10 movies + the user's own 1–5 rating |
| Social traits | Activity, Conformity, Diversity | Conformity removed |
| Profiles | like = rating ≥ 3 | like = 4–5, neutral = 3, dislike = 1–2; no contradictory patterns (regenerated) |
| Click output | alignment: strong / adjacent / none | interest 1–5 (click only if ≥ 3) |
| Conversion output | predicted 1–5 rating ("important comparative evidence") | watch_likelihood 1–5 ("not how good or well-known the movie is") |
| Anti-popularity instruction | none | both stages |

**Table 5. Reference vs v3, click + conversion, relative NDCG@10 change vs backbone**

| Positives | Protocol | MF | LightGCN | MultiVAE | Pooled ΔNDCG@10 [95% CI] |
|---|---|---:|---:|---:|---|
| all held-out | reference | +1.07% | −1.47% | −2.53% | −0.0035 [−0.0070, +0.0002] |
| all held-out | **v3** | **−4.32%** | **−7.18%** | **−7.56%** | **−0.0206 [−0.0243, −0.0167]** |
| rating ≥ 3 | reference | +2.33% | −1.12% | −2.37% | −0.0017 [−0.0053, +0.0022] |
| rating ≥ 3 | **v3** | **−4.81%** | **−7.70%** | **−8.26%** | **−0.0216 [−0.0253, −0.0174]** |
| rating ≥ 4 | reference | +4.53% | +0.66% | −1.13% | +0.0031 [−0.0011, +0.0078] |
| rating ≥ 4 | **v3** | **−4.62%** | **−9.02%** | **−9.33%** | **−0.0217 [−0.0258, −0.0173]** |

Paired v3 − reference ΔNDCG@10 on the same cases: −0.0171 [−0.0217, −0.0127] (all held-out),
−0.0199 [−0.0243, −0.0152] (≥ 3), −0.0248 [−0.0299, −0.0198] (≥ 4).

**Table 6. All policies, positives = all held-out**

| Policy | Protocol | MF | LightGCN | MultiVAE | Pooled ΔNDCG@10 [95% CI] |
|---|---|---:|---:|---:|---|
| click | reference | −0.94% | −3.11% | −2.16% | −0.0068 [−0.0113, −0.0022] |
| click | v3 | −2.75% | −8.84% | −8.47% | −0.0220 [−0.0275, −0.0167] |
| click + conversion | reference | +1.07% | −1.47% | −2.53% | −0.0035 [−0.0070, +0.0002] |
| click + conversion | v3 | −4.32% | −7.18% | −7.56% | −0.0206 [−0.0243, −0.0167] |
| three-tier | reference | −0.60% | −4.46% | −4.53% | −0.0107 [−0.0163, −0.0048] |
| three-tier | v3 | −6.63% | −14.19% | −14.55% | −0.0385 [−0.0447, −0.0323] |

**Table 7. Bias diagnostics (positives = all held-out)**

| | Reference | v3 | For comparison |
|---|---:|---:|---|
| Mean aggregate rating of converted items | 4.25 | **3.82** | held-out positives 3.80 |
| Mean train popularity of converted items | 295 | **208** | held-out positives 216 |
| Conversion = slate's top-rated movie | 42.6% | **6.1%** | random pick ≈ 5% |
| Converted item is a positive | 34.8% | **23.7%** | slate base rate 20.7% |
| Backbone rank-1 item is a positive | 39.8% | 38.9% | |
| Mean clicks per slate | 9.02 | 10.65 | |
| not_ready rate | 4.5% | 0.3% | |

v3 conversions are almost uniform over the original backbone rank: 7% at rank 1, about 5% at ranks
2–16, 4% at ranks 17–20. In the reference, the median converted item came from backbone rank 4.

**Table 8. Exploratory score fusion (split-half, positives = all held-out)**

Score = −log(backbone rank) + w₀·label + w₁·clicked + w₂·converted, with label = interest − 3
(v3) or strong − none (reference). Weights were grid-searched on one half of users (seed 7) and
tested on the other half, in both directions.

| Protocol | Tune A → test B | Tune B → test A | Mean test ΔNDCG@10 |
|---|---:|---:|---:|
| reference | +0.0100 | +0.0032 | ≈ +0.007 (≈ +2%) |
| v3 | +0.0023 | +0.0007 | ≈ +0.0015 (≈ +0.5%) |

**What v3 shows**

- **The bias is gone.** v3 converts movies whose rating and popularity match what users actually
  watched, and it picks the top-rated title about as often as chance.
- **Accuracy dropped with it.** Without the rating prior and the backbone-ordered list, the agent's
  pick is only slightly better than a random slate item. The original agent's precision (34.8%)
  was largely borrowed from (a) the backbone's presentation order and (b) the popularity and
  quality prior, which correlate with being watched.
- **Fusion confirms this.** v3's interest scores add almost nothing on top of the backbone rank,
  while the reference's signals still add about 2%.
- **The positive definition no longer matters for v3.** It is about equally negative under all
  three definitions, so the earlier "≥ 4 helps" result was tied to the reference agent's
  preference for highly rated movies.
- **For the paper:** the simulator's apparent reranking value comes mostly from echoing the backbone
  and from an "acclaimed and popular" prior, not from modelling the individual user. This is a
  behavioral-fidelity finding worth testing in the human study.

**v3 caveats**

- The most likely drivers are the shuffled order and the removed aggregate rating, but this run
  cannot separate them. Next: two single-factor runs on the reference protocol, about $6 each:
  (a) shuffle the order only; (b) remove the aggregate rating only.
- Pilot behavior issues carried into the full run: interest is skewed high (4–5 = 67% in the
  pilot), clicks rise to 10.65 per slate with some slates fully clicked, Activity has no monotonic
  effect, and not_ready almost never occurs. This hurts click and three-tier most.
- One run at temperature 0 with a live, unpinned model alias. Fusion results are exploratory and
  split-half tuned.
- Analysis scripts for Tables 5–8: [v3_vs_reference.py](scripts/v3_vs_reference.py)
  and [fusion_split_half.py](scripts/fusion_split_half.py). They require the local raw
  archive layout described in [scripts/README.md](scripts/README.md). Pilot checks:
  [FORMAT_BIAS_REPORT.json](n1000_v3/pilot100/FORMAT_BIAS_REPORT.json).

## Supporting runs

<details>
<summary>50-user gpt-4o-mini vs gpt-5-mini, and 30-user pilot</summary>

50-user subset of the same panel (seed 42, includes the 30 pilot users), same profiles for both
LLMs. gpt-5-mini used `reasoning_effort=low` and temperature 1 (it rejects 0).

| LLM | Policy | Model | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|
| gpt-4o-mini | converted_then_original | MF | 0.1897 | 0.2402 | -0.0011 (-0.56%) | -0.0145 (-5.68%) |
| gpt-4o-mini | converted_then_original | LightGCN | 0.2083 | 0.2645 | -0.0015 (-0.73%) | -0.0255 (-8.79%) |
| gpt-4o-mini | converted_then_original | MultiVAE | 0.1993 | 0.2567 | -0.0002 (-0.10%) | -0.0234 (-8.34%) |
| gpt-4o-mini | click_only | MF | 0.1757 | 0.2434 | -0.0151 (-7.90%) | -0.0113 (-4.44%) |
| gpt-4o-mini | click_only | LightGCN | 0.2092 | 0.2885 | -0.0006 (-0.29%) | -0.0015 (-0.52%) |
| gpt-4o-mini | click_only | MultiVAE | 0.1906 | 0.2642 | -0.0089 (-4.48%) | -0.0159 (-5.69%) |
| gpt-4o-mini | three_tier | MF | 0.1757 | 0.2320 | -0.0151 (-7.90%) | -0.0227 (-8.92%) |
| gpt-4o-mini | three_tier | LightGCN | 0.2092 | 0.2616 | -0.0006 (-0.29%) | -0.0285 (-9.81%) |
| gpt-4o-mini | three_tier | MultiVAE | 0.1906 | 0.2406 | -0.0089 (-4.48%) | -0.0395 (-14.10%) |
| gpt-5-mini (low) | converted_then_original | MF | 0.1917 | 0.2402 | +0.0009 (+0.46%) | -0.0145 (-5.69%) |
| gpt-5-mini (low) | converted_then_original | LightGCN | 0.2066 | 0.2704 | -0.0032 (-1.54%) | -0.0196 (-6.75%) |
| gpt-5-mini (low) | converted_then_original | MultiVAE | 0.2020 | 0.2678 | +0.0025 (+1.25%) | -0.0123 (-4.40%) |
| gpt-5-mini (low) | click_only | MF | 0.1851 | 0.2517 | -0.0056 (-2.95%) | -0.0030 (-1.18%) |
| gpt-5-mini (low) | click_only | LightGCN | 0.2105 | 0.2770 | +0.0007 (+0.32%) | -0.0130 (-4.48%) |
| gpt-5-mini (low) | click_only | MultiVAE | 0.1928 | 0.2570 | -0.0067 (-3.35%) | -0.0231 (-8.23%) |
| gpt-5-mini (low) | three_tier | MF | 0.1851 | 0.2372 | -0.0056 (-2.95%) | -0.0174 (-6.84%) |
| gpt-5-mini (low) | three_tier | LightGCN | 0.2105 | 0.2688 | +0.0007 (+0.32%) | -0.0212 (-7.31%) |
| gpt-5-mini (low) | three_tier | MultiVAE | 0.1928 | 0.2511 | -0.0067 (-3.35%) | -0.0290 (-10.35%) |

30-user pilot:

| LLM | Policy | Model | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|
| gpt-4o-mini | converted_then_original | MF | 0.1924 | 0.2581 | +0.0000 (+0.00%) | +0.0170 (+7.06%) |
| gpt-4o-mini | converted_then_original | LightGCN | 0.2104 | 0.2780 | -0.0009 (-0.42%) | -0.0111 (-3.83%) |
| gpt-4o-mini | converted_then_original | MultiVAE | 0.1946 | 0.2634 | +0.0000 (+0.00%) | -0.0094 (-3.46%) |
| gpt-4o-mini | click_only | MF | 0.1773 | 0.2317 | -0.0151 (-7.87%) | -0.0094 (-3.89%) |
| gpt-4o-mini | click_only | LightGCN | 0.2092 | 0.2928 | -0.0021 (-1.00%) | +0.0036 (+1.26%) |
| gpt-4o-mini | click_only | MultiVAE | 0.1707 | 0.2605 | -0.0240 (-12.31%) | -0.0123 (-4.51%) |
| gpt-4o-mini | three_tier | MF | 0.1773 | 0.2469 | -0.0151 (-7.87%) | +0.0058 (+2.42%) |
| gpt-4o-mini | three_tier | LightGCN | 0.2092 | 0.2780 | -0.0021 (-1.00%) | -0.0111 (-3.82%) |
| gpt-4o-mini | three_tier | MultiVAE | 0.1707 | 0.2488 | -0.0240 (-12.31%) | -0.0240 (-8.80%) |

</details>

## Interpretation (short)

**v3 debiased protocol** (see the v3 section above): removing the aggregate rating,
shuffling the candidate order, adding the user's own ratings, and adding anti-popularity instructions
removed the popularity/quality bias (converted items' rating 4.25 → 3.82, top-rated share 43% → 6%), but
NDCG@10 dropped to −4% to −9% vs. the backbones (pooled −0.021). Converted-item precision fell from
34.8% to 23.7%, barely above the 20.7% slate base rate. The original agent's signal appears to come
mostly from following the backbone order and the popularity prior, not from modelling the user.

See [`BIAS_AUDIT.md`](BIAS_AUDIT.md) for the bias analysis, including Moonsoo's two hypotheses
(rating exposure, positive definition). With rating ≥ 4 as positives, pooled ΔNDCG@10 for
click + conversion turns from −0.0035 to +0.0031 (CI includes 0).


- **No real gain at 1,000 users.** With click + conversion, MF improves slightly (+0.4% to +1.5%
  NDCG, not significant), LightGCN and MultiVAE drop slightly (−1.5% to −2.5%). The +4–7% NDCG in
  the 50-user proposal slides does not replicate; the 30/50-user runs here swung both ways
  (MF +7% to LightGCN −9%), i.e. small-sample noise.
- **The input ablation barely matters.** All four conditions are within about 1 percentage point of
  each other in NDCG change, and the pooled changes are nearly identical (Table 3). "w/o demographics is best" (slide 12) does
  not replicate; dropping the persona is, if anything, slightly better for MF. The agent's choice
  is driven mainly by the candidate movies, not by the user information.
- **Why the policy hurts:** the converted movie is a held-out positive 34.8% of the time, while the
  backbone's own rank-1 item is a positive 39.8% of the time, so moving it to #1 usually pushes
  down a better item (DCG down in 1,117 full-input cases, up in 665). MF benefits only because its
  rank-1 precision (33.6%) is the lowest.
- **Bias toward acclaimed, popular titles:** converted movies average 4.25 aggregate rating and
  295 training interactions, vs. 3.80 and 216 for the movies users actually watched. This is a
  behavioral-fidelity finding in its own right.
- **The click → conversion signal is real but weak:** clicked items are positives 25.2% of the
  time vs. 17.3% for unclicked ones. Overriding the backbone with it (`click`, `three-tier`, ~9
  clicks per slate) hurts most. Adding small click / conversion / alignment bonuses on top of the
  backbone rank instead gave about +0.009 NDCG@10 (~+3%) on a held-out half of users (full input;
  exploratory, must be re-tuned on a validation split).
- **Persona traits barely change behavior:** clicks go 8.9 → 9.6 from Activity level 1 → 3;
  Diversity has no visible effect (clicked items are almost all `strong`); Conformity effects are
  tiny; the conversion check almost never contradicts a click hypothesis (0.4%).
- **gpt-5-mini vs gpt-4o-mini (50 users):** gpt-5-mini clicks fewer items (3.4 vs 8.7) with higher
  precision but converts items from deeper in the list, so NDCG is not clearly better (pooled
  difference +0.006, 95% CI [−0.010, +0.021]).

## Notes / things to be aware of

- **Code differs from the handoff commit** (available on branch `jinyi`):
  - `56ba845` saves full API transcripts and stops title punctuation (e.g. "Who Framed Roger
    Rabbit?") from failing the one-sentence check.
  - `f217db1` adds:
    - HTTP 429/5xx retries with backoff
    - resumable profile generation
    - a retry instruction used only after an "evidence must be a nonempty string" failure;
      first-attempt prompts are unchanged
- **Missing cases recovered:** 21 `full` cases first failed because gpt-4o-mini returned an empty
  `evidence` for some `none` items, identically on every retry. All 21 were recovered with the new
  retry instruction. The three ablations had no such failures.
- **Profiles were partly replayed:** the first profile attempt stopped on HTTP 429 after 689 users.
  Their exact API responses (same prompt, model, temperature) were reused from transcripts, and
  311 users were newly generated. This differs from the handoff's "do not combine partial
  artifacts" rule in letter, not in substance.
- **Rate limits and execution:** concurrency 16, 300 RPM, 1M TPM (the handoff says 20/300/1M). 32
  workers triggered HTTP 429 from the proxy. The run was paused once after `full` for analysis.
  None of this affects results.
- **Raw outputs live outside the repo**; this directory publishes only reports,
  aggregate CSVs, and unchanged offline analysis scripts.
- **Transcripts:** every 1,000-user run directory has `transcripts.jsonl` (prompts, raw responses,
  validation verdicts) and `prompts/`. The 50- and 30-user runs predate this logging. gpt-5-mini's
  internal reasoning is not returned by the API; only reasoning-token counts are.
- **50-user reproduction:** raw run directories, panels, and the reasoning wrapper
  are not in repo; see the off-repo archive.

## Next steps

- Decide the reranking policy with Moonsoo. Score fusion (LLM signals as bonuses on the backbone
  rank) looks more promising than overriding. Tune it on a validation split, then re-score all
  four conditions offline from `actions.jsonl` (no new API calls needed).
- Add a listwise LLM baseline (full permutation) for comparison with the related work.
- Use the popularity/rating bias and weak trait adherence as the starting point for the human
  study (do people pick the "acclaimed" titles too?).

## Folder layout

```
jinyi_results/
├── README.md                     this file
├── BIAS_AUDIT.md                 audit of the rating/popularity bias and its likely causes
├── n1000_v2/
│   ├── summary_table.md          aggregate handoff table
│   ├── analysis.md               tables and bootstrap CIs
│   ├── analysis_full/report_full.md
│   └── analysis_bias/bias_eval.json
├── n1000_v3/pilot100/FORMAT_BIAS_REPORT.json
├── summary_csv/                  8 aggregate run summaries
└── scripts/                      4 unchanged offline scripts and archive-layout README
```

CSV summaries: [full](summary_csv/n1000_full.csv),
[no demographics](summary_csv/n1000_no_demographics.csv),
[no persona](summary_csv/n1000_no_persona.csv),
[no interaction history](summary_csv/n1000_no_interaction_history.csv),
[v3 full](summary_csv/n1000_v3_full.csv),
[50-user gpt-4o-mini](summary_csv/n50_gpt-4o-mini.csv),
[50-user gpt-5-mini low](summary_csv/n50_gpt-5-mini_low.csv),
and [30-user pilot](summary_csv/pilot30.csv).

Aggregate handoff table: [summary_table.md](n1000_v2/summary_table.md).
Bias evaluation numbers: [bias_eval.json](n1000_v2/analysis_bias/bias_eval.json).
Raw run directories, profiles, transcripts, prompts, and controllers are not in repo;
see the off-repo archive.
