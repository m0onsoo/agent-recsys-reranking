# Pilot-30 social-trait behavior prompt audit

Job: `13697945`

Run: `results/pilot30_social_traits/runs/20261103_121912_4c69226b0f`

Comparison: job `13691697`, `results/pilot30_natural/runs/20261103_020258_f565e53509`

## Integrity

- Social-trait run: 30 users x 3 models = 90/90 successful cases, zero failures.
- Estimated API cost: $0.1228062.
- Bundle, selected users, profile artifact, model alias, and profile components are
  identical to the comparison run. The behavior prompt is the intended difference.
- The comparison run has one failed LightGCN case. All direct old/new comparisons
  below therefore use the 89 common model-user cases (MF 30, LightGCN 29, MultiVAE 30).

## Default-policy performance

`converted_then_original` is the default policy. Delta vs old v2 is paired over common
cases; delta vs backbone is from the new run's complete summary.

| Model | New Recall@10 | New NDCG@10 | Recall delta vs old v2 | NDCG delta vs old v2 | Recall delta vs backbone | NDCG delta vs backbone |
|---|---:|---:|---:|---:|---:|---:|
| MF | 0.192397 | 0.232433 | +0.006614 | +0.005908 | +0.000000 | -0.008613 |
| LightGCN | 0.209091 | 0.275205 | -0.004926 | +0.011852 | -0.002219 | -0.013900 |
| MultiVAE | 0.195966 | 0.248537 | +0.001333 | +0.012031 | +0.001333 | -0.024294 |

The strengthened prompt improves paired conversion-policy NDCG over old v2 for all
three backbones, while Recall is mixed. It still remains below the sampled backbone
NDCG for all three models, so this pilot does not establish a ranking improvement.

## Action changes

| Statistic (89 common cases) | Old v2 | Social-trait prompt |
|---|---:|---:|
| Mean clicked movies | 5.517 | 5.213 |
| Empty-click cases | 0 | 0 |
| Mean converted movies | 1.000 | 1.000 |
| Empty-conversion cases | 0 | 0 |
| Exact click-set agreement | — | 28/89 |
| Exact conversion-set agreement | — | 65/89 |
| Cases whose observable text mentions rating | 89/89 | 86/89 |
| Cases whose observable text explicitly mentions a trait/label | 0/89 | 5/89 |

Explicit trait-name mentions are not required for adherence; the behavioral aggregates
below are more informative. However, always converting exactly one movie means the
conversion-stage activity threshold did not create abstention behavior.

## Trait-aligned behavior checks

These are descriptive group comparisons, not causal estimates. Each user contributes
one case per available backbone, and trait groups can differ in histories and candidate
slates. A counterfactual trait-flip experiment is required to isolate prompt adherence.

### Activity

| Level | Cases | Old mean clicks | New mean clicks |
|---|---:|---:|---:|
| 1: infrequent | 53 | 6.019 | 5.415 |
| 2: occasional | 33 | 4.758 | 4.909 |
| 3: enthusiast | 3 | 5.000 | 5.000 |

The prompt reduces clicks most for infrequent viewers, narrowing the level-1/level-2
gap. The ordering is still opposite the intended monotonic relationship, and level 3
has only three cases. Activity adherence is therefore not established.

### Diversity

| Level | Cases | New unique genres among clicks | New fraction of clicks containing a genre absent from the visible 10-item history |
|---|---:|---:|---:|
| 1: selective | 21 | 4.857 | 0.165 |
| 2: niche explorer | 39 | 5.487 | 0.227 |
| 3: broad explorer | 29 | 6.241 | 0.237 |

Both measurements increase in the intended direction. Unique-genre breadth was already
ordered similarly under old v2 (4.905, 5.487, 6.172), so the new prompt preserves and
slightly strengthens only the highest-level breadth rather than creating a new effect.

### Conformity

| Level | Cases | Old mean rating of clicked movies | New mean rating of clicked movies |
|---|---:|---:|---:|
| 1: dedicated follower | 21 | 4.240 | 4.228 |
| 2: balanced evaluator | 47 | 4.044 | 4.018 |
| 3: independent critic | 21 | 4.030 | 3.999 |

The desired follower-to-independent ordering is present, but it was already present in
old v2. Because candidate slates differ across users, these raw group means alone do not
prove that the new conformity instruction caused the pattern.

## Conclusion and next diagnostic

The prompt causes substantial action changes and improves paired default-policy NDCG
relative to old v2, but the evidence for trait adherence is uneven: diversity is aligned,
conformity is directionally aligned but largely pre-existing, and activity is not yet
monotonic. The clean next test is a no-API-profile-regeneration counterfactual: reuse the
same user, profile, and candidate slate; change exactly one stored trait level at a time;
then measure within-case changes in click count, genre novelty, and rating sensitivity.
