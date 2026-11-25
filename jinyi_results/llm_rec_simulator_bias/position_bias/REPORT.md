# Agent4Rec and SimUSER randomized position-bias results

This is the single results document for the position-permutation experiment. It is generated from analyzer outputs; do not transcribe values manually.

## Inputs and completion status

- Vanilla summary: [vanilla_summary.json](vanilla_summary.json)
- Randomized summary, seed 20261121: [s20261121/summary.json](s20261121/summary.json)
- Randomized summary, seed 20261122: [s20261122/summary.json](s20261122/summary.json)
- Randomized summary, seed 20261123: [s20261123/summary.json](s20261123/summary.json)
- Randomized summary, seed pooled: [pooled_summary.json](pooled_summary.json)
- Each included summary contains exactly 1,000 Agent4Rec users and 1,000 SimUSER users.
- Simulator-specific audits must be passed before this report is treated as final.

## Main conclusion

- **Agent4Rec, seed 20261121:** Causal front-position effect detected (monotonic position curve).
- **SimUSER, seed 20261121:** Causal front-position effect detected (non-monotonic position curve).
- **Agent4Rec, seed 20261122:** Causal front-position effect detected (monotonic position curve).
- **SimUSER, seed 20261122:** Causal front-position effect detected (non-monotonic position curve).
- **Agent4Rec, seed 20261123:** Causal front-position effect detected (monotonic position curve).
- **SimUSER, seed 20261123:** Causal front-position effect detected (non-monotonic position curve).
- **Agent4Rec, seed pooled:** Causal front-position effect detected (monotonic position curve).
- **SimUSER, seed pooled:** Causal front-position effect detected (non-monotonic position curve).

The vanilla rows are descriptive associations. Only randomized rows support causal claims about displayed position.

## Selection rate by displayed position

| Simulator | Run | Users | Pages | Position 1 | Position 2 | Position 3 | Position 4 |
|---|---|---:|---:|---:|---:|---:|---:|
| Agent4Rec | Vanilla, original order | 1,000 | 3,117 | 44.08% | 39.75% | 35.61% | 33.01% |
| SimUSER | Vanilla, original order | 1,000 | 5,000 | 70.28% | 63.62% | 60.94% | 63.80% |
| Agent4Rec | Random order, seed 20261121 | 1,000 | 3,205 | 43.00% | 39.84% | 36.91% | 33.54% |
| SimUSER | Random order, seed 20261121 | 1,000 | 5,000 | 70.16% | 64.14% | 62.62% | 64.04% |
| Agent4Rec | Random order, seed 20261122 | 1,000 | 3,271 | 43.01% | 38.80% | 36.41% | 34.97% |
| SimUSER | Random order, seed 20261122 | 1,000 | 5,000 | 70.02% | 63.24% | 61.60% | 65.06% |
| Agent4Rec | Random order, seed 20261123 | 1,000 | 3,213 | 42.48% | 42.08% | 35.98% | 33.83% |
| SimUSER | Random order, seed 20261123 | 1,000 | 5,000 | 69.96% | 63.72% | 62.04% | 64.58% |
| Agent4Rec | Random order, pooled 3 seeds | 1,000 | 9,689 | 42.83% | 40.23% | 36.43% | 34.12% |
| SimUSER | Random order, pooled 3 seeds | 1,000 | 15,000 | 70.05% | 63.70% | 62.09% | 64.56% |

## Effect summaries

