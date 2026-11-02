# GPT-4o-mini 50-user legacy reproduction (2026-11-02)

## Run identity

- New run: `20261102_005259_a151fe2513`
- Cases: 50 users x MF, LightGCN, vanilla MultiVAE = 150
- Profile components: history and full v3 persona; demographics excluded
- Completed: 150; failures: 0
- API calls: 300 successful stage calls; no validation retries
- Estimated cost: $0.1870209
- Input audit: the legacy and new user-153 profile, candidates, and serialized click JSON payload are exactly equal.

The MF and LightGCN references are the fresh legacy no-demographics run
`20261027_1512_mf-lightgcn-multivae_gpt-4o-mini_e2319ed8`. MultiVAE is compared
with the later vanilla-checkpoint run
`20261029_0002_multivae_gpt-4o-mini_8656a32e`.

## New aggregate metrics

| Model | Policy | Recall@10 | NDCG@10 | Change from backbone Recall | Change from backbone NDCG |
|---|---|---:|---:|---:|---:|
| MF | backbone | 0.140819 | 0.222189 | 0 | 0 |
| MF | click-only | 0.152931 | 0.220723 | +0.012112 | -0.001466 |
| MF | conversion-only | 0.152334 | 0.230099 | +0.011515 | +0.007910 |
| MF | three-tier | 0.152931 | 0.222616 | +0.012112 | +0.000427 |
| LightGCN | backbone | 0.183144 | 0.260781 | 0 | 0 |
| LightGCN | click-only | 0.189606 | 0.264015 | +0.006462 | +0.003234 |
| LightGCN | conversion-only | 0.187589 | 0.268378 | +0.004444 | +0.007597 |
| LightGCN | three-tier | 0.189606 | 0.269205 | +0.006462 | +0.008424 |
| MultiVAE | backbone | 0.185796 | 0.254771 | 0 | 0 |
| MultiVAE | click-only | 0.180202 | 0.244305 | -0.005594 | -0.010466 |
| MultiVAE | conversion-only | 0.184926 | 0.236588 | -0.000870 | -0.018183 |
| MultiVAE | three-tier | 0.180202 | 0.233087 | -0.005594 | -0.021684 |

## Reproduction differences

| Model | Policy | Recall delta vs legacy | NDCG delta vs legacy |
|---|---|---:|---:|
| MF | click-only | +0.000020 | -0.002184 |
| MF | conversion-only | -0.005152 | -0.013202 |
| LightGCN | click-only | +0.000696 | +0.002653 |
| LightGCN | conversion-only | -0.000707 | -0.008260 |
| MultiVAE | click-only | +0.003680 | -0.001761 |
| MultiVAE | conversion-only | -0.001346 | -0.029353 |

Backbone metrics reproduce to floating-point precision. Click-only metrics are close.
Conversion results are less stable: exact converted-item agreement is 70% for MF,
66% for LightGCN, and 62% for MultiVAE. Mean click-set Jaccard is respectively
0.651, 0.617, and 0.603. This is consistent with GPT-4o-mini serving nondeterminism
despite temperature zero and byte-equivalent inputs.

Paired user bootstrap 95% intervals for conversion NDCG difference are:

- MF: -0.01320, CI [-0.02929, -0.00127]
- LightGCN: -0.00826, CI [-0.02608, +0.01030]
- MultiVAE: -0.02935, CI [-0.05725, -0.00705]

The current replication supports environment correctness but shows that a single
LLM run is insufficient for strong claims about conversion-reranking effect size.
Use repeated LLM seeds/runs or paired uncertainty estimates for the 1,000-user study.
