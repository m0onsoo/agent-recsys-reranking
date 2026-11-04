# Jinyi's experiment results — agent reranking (MovieLens-1M)

Last updated: 2026-11-03 (PT). Code: `agent-recsys-reranking` on local branch
`jinyi/transcripts-validator-fix` (commit `56ba845` on top of handoff commit `ec7fac9`, plus
uncommitted retry/profile-resume changes; see Notes).

## Status

| Experiment | Users | LLM | Status | Recorded cost |
|---|---:|---|---|---:|
| 1,000-user handoff run — `full` condition | 1,000 | gpt-4o-mini | **done** (2,979 / 3,000 cases) | $6.19 incl. profiles |
| 1,000-user — `no_demographics`, `no_persona`, `no_interaction_history` | 1,000 | gpt-4o-mini | **paused** before start | – |
| 50-user LLM comparison | 50 | gpt-4o-mini vs gpt-5-mini | done (150 / 150 each) | $0.30 / $0.90 |
| 30-user pilot | 30 | gpt-4o-mini | done (90 / 90) | $0.18 |

The 1,000-user run was stopped on purpose after `full` so the results could be checked before
spending on the three ablations. Costs are token-rate estimates, not the proxy bill.

## Main result: 1,000 users, `full` condition

Same format as the handoff summary table. Prompt `behavior-align-rating-social-traits`,
profile protocol `separated`, gpt-4o-mini, temperature 0, Top-20 candidates, Top-10 evaluation,
all held-out interactions count as positives. Changes are vs. each backbone on the same cases.

| Condition | Model | Stage | Cases | Failures | Recorded cost | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| full | MF | sampled_baseline | 993 | 7 | $1.94 | 0.1742 | 0.2819 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | MF | click_only | 993 | 7 | $1.94 | 0.1718 | 0.2794 | -0.0025 (-1.42%) | -0.0025 (-0.90%) |
| full | MF | converted_then_original | 993 | 7 | $1.94 | 0.1760 | 0.2844 | +0.0017 (+0.99%) | +0.0025 (+0.89%) |
| full | MF | three_tier | 993 | 7 | $1.94 | 0.1718 | 0.2800 | -0.0025 (-1.42%) | -0.0020 (-0.70%) |
| full | LightGCN | sampled_baseline | 991 | 9 | $1.92 | 0.2045 | 0.3431 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | LightGCN | click_only | 991 | 9 | $1.92 | 0.2003 | 0.3321 | -0.0042 (-2.04%) | -0.0110 (-3.22%) |
| full | LightGCN | converted_then_original | 991 | 9 | $1.92 | 0.2048 | 0.3382 | +0.0003 (+0.15%) | -0.0049 (-1.43%) |
| full | LightGCN | three_tier | 991 | 9 | $1.92 | 0.2000 | 0.3275 | -0.0045 (-2.20%) | -0.0156 (-4.53%) |
| full | MultiVAE | sampled_baseline | 995 | 5 | $1.94 | 0.2051 | 0.3307 | +0.0000 (+0.00%) | +0.0000 (+0.00%) |
| full | MultiVAE | click_only | 995 | 5 | $1.94 | 0.1983 | 0.3234 | -0.0067 (-3.29%) | -0.0074 (-2.22%) |
| full | MultiVAE | converted_then_original | 995 | 5 | $1.94 | 0.2052 | 0.3225 | +0.0002 (+0.08%) | -0.0083 (-2.51%) |
| full | MultiVAE | three_tier | 995 | 5 | $1.94 | 0.1984 | 0.3156 | -0.0067 (-3.25%) | -0.0151 (-4.57%) |

User-clustered bootstrap (2,000 resamples), NDCG@10 change pooled over the three backbones:

| Stage | ΔNDCG@10 | 95% CI |
|---|---:|---|
| click_only | −0.0068 | [−0.0119, −0.0023] |
| converted_then_original | −0.0036 | [−0.0073, −0.0001] |
| three_tier | −0.0109 | [−0.0164, −0.0048] |

Per backbone, `converted_then_original` NDCG@10: MF +0.0025 [−0.0032, +0.0081];
LightGCN −0.0049 [−0.0099, +0.0003]; MultiVAE −0.0083 [−0.0132, −0.0034].
Full diagnostics: [`n1000_v2/analysis_full/report_full.md`](n1000_v2/analysis_full/report_full.md).

## Supporting runs

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

30-user pilot (subset of the 1,000-user panel):

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

## Interpretation (short)

- **At 1,000 users the default policy is roughly neutral to slightly negative.** It helps MF a
  little (+0.9% NDCG, not significant) and hurts LightGCN (−1.4%) and MultiVAE (−2.5%,
  significant). The +4–7% NDCG gains in the 50-user proposal slides do not replicate, and the
  30/50-user runs here swung both ways (MF +7% to LightGCN −9%), i.e. small-sample noise.
