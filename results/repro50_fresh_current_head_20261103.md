# Fresh GPT-4o-mini repro50 run (2026-11-03)

Slurm array: `13691126_[0-3]`

Every condition completed 150/150 model-user cases with zero final failures. Values
below are the relative changes from each unchanged backbone for the primary
`converted_then_original` policy.

| Condition | Backbone | Recall@10 change | NDCG@10 change |
|---|---|---:|---:|
| full | MF | +3.564% | +9.854% |
| full | LightGCN | -0.173% | +0.300% |
| full | MultiVAE | -0.468% | -3.206% |
| w/o demographics | MF | +5.626% | +4.198% |
| w/o demographics | LightGCN | +2.427% | +3.976% |
| w/o demographics | MultiVAE | +1.326% | +0.416% |
| w/o persona | MF | +3.156% | -3.185% |
| w/o persona | LightGCN | +0.442% | +1.349% |
| w/o persona | MultiVAE | -2.486% | +0.486% |
| w/o interaction history | MF | +7.546% | +5.782% |
| w/o interaction history | LightGCN | -0.396% | -3.233% |
| w/o interaction history | MultiVAE | -1.915% | -7.200% |

The broad earlier trends recur: removing demographics is positive across all three
backbones in this run, while removing history harms LightGCN and MultiVAE. Exact
effect sizes remain unstable at 50 users because live GPT-4o-mini responses are not
deterministic even with byte-equivalent requests and temperature zero.
