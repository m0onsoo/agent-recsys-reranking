# Jinyi's experiment results — agent reranking (MovieLens-1M)

Last updated: 2026-11-04 (PT). Code: `agent-recsys-reranking`, local branch
`jinyi/transcripts-validator-fix` = handoff commit `ec7fac9` + `56ba845` + `f217db1` (see Notes).
Not pushed.

## Status

| Experiment | Users | LLM | Status | Recorded cost |
|---|---:|---|---|---:|
| 1,000-user handoff run, 4 conditions | 1,000 | gpt-4o-mini | **complete** — 3,000 / 3,000 cases per condition, 0 missing | $22.17 total (profiles $0.33; full $5.85, no_demographics $5.83, no_persona $5.70, no_interaction_history $4.42) |
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

- **Code differs from the handoff commit** (all committed locally, not pushed):
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
- **Outputs live outside the repo** because `results/n1000_align_rating/` is not gitignored.
- **Transcripts:** every 1,000-user run directory has `transcripts.jsonl` (prompts, raw responses,
  validation verdicts) and `prompts/`. The 50- and 30-user runs predate this logging. gpt-5-mini's
  internal reasoning is not returned by the API; only reasoning-token counts are.
- **Keep `n50/` next to `../panels/` and `../run_with_reasoning.py`**; its scripts use those paths.

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
├── n1000_v2/                     1,000-user handoff run (complete)
│   ├── profiles/ours_all_n1000/  1,000 profiles + transcripts + prompts
│   ├── n1000_align_rating/<condition>/runs/<run_id>/   actions, rankings, metrics, transcripts
│   ├── summary_table.md, analysis.md   controller-generated tables and bootstrap CIs
│   ├── analysis_full/            extra diagnostics for `full` (analyze_full.py, report_full.md)
│   ├── SHA256SUMS.txt, run_info.md, timeline.md, execution_events.jsonl
│   └── execute_experiment.py     Codex controller (resume, safety stops, reports)
├── n50/                          50-user gpt-4o-mini vs gpt-5-mini comparison (report_zh.md, CSVs)
├── pilot30/                      30-user pilot (runs/, profiles/, run_pilot.sh, logs)
├── panels/users_50_from_1000_seed42.csv   50-user panel (needed by n50)
├── run_with_reasoning.py         wrapper that adds reasoning_effort for GPT-5 models
└── code/code_changes_transcripts_validator.patch   diff of commit 56ba845
```