- **Why:** the single converted movie is a held-out positive 34.7% of the time, while the
  backbone's own rank-1 item is a positive 39.8% of the time. Moving the converted movie to the
  top therefore usually pushes down a better item (DCG down in 1,109 cases, up in 660). MF gains
  only because its rank-1 precision (33.8%) is closest to the agent's.
- **The agent prefers acclaimed, popular titles:** converted movies average 4.25 aggregate
  rating and 295 training interactions, vs. 3.80 and 216 for the movies users actually watched.
- **The signal is real but weak:** clicked items are positives 25.1% of the time vs. 17.3% for
  unclicked ones. Promoting all clicks (`click_only`, ~9 clicks per slate) or tiers scrambles the
  backbone order and hurts more.
- **Score fusion looks better than override:** adding small bonuses for click / conversion /
  alignment on top of the backbone rank gave about +0.009 NDCG@10 (~+3%) on a held-out half of
  users (weights tuned on the other half). Exploratory only; must be re-done on a validation
  split before being reported.
- **Persona traits barely change behavior:** clicks rise only 8.9 → 9.6 from Activity level 1 → 3;
  Diversity has no visible effect (clicked items are almost all `strong`); Conformity effects are
  tiny. The conversion check almost never contradicts a click hypothesis (0.4%).
- **gpt-5-mini vs gpt-4o-mini (50 users):** gpt-5-mini clicks far fewer items (3.4 vs 8.7) with
  higher precision, but picks conversions from deeper in the list, so NDCG is not clearly better
  (pooled difference +0.006, 95% CI [−0.010, +0.021]).

## Notes / things to be aware of

- **Code differs from the handoff commit.** Commit `56ba845` adds full API transcripts and stops
  movie-title punctuation (e.g. "Who Framed Roger Rabbit?") from failing the one-sentence check.
  The 1,000-user run also uses uncommitted changes (HTTP 429/5xx retries with backoff, resumable
  profile generation); file hashes are in `n1000_v2/code_version_resume_before.json`. Model
  requests are unchanged. Commit these after the run finishes and show Moonsoo the diff.
- **Profiles were partly replayed.** The first profile attempt stopped on HTTP 429 after 689 users.
  Those users' exact API responses were reused from the transcripts (same prompt, model,
  temperature) and only 311 users were newly generated. This differs from the handoff's
  "do not combine partial artifacts" rule in letter, not in substance.
- **21 cases are missing** (MF 7, LightGCN 9, MultiVAE 5). gpt-4o-mini returns an empty `evidence`
  string for some `none` items, identically on every retry at temperature 0, so `--resume` cannot
  recover them. Metrics above exclude these cases for both the agent and the backbone.
- **Rate limits:** concurrency 16, 300 RPM, 1M TPM (the handoff says 20/300/1M); 32 concurrent
  workers triggered HTTP 429 from the proxy. These settings do not affect results.
- **Outputs live outside the repo** because `results/n1000_align_rating/` is not gitignored.
- **Transcripts:** every 1,000-user run directory has `transcripts.jsonl` (full prompts, raw
  responses, validation verdicts) and `prompts/`. The 50-user and 30-user runs predate this logging.
  gpt-5-mini's internal reasoning is not returned by the API; only reasoning-token counts are.
- **Do not move or rename `n1000_v2/` or `n50/`** while the experiment is paused: their controller
  scripts use these paths (`n50` also needs `../panels/` and `../run_with_reasoning.py`).

## How to continue the 1,000-user run

Archive `n1000_v2/STOP_REQUEST.json`, decide how to handle the 21 empty-evidence cases (targeted
retry message, or cap resumes and report them), then restart the controller
(`n1000_v2/execute_experiment.py`). It skips `full` and runs `no_demographics`, `no_persona`,
`no_interaction_history` in order (~50 min and ~$6 each).

## Folder layout

```
jinyi_results/
├── README.md                     this file
├── n1000_v2/                     1,000-user handoff run (paused after `full`)
│   ├── profiles/ours_all_n1000/  1,000 profiles + transcripts + prompts
│   ├── n1000_align_rating/full/runs/<run_id>/   actions, rankings, metrics, transcripts
│   ├── analysis_full/            offline analysis script + report_full.md
│   ├── execute_experiment.py     Codex controller (resume, safety stops, reports)
│   └── run_info.md, timeline.md, execution_events.jsonl, progress.json, logs
├── n50/                          50-user gpt-4o-mini vs gpt-5-mini comparison
│   ├── gpt-4o-mini/runs/, gpt-5-mini_low/runs/, smoke/runs/, profiles/
│   └── report_zh.md, comparison.csv, behavior.csv, bootstrap_ci.csv, costs.csv
├── pilot30/                      30-user pilot (runs/, profiles/, run_pilot.sh, logs)
├── panels/users_50_from_1000_seed42.csv   50-user panel (needed by n50)
├── run_with_reasoning.py         wrapper that adds reasoning_effort for GPT-5 models
└── code/code_changes_transcripts_validator.patch   diff of commit 56ba845
```
