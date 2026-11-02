# Legacy-parity no-demographics reproduction

Date: 2026-11-02  
Job: `13676184_1`  
Run: `20261102_132746_0e0714dc10`  
Users: 50  
Backbones: MF, LightGCN, vanilla MultiVAE  
LLM: `gpt-4o-mini`, temperature 0  
Condition: history + legacy combined persona, no demographics  
Policy: converted item first, all other items in original backbone order

## Compatibility fixes

Commits `ed2efa1` and `c66bf34` restore the original implementation's:

- stripped prompt-template rendering;
- exact full-slate conversion-context instruction;
- response schema and retry schema;
- short-sentence validation and retry instructions;
- strict runtime response shape;
- explicit `unknown` and empty-array values for missing detail metadata.

The audit established:

- 50/50 generated profile JSON payloads equal;
- 150/150 click user JSON payloads equal;
- 150/150 candidate lists and orders equal;
- all candidate detail records equal after explicit default restoration;
- normal click, click retry, normal conversion, and conversion retry HTTP request bytes equal;
- baseline, held-out labels, reranking, and metric calculations equal;
- replaying original-code actions through the migrated evaluator reproduces the original metrics to floating-point precision.

Four frozen request SHA-256 values are enforced by `tests/test_legacy_request_parity.py`.

## Completion

- Completed cases: 150/150
- API calls: 300
- Validation retries: 0
- Final failures: 0
- Recorded cost: USD 0.1877124

## Final results

| Backbone | Baseline R/N | Converted-first R/N | Relative R/N change |
|---|---:|---:|---:|
| MF | 0.140819 / 0.222189 | 0.145667 / 0.226621 | +3.443% / +1.995% |
| LightGCN | 0.183144 / 0.260781 | 0.186478 / 0.267188 | +1.820% / +2.457% |
| MultiVAE | 0.185796 / 0.254771 | 0.184926 / 0.247814 | -0.468% / -2.731% |

## Comparison

| Backbone | Earlier reported | Fresh original code | Final legacy-parity migration |
|---|---:|---:|---:|
| MF | 0.155263 / 0.232017 | 0.153350 / 0.240803 | 0.145667 / 0.226621 |
| LightGCN | 0.188296 / 0.279746 | 0.189407 / 0.274787 | 0.186478 / 0.267188 |
| MultiVAE | 0.186272 / 0.265941 | 0.189606 / 0.251821 | 0.184926 / 0.247814 |

The earlier reported row is composite: MF and LightGCN come from the 2026-10-25 no-demographics run, while vanilla MultiVAE comes from its 2026-10-29 replacement run.

## Run-to-run behavior agreement

Compared with the fresh original-code no-cache run:

| Backbone | Exact click set | Same converted set | Mean click-set Jaccard |
|---|---:|---:|---:|
| MF | 6/50 | 25/50 | 0.644 |
| LightGCN | 5/50 | 29/50 | 0.638 |
| MultiVAE | 4/50 | 27/50 | 0.616 |

Despite byte-identical request construction, only about half of the conversion selections and very few complete click sets repeat. This is direct evidence of API run-to-run behavioral variation at temperature zero.

Paired 50-user bootstrap 95% intervals for the final absolute conversion-reranking deltas include zero (or touch zero) for all six model-metric combinations. The individual 50-user point estimates should therefore be treated as exploratory.

## Conclusion

The migrated request and evaluation pipeline now matches the original implementation under the audited legacy protocol, but the earlier 50-user point estimates do not reproduce in a new live LLM sample. The remaining observed difference is not evidence of a checkpoint or post-processing mismatch. Stable conclusions require a larger panel and, ideally, repeated LLM samples or a frozen-response replay evaluation.
