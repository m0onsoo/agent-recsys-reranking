# Bias audit: why the agent reranker under-performs the backbone

Date: 2026-11-04 · Scope: the 1,000-user run in `n1000_v2/` (gpt-4o-mini, prompt
`behavior-align-rating-social-traits`, 4 input conditions × 3 backbones × 1,000 users), plus the
30/50-user pilots and Moonsoo's earlier audits in the repository's `results/` directory.
Every number below was computed offline from saved artifacts; no new API calls were made.
Analysis scripts: [bias_eval.py](scripts/bias_eval.py) and
[analyze_full.py](scripts/analyze_full.py). They read local raw run directories,
which are not in repo; see [scripts/README.md](scripts/README.md) and the off-repo archive.
Published numbers: [bias_eval.json](n1000_v2/analysis_bias/bias_eval.json) and
[report_full.md](n1000_v2/analysis_full/report_full.md).

## TL;DR

1. **The agent picks acclaimed, popular movies, and users don't.** Converted items sit at the
   91st percentile of their slate by aggregate rating (77th by popularity), and 43% of the time
   the agent converts the single highest-rated movie in the slate. Conversion rate rises 130×
   from low-rated to high-rated movies, while the true positive rate stays flat at about 20%.
2. **Showing `average_rating` is a likely cause** (Moonsoo's point 1). The proposal's 50-user
   gains came from the original code, which did not show ratings. In Moonsoo's paired 30-user
   control, hiding ratings raised `converted_then_original` NDCG@10 by +0.012 to +0.025 for all
   three backbones, and rating mentions in the agent's reasons fell from 783 to 7. The current
   protocol goes further and asks for a predicted 1–5 rating, which the prompt calls "important
   comparative evidence".
3. **The positive definition penalizes the agent** (Moonsoo's point 2). With all held-out
   interactions as positives, pooled ΔNDCG@10 is −0.0035. With rating ≥ 4 as positives it becomes
   +0.0031 (MF +4.5%, LightGCN +0.7%, MultiVAE −1.1%), with the same direction in all four input
   conditions. The CIs still include 0.
4. **The candidate list is shown in backbone order** although the prompt says ranks are not
   provided. Conversion rate falls 17× from rank 1 to rank 20, against 3× for the true positive
   rate, so there is also a position effect.
5. Other contributors: the user's own ratings are missing from the history shown to the agent;
   personas are generic; the single-conversion → rank-1 policy is blunt; trait instructions have
   almost no effect.

## 1. Evidence of the bias

### 1.1 Rating and popularity of what the agent picks (full input, 3,000 cases)

| | Converted item | Backbone rank-1 item | Held-out positives | Whole slate |
|---|---:|---:|---:|---:|
| Mean aggregate rating (1–5) | **4.25** | 3.87 | 3.80 | 3.79 |
| Mean train popularity (interactions) | **295** | 233 | 216 | 199 |

Within-slate percentile of the converted item: 0.91 by rating and 0.77 by popularity (0.5 = slate
median). In 42.6% of cases the converted item is the highest-rated movie in the slate.

### 1.2 The agent follows aggregate rating, users do not

All 60,000 candidate items in `full`, binned by aggregate rating:

| Aggregate rating | Items | Click rate | Conversion rate | True positive rate |
|---|---:|---:|---:|---:|
| < 3.5 | 14,344 | 19.6% | 0.15% | 19.5% |
| 3.5–4.0 | 23,361 | 42.0% | 1.3% | 21.0% |
| 4.0–4.3 | 14,925 | 62.6% | 7.1% | 21.4% |
| ≥ 4.3 | 7,370 | 69.1% | **20.0%** | 20.6% |

Consequence: the converted item is a positive 34.8% of the time, against 39.8% for the backbone's
rank-1 item. Promoting it lowers DCG in 1,117 cases and raises it in 665.

The same pattern appears with gpt-5-mini on 50 users: converted items average a 4.24 rating. A
stronger model does not remove it.

## 2. Candidate causes

| # | Source | Where | What it does | Evidence | Severity |
|---|---|---|---|---|---|
| A | `average_rating` shown for every candidate | click and conversion prompts, `agent.py` (`exposes_average_rating` is true for every version except v1) | Gives the model a ready "quality" score | V1 (hidden) vs V2 (shown), same 30 users: NDCG +0.013/+0.025/+0.012 for MF/LightGCN/MultiVAE; rating references in reasons 7 vs 783 (`results/pilot30_natural_v1_vs_v2_audit_20261103.md`) | **High** |
| B | Predicted 1–5 rating, called "important comparative evidence"; Conformity instructions tie decisions to `average_rating` | conversion prompt (current protocol only) | Turns the final choice into "pick the highest predicted rating", which tracks the aggregate rating (mean \|pred − avg\| ≈ 0.40) | Converted item is the slate's top-rated movie in 43% of cases | **High** |
| C | Positives = every held-out interaction (ratings 1–5) | evaluation (`metrics.py`); handoff §3 | The agent aims at "would enjoy", the metric rewards "did watch"; 16.6% of positives are rated 1–2 | Pooled ΔNDCG: −0.0035 (all) → −0.0017 (≥3) → +0.0031 (≥4); converted-item precision equals rank-1 precision under ≥4 (31.1% vs 31.4%) | **High** |
| D | Backbones trained on all ratings | RecBole checkpoints | Backbones are optimized for exactly the "did watch" target in C, which favors them under the current metric | Backbone NDCG drops 0.2815 → 0.2368 (MF) when switching to ≥4, but the agent drops less | Medium (interacts with C) |
| E | Candidates listed in backbone order | `agent.py` `simulate()` builds the slate in `item_ids` order; the conversion context says the slate "does not provide recommender scores or ranks" | LLM primacy bias; the agent partly echoes the backbone order | Conversion rate 13.7% at rank 1 → 0.8% at rank 20 (17×) while positive rate goes 39% → 13% (3×) | Medium |
| F | User's own ratings missing from `interaction_history` | `runner._profile_payload` passes title, year, genres, overview, director, cast, date, language, country | Movies the user disliked look like preferences, which weakens personal evidence and leaves item quality as the easiest signal | Fields audited in the 1,000 profiles | Medium |
| G | Generic personas; "like" threshold is rating ≥ 3 | `prompts/profile_ours_*.txt` | A rating of 3 is neutral, yet it counts as "liked". gpt-4o-mini personas are often generic or self-contradictory (e.g. "Positive ratings for drama films" alongside "Dislike for films rated below 3 in drama") | Input ablation changes pooled ΔNDCG by ≤ 0.001 across conditions | Medium |
| H | One conversion promoted to rank 1 | `rerank.py` `converted_then_original` | Each mistake costs the full rank-1 position | Score fusion (bonuses on top of backbone rank) gave +0.0095 on held-out users vs −0.0021 for the current policy | High for metrics, not a behavior bias |
| I | Social-trait instructions barely followed | click and conversion prompts | No user-specific counterweight to the quality prior | Clicks 8.9 → 9.6 from Activity level 1 → 3; adjacent share ≈ 0.3% at every Diversity level; conversion check contradicts a click in only 0.4% of cases | Medium |
| J | LLM's prior knowledge of canonical films | model pre-training; MovieLens-1M is a pre-2001 catalog | Famous titles are recognized and pre-judged as good even without the rating field | Not tested yet (a title-masking test would isolate it) | Unknown |
| K | Sample design | random-order split; joint Top-20 eligibility filter | Held-out items are a random sample of viewing, with no recency and no extra popularity; results apply only to users whose positives appear in all three Top-20 lists | Positives' popularity (216) ≈ slate (199) | Low (scope) |

## 3. Moonsoo's two hypotheses

**H1: the 50-user improvement had no per-item ratings; showing them in the GitHub version may
explain the drop.** Supported. The proposal numbers come from the original `run_m4.py` code with
the v1 prompts, which do not show ratings (`results/original_code_no_cache_comparison_20261102.md`,
`results/repro50_current_head_audit_20261103.md`). Ratings were added in commit `39337d7` (Nov 3).
The only paired test so far (30 users, V1 vs V2) favors hiding ratings on all three backbones, but
n = 30, and V2 is not the current protocol: the current one adds predicted ratings, which should
make the effect stronger. This needs a 1,000-user rating-blind run of the current protocol.

**H2: low ratings (< 3) count as positives but may not be genuine interest; restrict positives to
≥ 3.** Partly supported. ≥ 3 halves the gap; ≥ 4 reverses its sign:

| Positives | Users | MF | LightGCN | MultiVAE | Pooled ΔNDCG@10 [95% CI] |
|---|---:|---:|---:|---:|---|
| all ratings | 1,000 | +1.07% | −1.47% | −2.53% | −0.0035 [−0.0070, +0.0002] |
| rating ≥ 3 | 997 | +2.33% | −1.12% | −2.37% | −0.0017 [−0.0053, +0.0022] |
| rating ≥ 4 | 987 | +4.53% | +0.66% | −1.13% | +0.0031 [−0.0011, +0.0078] |

(full input, `click + conversion`; percentages are relative NDCG@10 change vs. the backbone under
the same positive definition.) The other three input conditions show the same ordering
(≥ 4 pooled: +0.0032, +0.0035, +0.0012).

Caveats: (i) none of these intervals excludes 0; (ii) choosing the metric after seeing results is
a researcher degree of freedom, so report all three definitions, or fix one in advance and argue
for it ("liked" = rating ≥ 4 matches the agent's stated goal; "watched" matches the backbone's
training target); (iii) users with no ≥ 4 held-out item (13) drop out.

## 4. Recommended checks (cheap first)

| Priority | Check | Cost | Tests |
|---|---|---|---|
| 1 | Report all / ≥ 3 / ≥ 4 positive definitions for every condition (done here, offline) | $0 | C, D |
| 2 | Rating-blind variant of the current protocol: remove `average_rating`, predicted rating, and the rating sentences; keep everything else. Run 1,000 users, full input | ≈ $6 | A, B (H1) |
| 3 | Shuffle candidate order with a fixed seed per case; keep backbone order only for tie-breaking | ≈ $6 | E |
| 4 | Add the user's own rating to each `interaction_history` item | ≈ $6 | F |
| 5 | Score-fusion policy tuned on a validation split, then applied to all saved runs | $0 | H |
| 6 | Title masking (show genres/overview only) on 200 users | ≈ $1 | J |
| 7 | Human study: do people also choose the acclaimed titles from the same slates? | — | fidelity of the bias itself |

Run 2–4 as single-factor changes against the existing `full` run (same users, profiles, slates,
temperature 0) so each effect is attributable. After that, fix the prompt and metric before the
final evaluation.

## 5. What this means for the paper

- The current headline ("behavioral funnel improves offline accuracy") is not supported at
  1,000 users under the handoff metric. Results depend on prompt exposure of ratings and on what
  counts as a positive, so both must be stated explicitly.
- The bias itself is a finding: the LLM user simulator substitutes item quality and popularity
  for personal taste, and persona and trait conditioning barely change this. That fits the
  behavioral-fidelity / human-study contribution well.