| Simulator | Run | P1−P4 (95% CI) | P1/P4 (95% CI) | Mean selected position (95% CI) | Trend p | Adjusted OR per step (95% CI; p) | Interpretation |
|---|---|---|---|---|---:|---|---|
| Agent4Rec | Vanilla, original order | 0.1107 [0.0902, 0.1317] | 1.335 [1.264, 1.414] | 2.378 [2.355, 2.399] | `8.09e-22` | 0.863 [0.838, 0.889]; `p=2.81e-22` | Strong monotonic association; fixed relevance order prevents causal attribution. |
| SimUSER | Vanilla, original order | 0.0648 [0.0474, 0.0826] | 1.102 [1.073, 1.132] | 2.457 [2.446, 2.468] | `2.55e-13` | 0.918 [0.895, 0.942]; `p=4.84e-11` | Front-position association is present but non-monotonic; fixed order prevents causal attribution. |
| Agent4Rec | Random order, seed 20261121 | 0.0945 [0.0729, 0.1158] | 1.282 [1.210, 1.360] | 2.398 [2.375, 2.420] | `3.69e-16` | 0.872 [0.846, 0.899]; `p=1.17e-18` | Causal front-position effect detected (monotonic position curve). |
| SimUSER | Random order, seed 20261121 | 0.0612 [0.0444, 0.0786] | 1.096 [1.068, 1.125] | 2.462 [2.451, 2.472] | `4.1e-11` | 0.912 [0.889, 0.934]; `p=2.18e-13` | Causal front-position effect detected (non-monotonic position curve). |
| Agent4Rec | Random order, seed 20261122 | 0.0804 [0.0592, 0.1018] | 1.230 [1.164, 1.303] | 2.413 [2.391, 2.435] | `3.11e-12` | 0.894 [0.867, 0.921]; `p=1.9e-13` | Causal front-position effect detected (monotonic position curve). |
| SimUSER | Random order, seed 20261122 | 0.0496 [0.0324, 0.0664] | 1.076 [1.049, 1.104] | 2.468 [2.458, 2.479] | `4.36e-08` | 0.929 [0.907, 0.952]; `p=4.08e-09` | Causal front-position effect detected (non-monotonic position curve). |
| Agent4Rec | Random order, seed 20261123 | 0.0865 [0.0644, 0.1096] | 1.256 [1.184, 1.338] | 2.396 [2.373, 2.419] | `7.05e-17` | 0.871 [0.844, 0.899]; `p=7.86e-18` | Causal front-position effect detected (monotonic position curve). |
| SimUSER | Random order, seed 20261123 | 0.0538 [0.0366, 0.0714] | 1.083 [1.056, 1.112] | 2.466 [2.455, 2.476] | `3.42e-09` | 0.924 [0.902, 0.947]; `p=2.54e-10` | Causal front-position effect detected (non-monotonic position curve). |
| Agent4Rec | Random order, pooled 3 seeds | 0.0871 [0.0737, 0.1002] | 1.255 [1.210, 1.304] | 2.403 [2.388, 2.417] | `8.5e-42` | 0.879 [0.863, 0.896]; `p=6.44e-41` | Causal front-position effect detected (monotonic position curve). |
| SimUSER | Random order, pooled 3 seeds | 0.0549 [0.0445, 0.0650] | 1.085 [1.068, 1.101] | 2.465 [2.459, 2.471] | `2.94e-25` | 0.922 [0.908, 0.935]; `p=6.65e-28` | Causal front-position effect detected (non-monotonic position curve). |

## Prespecified decision rule

A randomized run is labeled as a causal front-position effect only when all three conditions hold:

1. the user-cluster bootstrap 95% CI for P1−P4 is entirely above 0;
2. the user-cluster bootstrap 95% CI for P1/P4 is entirely above 1; and
3. the user-cluster-robust adjusted odds-ratio 95% CI is entirely below 1.

A significant but non-monotonic position curve is reported as non-monotonic rather than collapsed into a generic bias label. The adjusted model controls for log item train degree, held-out ground-truth membership, and page fixed effects.
Pooled rows combine observed exposures across seeds, not three independent user panels. The user bootstrap resamples each user's entire three-seed record; adjusted logistic inference clusters by user across seeds and adds seed fixed effects. Rate-table Wilson intervals and naive trend/chi-square p-values are descriptive; causal decisions use the user-cluster bootstrap and cluster-robust adjusted model. Full sessions include condition-dependent page reach. Conclusions apply to these simulators and settings, not human behavior.

## Metric provenance

- Collins et al. (2018), *A Study of Position Bias in Digital Library Recommender Systems*: randomized order, rank-level CTR, and chi-square testing. <https://arxiv.org/abs/1802.06565>
- Joachims, Swaminathan, and Schnabel (2017), *Unbiased Learning-to-Rank with Biased Feedback*: randomized interventions for position propensity identification. <https://www.cs.cornell.edu/~schnabts/downloads/joachims2017ltr.pdf>
- Bito, Ren, and He (2025), *Evaluating Position Bias in Large Language Model Recommendations*: repeated shuffled/reversed candidate orders. <https://arxiv.org/abs/2508.02020>
- Peláez-González, Herrera, and Herrera-Poyatos (2026), *Statistical Detection of Positional Bias in LLM-Based Recommender Systems*: permutation-based position distributions and query-level bootstrap uncertainty. <https://arxiv.org/abs/2610.37962>

## Baseline Provenance

Vanilla comparison uses the existing archived analysis/position_bias/summary.json (1,000 users per simulator). The vanilla SimUSER raw-run directory is absent locally, so its baseline cannot be independently re-audited here; no baseline was regenerated or substituted.
