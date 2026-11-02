# GPT-4o-mini 50-user input-ablation reproduction

Date: 2026-11-02  
Model: `gpt-4o-mini`  
Users: the same 50-user legacy panel  
Backbones: MF, LightGCN, vanilla MultiVAE  
Reranking policy used for the main comparison: `converted_then_original`

## Completion

All four conditions have 150/150 completed user-backbone cases.

| Condition | Run ID | Completed | Recorded failures | Recorded cost (USD) |
|---|---|---:|---:|---:|
| full | `20261102_122510_68e61f4f15` | 150/150 | 0 | 0.188471 |
| w/o demographics | `20261102_122510_0e0714dc10` | 150/150 | 0 | 0.187364 |
| w/o persona | `20261102_122512_0557e2b36a` | 150/150 | 0 | 0.185266 |
| w/o interaction history | `20261102_122506_dab0d7870e` | 150/150 | 1 historical, recovered | 0.122694 |

The `w/o interaction history` run initially received one invalid response for MultiVAE user 39. Array job `13673366` resumed the existing run and recovered that case. The retained failure row is an audit record, not a missing final action. Its recorded cost does not include the failed attempt, so the actual total cost is slightly above the sum shown here (at least USD 0.683794).

## New results

Values are relative changes against each backbone's unchanged sampled baseline. `R` is Recall@10 and `N` is NDCG@10.

| Condition | Backbone | R change | N change |
|---|---|---:|---:|
| full | MF | +3.443% | +0.240% |
| full | LightGCN | +0.607% | -0.662% |
| full | MultiVAE | -0.468% | -6.430% |
| w/o demographics | MF | +3.443% | +0.578% |
| w/o demographics | LightGCN | +1.820% | +3.160% |
| w/o demographics | MultiVAE | -0.468% | -2.756% |
| w/o persona | MF | +3.156% | -1.737% |
| w/o persona | LightGCN | 0.000% | -3.391% |
| w/o persona | MultiVAE | -1.409% | +0.468% |
| w/o interaction history | MF | +8.053% | +5.190% |
| w/o interaction history | LightGCN | -1.941% | -0.396% |
| w/o interaction history | MultiVAE | -0.261% | -7.206% |

## Comparison with the earlier 50-user runs

Each cell is `Recall@10 / NDCG@10` relative change. MultiVAE comparisons use the same vanilla checkpoint rather than the older non-vanilla result.

| Condition | Backbone | Earlier | New | Direction assessment |
|---|---|---:|---:|---|
| full | MF | +1.355% / +0.860% | +3.443% / +0.240% | both positive again |
| full | LightGCN | +2.813% / +6.531% | +0.607% / -0.662% | recall agrees; NDCG flips |
| full | MultiVAE | +1.794% / +3.192% | -0.468% / -6.430% | both flip |
| w/o demographics | MF | +10.257% / +4.423% | +3.443% / +0.578% | both positive again |
| w/o demographics | LightGCN | +2.813% / +7.272% | +1.820% / +3.160% | both positive again |
| w/o demographics | MultiVAE | +0.256% / +4.384% | -0.468% / -2.756% | both flip |
| w/o persona | MF | -1.578% / -7.075% | +3.156% / -1.737% | NDCG agrees; recall flips |
| w/o persona | LightGCN | -0.364% / -0.698% | 0.000% / -3.391% | non-positive again |
| w/o persona | MultiVAE | -0.979% / +0.678% | -1.409% / +0.468% | both directions agree |
| w/o interaction history | MF | +2.372% / -0.525% | +8.053% / +5.190% | recall agrees; NDCG flips |
| w/o interaction history | LightGCN | -1.144% / -4.205% | -1.941% / -0.396% | both negative again |
| w/o interaction history | MultiVAE | +0.815% / -1.360% | -0.261% / -7.206% | NDCG agrees; recall slightly flips |

## Interpretation

This is a partial trend reproduction, not a numerical reproduction.

- MF and LightGCN reproduce several broad signs: removing demographics still improves both metrics, removing persona leaves LightGCN non-positive, and removing history still hurts LightGCN.
- MultiVAE is the unstable backbone. The full and no-demographics conditions reverse both earlier signs, while no-persona reproduces both signs and no-history again lowers NDCG.
- The paired 50-user bootstrap 95% intervals for the new absolute conversion-reranking deltas mostly include zero. The only one-sided boundary cases are small, discrete Recall@10 effects. Therefore the differences among these four prompts should not be treated as statistically established at n=50.
- The scientifically defensible conclusion is that the pipeline and broad ablation behavior are reproducible, while exact effect sizes and several signs—especially vanilla MultiVAE—are sensitive to GPT sampling. The planned 1,000-user run is needed for a stable comparison.

## Protocol notes

- The legacy reproduction protocol passes one historical `persona_summary` string and does not duplicate social traits.
- `w/o persona` removes both unique-taste content and the social-trait text embedded in that legacy summary.
- The agent behavior prompt and candidate lists are unchanged across the four conditions; only the specified profile input components differ.
- Raw summaries for all policies (`click_only`, `converted_then_original`, and `three_tier`) remain under `results/ablations/<condition>/runs/<run_id>/summary.csv` and are intentionally git-ignored.
