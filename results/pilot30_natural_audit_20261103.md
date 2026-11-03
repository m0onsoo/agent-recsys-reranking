# Naturalized-profile 30-user rerun audit

Job: `13691697`  
Run: `results/pilot30_natural/runs/20261103_020258_f565e53509`  
Comparison run: job `13691396`, `results/pilot30/runs/20261103_013145_2ef39d8dda`

## Experimental control

The rerun deliberately reused the exact 30-user panel, profile evidence, precomputed
candidate slates, model list, behavior prompts, GPT-4o-mini alias, and runtime settings.
The two saved configurations differ only in `output_root`. The code change affects the
profile payload rendered immediately before the behavior request:

- ML-1M age, gender, and occupation codes are mapped to readable labels.
- structured TASTE-REASON evidence is rendered once as an `Unique tastes: ...` string.
- Activity, Conformity, and Diversity levels are rendered once with the established
  pre-migration labels and descriptions as a `Social traits: ...` string.
- interaction-history field order remains `title`, `release_year`, `genres`, followed
  by detailed metadata.

Input hashes:

| Input | SHA-256 |
|---|---|
| `data/panels/users_30_from_1000_seed42.csv` | `30cebfbd33d5ca7391e9ef2fa680fee712c85aba58b5d3c66458134d1561c03c` |
| `artifacts/profiles/pilot30_ours_all_v2/profiles.jsonl` | `50e8a78fddfefd19759c922860d0abd26526c9e1c1b791b2adab289b647d799c` |
| `data/derived/ml1m_ro_n1000_seed42/candidates.jsonl` | `abdb5bdb26c8695d1f796258a08180ab73f21a09974dbd5758fca5a3e123e738` |

## Payload audit

All 30 rendered profiles passed the following checks:

- every age and gender is a known readable ML-1M label;
- no occupation remains a numeric code;
- every `unique_tastes` value is one string beginning with `Unique tastes:`;
- every `social_traits` value is one string beginning with
  `Social traits: activity is`;
- no structured taste/reason object is duplicated in the behavior payload.

For user 184, the rendered demographic value is:

```json
{"age": "25-34", "gender": "female", "occupation": "other or not specified"}
```

Every one of the 89 successful action rows has a `profile_hash` equal to the current
rendered payload and a `candidate_hash` equal to the committed bundle slate.

## Run integrity and generated files

The run completed 89 of 90 expected model-user cases. Both the old and new runs failed
on exactly `(LightGCN, user 849)` because the click response selected an item outside
the permitted slate. Their successful case sets are therefore identical, and all
baseline metrics match exactly.

| File | Data rows | Purpose |
|---|---:|---|
| `actions.jsonl` | 89 | durable click/conversion outcomes |
| `calls.jsonl` | 178 | successful click and conversion call records |
| `failures.jsonl` | 1 | terminal invalid-output record |
| `rankings.jsonl` | 89 | all deterministic policy rankings per case |
| `per_user_metrics.csv` | 356 | 89 cases x 4 ranking stages |
| `summary.csv` | 12 | 3 models x 4 ranking stages |
| `rating_stratified_metrics.csv` | 876 | per-user metrics by held-out rating stratum |
| `config.yaml` | n/a | exact effective configuration |
| `run_manifest.json` | n/a | completion, cost, bundle, and prompt hashes |

The behavior-call cost recorded by the run is `$0.1176822`. No new profile file was
generated in this controlled rerun; the earlier profile evidence was reused by design.

## Performance compared with the pre-fix 30-user run

Because both runs contain the same 89 successful cases, the following are direct
aggregate comparisons. `Delta vs old` is new minus job `13691396`.

| Policy | Model | New Recall@10 | Delta vs old | New NDCG@10 | Delta vs old |
|---|---|---:|---:|---:|---:|
| converted then original | MF | 0.185784 | +0.000000 | 0.226524 | +0.006243 |
| converted then original | LightGCN | 0.218092 | +0.000000 | 0.269048 | +0.000000 |
| converted then original | MultiVAE | 0.194633 | -0.005500 | 0.236507 | -0.015798 |
| three tier | MF | 0.191935 | +0.006812 | 0.227987 | +0.009055 |
| three tier | LightGCN | 0.213745 | -0.004454 | 0.270307 | -0.006198 |
| three tier | MultiVAE | 0.199059 | +0.016364 | 0.243892 | +0.009533 |
| click only | MF | 0.191935 | +0.006812 | 0.241996 | +0.003815 |
| click only | LightGCN | 0.213745 | -0.004454 | 0.292993 | -0.007179 |
| click only | MultiVAE | 0.199059 | +0.016364 | 0.274772 | +0.016458 |

Under the default `converted_then_original` policy, the naturalized input improves MF
NDCG, leaves both LightGCN metrics unchanged, and reduces MultiVAE Recall and NDCG in
this small pilot. Under `click_only` and `three_tier`, MF and MultiVAE mostly improve
while LightGCN declines. These directions are exploratory at n=30 and should not be
treated as stable population estimates.

Behavior outputs changed despite some identical aggregate metrics: click sets changed
in 23/30 MF, 17/29 LightGCN, and 27/30 MultiVAE cases; conversion sets changed in 8/30,
2/29, and 7/30 cases respectively. This is compatible with both the input-format change
and the fact that the live GPT-4o-mini alias is not revision- or seed-pinned.
