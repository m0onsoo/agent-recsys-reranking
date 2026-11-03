# GPT-4o-mini reranking results: repro50 and pilot30

Date: 2026-11-03

## Interpretation boundary

These runs must not be pooled or compared as if they used the same sample and input
protocol. Job `13691336` uses the fixed 50-user reproduction sample and the
`legacy_combined` profile protocol. Job `13691396` uses a seed-42 subset of the fixed
1,000-user panel and the new `separated` protocol intended for the 1,000-user study.
The pilot is an end-to-end scalability check, not a stable performance estimate.

Both jobs use GPT-4o-mini, prompt version `behavior-motive-assessment-v2`, candidate
size 20, and Top-10 evaluation. All changes below are measured against each model's
sampled backbone baseline on the same successfully completed cases.

## Job 13691336: fixed 50-user ablation reproduction

The table reports the default `converted_then_original` policy. `no_persona` has one
failed MF case, so its MF row contains 49 users; every other row contains 50 users.

| Input condition | Model | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---:|---:|---:|---:|
| full | MF | 0.1508 | 0.2345 | +0.0100 (+7.09%) | +0.0123 (+5.53%) |
| full | LightGCN | 0.1877 | 0.2629 | +0.0046 (+2.50%) | +0.0021 (+0.81%) |
| full | MultiVAE | 0.1758 | 0.2377 | -0.0100 (-5.40%) | -0.0170 (-6.69%) |
| w/o demographics | MF | 0.1523 | 0.2330 | +0.0115 (+8.14%) | +0.0108 (+4.86%) |
| w/o demographics | LightGCN | 0.1825 | 0.2544 | -0.0007 (-0.37%) | -0.0064 (-2.45%) |
| w/o demographics | MultiVAE | 0.1850 | 0.2327 | -0.0008 (-0.42%) | -0.0221 (-8.68%) |
| w/o persona | MF | 0.1491 | 0.2295 | +0.0086 (+6.09%) | +0.0101 (+4.61%) |
| w/o persona | LightGCN | 0.1860 | 0.2517 | +0.0028 (+1.54%) | -0.0091 (-3.49%) |
| w/o persona | MultiVAE | 0.1700 | 0.2104 | -0.0158 (-8.52%) | -0.0443 (-17.40%) |
| w/o interaction history | MF | 0.1497 | 0.2320 | +0.0089 (+6.32%) | +0.0098 (+4.43%) |
| w/o interaction history | LightGCN | 0.1852 | 0.2629 | +0.0020 (+1.10%) | +0.0021 (+0.80%) |
| w/o interaction history | MultiVAE | 0.1755 | 0.2355 | -0.0103 (-5.54%) | -0.0192 (-7.55%) |

The reproduction trend is model-dependent: the default conversion policy consistently
helps MF, is small or mixed for LightGCN, and generally hurts MultiVAE. Removing the
persona produces the largest MultiVAE degradation in this run.

## Job 13691396: 30-user fixed-panel pilot

The full pipeline completed 89 of 90 model-user cases. LightGCN user 849 was excluded
because the LLM selected an item outside the permitted candidate set. MF and MultiVAE
therefore contain 30 users, while LightGCN contains 29. Estimated behavior-call cost
was $0.1261. Profile-generation cost is not included in that estimate and the current
profile generator does not persist a separate cost total.

| Policy | Model | Recall@10 | NDCG@10 | Recall change | NDCG change |
|---|---|---:|---:|---:|---:|
| converted then original | MF | 0.1858 | 0.2203 | -0.0066 (-3.44%) | -0.0208 (-8.61%) |
| converted then original | LightGCN | 0.2181 | 0.2690 | +0.0026 (+1.22%) | -0.0252 (-8.58%) |
| converted then original | MultiVAE | 0.2001 | 0.2523 | +0.0055 (+2.83%) | -0.0205 (-7.52%) |
| click only | MF | 0.1851 | 0.2382 | -0.0073 (-3.78%) | -0.0029 (-1.19%) |
| click only | LightGCN | 0.2182 | 0.3002 | +0.0027 (+1.27%) | +0.0059 (+2.00%) |
| click only | MultiVAE | 0.1827 | 0.2583 | -0.0119 (-6.13%) | -0.0145 (-5.32%) |
| three tier | MF | 0.1851 | 0.2189 | -0.0073 (-3.78%) | -0.0221 (-9.17%) |
| three tier | LightGCN | 0.2182 | 0.2765 | +0.0027 (+1.27%) | -0.0178 (-6.04%) |
| three tier | MultiVAE | 0.1827 | 0.2344 | -0.0119 (-6.13%) | -0.0385 (-14.10%) |

The pilot confirms that fixed-user selection, profile generation, all three backbone
slates, two-stage agent behavior, deterministic policy post-processing, and metric
tables work end to end. Its metric directions are unstable across models and metrics,
which is expected for a small conditioned sample. The 1,000-user run should be treated
as the first inferential evaluation of the new separated-input pipeline.

## Source artifacts

- 50-user summaries: `results/ablations/{full,no_demographics,no_persona,no_interaction_history}/runs/*/summary.csv`
- 30-user summary: `results/pilot30/runs/20261103_013145_2ef39d8dda/summary.csv`
- 30-user actions: `results/pilot30/runs/20261103_013145_2ef39d8dda/actions.jsonl`
- 30-user fixed panel: `data/panels/users_30_from_1000_seed42.csv`

