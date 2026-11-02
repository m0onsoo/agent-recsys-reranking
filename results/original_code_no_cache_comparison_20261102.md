# Original-code GPT-4o-mini 50-user no-cache rerun

Date: 2026-11-02  
Jobs: `13673402` (full), `13673425_[0-3]` (ablations)  
Implementation: the original parent-repository `run_m4.py` pipeline  
Panel: fixed legacy 50 users  
Backbones: MF, LightGCN, vanilla MultiVAE  
LLM cache: disabled (zero hits in every condition)

## Completion

| Condition | Cases | LLM attempts | Final failures |
|---|---:|---:|---:|
| full | 150/150 | 300 | 0 |
| w/o demographics | 150/150 | 300 | 0 |
| w/o history | 150/150 | 303 | 0 |
| w/o persona | 150/150 | 300 | 0 |
| w/o all user context | 149/150 | 301 | 1 |

The one omitted case is MultiVAE user 5407 in the no-context condition. It failed with a transient `RemoteDisconnected`. The no-context MultiVAE aggregate therefore uses 49 users; all other cells use 50.

## Results

All values are relative changes from the unchanged backbone Top-10 baseline. Each pair is Recall@10 / NDCG@10.

| Condition | Backbone | Click rerank | Conversion rerank |
|---|---|---:|---:|
| full | MF | +6.782% / -0.838% | +4.007% / +4.473% |
| full | LightGCN | +2.534% / -0.597% | +1.820% / +2.375% |
| full | MultiVAE | +0.056% / -0.766% | +1.794% / +2.205% |
| w/o demographics | MF | +5.412% / -2.581% | +8.899% / +8.378% |
| w/o demographics | LightGCN | +3.851% / +1.581% | +3.420% / +5.371% |
| w/o demographics | MultiVAE | +3.703% / -0.150% | +2.050% / -1.158% |
| w/o history | MF | +6.202% / -0.844% | +8.053% / +5.542% |
| w/o history | LightGCN | -3.036% / -6.368% | -3.033% / -4.567% |
| w/o history | MultiVAE | -3.305% / -6.755% | -0.979% / -5.704% |
| w/o persona | MF | +3.169% / +0.568% | -1.578% / -4.341% |
| w/o persona | LightGCN | +2.694% / -0.616% | -0.364% / +0.444% |
| w/o persona | MultiVAE | -5.588% / -2.628% | -5.382% / +0.679% |
| w/o all user context | MF | -6.607% / -3.415% | +2.470% / -3.375% |
| w/o all user context | LightGCN | -0.127% / -0.969% | -2.389% / -5.982% |
| w/o all user context | MultiVAE (n=49) | -5.697% / -3.274% | -7.700% / -4.754% |

## Comparison with the migrated repository

The main policy is conversion-first reranking. Each pair is Recall@10 / NDCG@10 relative change.

| Condition | Backbone | Original code, fresh | Migrated repository |
|---|---|---:|---:|
| full | MF | +4.007% / +4.473% | +3.443% / +0.240% |
| full | LightGCN | +1.820% / +2.375% | +0.607% / -0.662% |
| full | MultiVAE | +1.794% / +2.205% | -0.468% / -6.430% |
| w/o demographics | MF | +8.899% / +8.378% | +3.443% / +0.578% |
| w/o demographics | LightGCN | +3.420% / +5.371% | +1.820% / +3.160% |
| w/o demographics | MultiVAE | +2.050% / -1.158% | -0.468% / -2.756% |
| w/o history | MF | +8.053% / +5.542% | +8.053% / +5.190% |
| w/o history | LightGCN | -3.033% / -4.567% | -1.941% / -0.396% |
| w/o history | MultiVAE | -0.979% / -5.704% | -0.261% / -7.206% |
| w/o persona | MF | -1.578% / -4.341% | +3.156% / -1.737% |
| w/o persona | LightGCN | -0.364% / +0.444% | 0.000% / -3.391% |
| w/o persona | MultiVAE | -5.382% / +0.679% | -1.409% / +0.468% |

## Behavioral agreement between fresh full-input runs

| Backbone | Exact click set | Exact click sequence | Same converted set | Mean click-set Jaccard |
|---|---:|---:|---:|---:|
| MF | 7/50 | 7/50 | 24/50 | 0.592 |
| LightGCN | 5/50 | 3/50 | 26/50 | 0.625 |
| MultiVAE | 4/50 | 4/50 | 27/50 | 0.575 |

## Interpretation

- The original-code fresh full-input run improves both conversion-reranked metrics for all three backbones. This agrees directionally with the earlier original-code full runs and does not reproduce the migrated repository's large vanilla-MultiVAE decline.
- Removing demographics is again strongly positive for MF and LightGCN. MultiVAE Recall improves slightly, but NDCG declines slightly.
- Removing history again hurts both metrics for LightGCN and MultiVAE, while MF improves. This is the most stable ablation pattern across implementations.
- Removing persona hurts conversion Recall for all three original-code backbones, particularly MultiVAE. Its NDCG effect is mixed.
- Removing all user context is broadly harmful for LightGCN and MultiVAE. The missing MultiVAE case does not explain a -7.7% Recall change by itself.
- The 50-user paired bootstrap intervals mostly include zero. These are exploratory trends, not statistically established effects.
- Low action overlap demonstrates substantial GPT run-to-run variability even at temperature zero. Nevertheless, because the original-code full trend is positive again while the migrated MultiVAE trend is strongly negative, behavioral equivalence of the migrated implementation should be treated as unverified rather than assumed.

## Raw run directories

- Full: `outputs/all_ratings_ro_original_code_full_no_cache_reproduction/20261102_1238_mf-lightgcn-multivae_gpt-4o-mini_c876396c`
- No demographics: `outputs/all_ratings_ro_mf_v3_motive_v4_50_no_demographics_experiments/20261102_1241_mf-lightgcn-multivae_gpt-4o-mini_683ddbd9`
- No history: `outputs/all_ratings_ro_mf_v3_motive_v4_50_no_history_experiments/20261102_1245_mf-lightgcn-multivae_gpt-4o-mini_c6d6c002`
- No persona: `outputs/all_ratings_ro_mf_v3_motive_v4_50_no_persona_experiments/20261102_1249_mf-lightgcn-multivae_gpt-4o-mini_6de2d1d3`
- No user context: `outputs/all_ratings_ro_mf_v3_motive_v4_50_no_user_context_experiments/20261102_1253_mf-lightgcn-multivae_gpt-4o-mini_09d4fc40`
