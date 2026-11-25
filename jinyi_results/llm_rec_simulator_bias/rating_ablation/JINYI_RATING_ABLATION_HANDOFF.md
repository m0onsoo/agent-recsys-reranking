# Agent4Rec rating-cue ablation and activity crossover: experiment handoff for Jinyi

## Goal and current status

The next experiment tests whether the explicit per-movie `History ratings` value shown to Agent4Rec causes the simulator to select systematically higher-rated and more popular movies. We repeat that direct shown-versus-hidden comparison with and without the activity-frequency persona, producing four controlled conditions:

| Activity persona in prompt | Item historical rating in prompt | Status | Run directory |
|---|---|---|---|
| Included | Included | Complete | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_batch4_from200` |
| Excluded | Included | Complete | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_no_activity` |
| Included | Excluded | Complete; audited | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_no_item_rating` |
| Excluded | Excluded | Complete; audited | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_no_activity_no_item_rating` |

Run all 1,000 users for up to five pages (four items per page). Do not substitute a smaller panel or a one-page run. The completed conditions used GPT-6 Luna, seed 101, temperature 0, no reasoning effort, and the same cached LightGCN ranking. Every new condition must preserve all of these settings.

This is a rating-**presentation** ablation. The movie's historical mean rating remains available in the dataset for evaluation but must not appear in the item text sent to the LLM. Conformity and diversity personas remain unchanged. The activity-included comparison is the primary test because it changes only the rating cue from the reproduced vanilla condition. The activity-excluded comparison is a robustness check, not a test that activity moderates rating sensitivity.

The separate **activity crossover** tests whether the injected activity description itself causes the group differences. It swaps only the extreme prompt labels: original Infrequent (`1`) receives the Frequent (`3`) description, original Frequent receives the Infrequent description, and Occasional (`2`) remains unchanged as a negative-control group. Original group labels are retained for analysis.

| Original activity mapping | Prompt activity mapping | Item rating shown? | Status | Run directory |
|---|---|---|---|---|
| Identity | Identity | Yes | Complete vanilla reference | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_batch4_from200` |
| 1↔3, 2 unchanged | Swapped extremes | Yes | Complete; audited | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_activity_swap` |
| Identity | Identity | No | Complete; audited | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_no_item_rating` |
| 1↔3, 2 unchanged | Swapped extremes | No | Complete; audited | `storage/ml-1m/LightGCN/agent4rec_lightgcn_luna_1000_5pages_activity_swap_no_item_rating` |

## Code and vanilla-safety contract

The new CLI argument is:

```text
--item_rating_mode {included,excluded}
```

`included` is the default. `--exclude_item_rating` is an alias for `--item_rating_mode excluded`.

The activity crossover uses:

```text
--activity_persona_transform swap_extremes
```

Its default is `identity`. The transform is valid only with `--activity_persona_mode included`.

The implementation is deliberately opt-in:

- Default `included` produces the legacy recommendation string byte-for-byte and does not add a new manifest or behavior field.
- Only `excluded` removes the `History ratings: <value>` fragment from recommended-item, forced-validation, and advertisement presentation text.
- Only `excluded` records `item_rating_mode: excluded` in `run_manifest.json` and behavior records.
- Existing vanilla runs therefore retain resume compatibility and output structure. Never change the default when running the original reproduction.

Regression coverage is in `tests/test_item_rating_mode.py` and `tests/test_activity_persona_transform.py`. Before submitting jobs, run:

```bash
python -m pytest -q tests/test_item_rating_mode.py tests/test_activity_persona_transform.py
```

If `pytest` is unavailable, install it in the experiment environment; do not change application dependencies merely to bypass the test.

## Required ranking artifact

All new runs must consume the exact cached ranking tracked in this repository at
`artifacts/rankings/full_rankings_1000.npy`. It is about 26 MB and is intentionally
versioned as an immutable experiment input.

```text
filename: full_rankings_1000.npy
SHA-256: 906e830fc56652cf21a9f2818cd3fa571f9b38d7ff9909f4e11ae72cd15e89d1
```

Do not regenerate recommendations independently for each condition. Sharing this array makes the underlying ranked candidate list identical. Run `python scripts/verify_artifacts.py` from the repository root before submitting a job. With a cached ranking, these simulations are CPU/API workloads; no GPU request is necessary.

The `.npy` file stores the **complete ordered item-ID list for each user**, not model scores. The simulation assigns row `u` to avatar `u` for users `0..999` and slices that row into consecutive groups of four for pages 1–5. There is no checkpoint inference, sampling, or re-ranking after the file is loaded. Therefore a different Python/CUDA environment cannot change the candidate order.

The artifact alone is not sufficient if the item-ID mapping or execution settings have been changed. Use the repository revision containing rating-ablation commit `a9fd38b` and activity-crossover commit `9d678d8` (or a descendant with no changes to ranking loading, dataset mapping, or page generation), together with the tracked `datasets/ml-1m` files from that revision. The Slurm templates verify SHA-256 hashes for the ranking, train/valid/test splits, movie metadata, personas, and activity statistics before making an API call. The loader also rejects an array whose user/item dimensions do not match the dataset. The templates fix and record the following settings in `run_manifest.json`:

```text
dataset=ml-1m, modeltype=LightGCN, n_avatars=1000
items_per_page=4, max_pages=5, seed=101
llm_model=gpt-6-luna, reasoning_effort=none, temperature=0.0
no advertisements, original ranking order
```

Before interpreting results, compare every `recommended_id` in the four-condition common prefix. The required mismatch count is zero. This final output-level check catches any mapping or configuration mistake even if the input hash passed.

## Submission commands

The parameterized Slurm template is `Agent4Rec/slurm/run_1000_luna_no_item_rating.sbatch`. Adjust only the site-specific `#SBATCH --account`, partition, module, and virtual-environment lines if Jinyi's cluster differs. Put `OPENAI_API_KEY=...` in the Git-ignored `Agent4Rec/.env` file. Run the submission commands below from `Agent4Rec/`.

Submit the activity-included/rating-hidden condition first:

```bash
sbatch --export=ALL,ACTIVITY_PERSONA_MODE=included,RANKINGS_PATH="$(pwd)/../artifacts/rankings/full_rankings_1000.npy" \
  slurm/run_1000_luna_no_item_rating.sbatch
```

After it finishes cleanly, submit the no-activity/rating-hidden condition:

```bash
sbatch --export=ALL,ACTIVITY_PERSONA_MODE=excluded,RANKINGS_PATH="$(pwd)/../artifacts/rankings/full_rankings_1000.npy" \
  slurm/run_1000_luna_no_item_rating.sbatch
```

Submit the activity crossover with ratings shown:

```bash
sbatch --export=ALL,ITEM_RATING_MODE=included,RANKINGS_PATH="$(pwd)/../artifacts/rankings/full_rankings_1000.npy" \
  slurm/run_1000_luna_activity_swap.sbatch
```

Submit the same crossover with ratings hidden:

```bash
sbatch --export=ALL,ITEM_RATING_MODE=excluded,RANKINGS_PATH="$(pwd)/../artifacts/rankings/full_rankings_1000.npy" \
  slurm/run_1000_luna_activity_swap.sbatch
```

Both Slurm templates use `--resume`, two concurrent workers, batches of two, a ten-second inter-batch pause, retry/error status recording, ranking/data hash validation, and an item-ID matching audit. Rating-hidden runs also check that `History ratings:` did not leak into recommendation logs. Re-submit the same command after interruption; completed users are preserved, and the manifest prevents resuming with a different configuration.

Acceptance criteria for every run:

1. Exactly 1,000 complete behavior files exist and `scripts/audit_item_matching.py` passes.
2. The `.status` file reports `exit_code=0`.
3. The ranking and tracked-data hashes pass.
4. Every observed `recommended_id` equals the corresponding cached-ranking page slice.
5. Rating-hidden manifests contain `"item_rating_mode": "excluded"`, and their logs contain no `History ratings:` occurrence.
6. Crossover manifests contain `"activity_persona_transform": "swap_extremes"`; behavior records must show mappings `1→3`, `2→2`, and `3→1`.

## Evaluation design

### Primary estimands

Use `watch_id` as selection because Agent4Rec treats viewing as the adoption action. Report `like_id` as a secondary, stricter outcome. Compute movie popularity as **training-set item degree** only; do not use test interactions. Compute the displayed historical rating from `datasets/ml-1m/simulation/movie_detail.csv`, matching the value that was hidden or shown.

For every user and condition, calculate:

- **Selection rate:** selected impressions / displayed impressions.
- **Popularity uplift:** mean train-degree percentile of selected items minus mean train-degree percentile of displayed impressions. Percentile is preferred to raw degree because degree is heavy-tailed and its absolute scale is difficult to compare.
- **Historical-rating uplift:** mean historical rating of selected items minus mean historical rating of displayed impressions.
- **Session outcomes:** average exit page, view count/ratio, like count/ratio, and satisfaction where available.

Average Recommendation Popularity (ARP) defines popularity as the number of training ratings received by an item and averages it over recommendation lists; this is the source for our train-degree measure ([Abdollahpouri, Burke, and Mobasher, 2019, §Evaluation](https://arxiv.org/abs/1901.07555)). Our selected-minus-impression uplift is a study-specific exposure-normalized adaptation: the displayed list is the within-user baseline, and the selected list is the simulator output. It is not an original Agent4Rec metric.

Agent4Rec's native session metrics are average viewing ratio, number and ratio of likes, exit page, and satisfaction score ([Zhang et al., 2024, §3.3](https://arxiv.org/abs/2310.10108)). The paper also uses Recall@20 and NDCG@20 only when retraining and evaluating recommenders from simulated feedback ([§3.4](https://arxiv.org/abs/2310.10108)); those offline metrics are not needed for this prompt-cue ablation because no recommender is retrained.

### Identical-exposure analysis

The primary comparison must use each user's **four-condition common page prefix**:

```text
pages 1 .. min(last page in all four conditions)
```

Verify that every item ID and order in that prefix matches across all four conditions. This makes the compared impressions identical. Full-session results are still useful as total effects, but later pages mix prompt effects with condition-dependent exit/attrition and must be labeled accordingly.

Within each activity group (Infrequent, Occasional, Frequent), make two direct paired comparisons: rating shown versus hidden when the activity prompt is included, and rating shown versus hidden when the activity prompt is excluded. Report paired user-level means, the paired mean difference, 95% confidence interval, paired Cohen's dz, and raw two-sided paired-test p-value. These comparisons answer the immediate question without requiring a difference-in-differences interaction or a study-specific regression model. Conformity remains unchanged in all four runs and should be discussed as a possible remaining source of rating sensitivity, not removed or modeled unless a later analysis specifically requires it.

For the activity crossover, compare identity versus swapped prompts separately with ratings shown and hidden. Stratify by the user's **original** activity group. A prompt-driven effect should reverse the extreme groups: original Infrequent users should become more active when shown the Frequent description, while original Frequent users should become less active when shown the Infrequent description. Occasional users receive identical activity text and serve as a negative control. Apply the same full-session and identical-exposure common-prefix distinction used for the rating experiment.

## Results already available

### Ground-truth profile popularity

The groups differ before simulation, so selected degree alone must not be interpreted as an LLM effect.

| Activity group | Users | Mean train degree of user's training interactions |
|---|---:|---:|
| Infrequent | 539 | 77.0660 |
| Occasional | 352 | 65.1706 |
| Frequent | 109 | 50.8405 |

### Full-session results with ratings shown

These are total effects and include differential page reach.

| Activity group | Activity prompt | Users | Users in degree comparison | Watch rate | Impression mean degree | Watch-selected mean degree | Selected − impression degree |
|---|---|---:|---:|---:|---:|---:|---:|
| Infrequent | Included | 539 | 480 | 0.2059 | 120.6273 | 128.1351 | +7.5078 |
| Infrequent | Excluded | 539 | 531 | 0.5384 | 112.3479 | 115.8071 | +3.4592 |
| Occasional | Included | 352 | 333 | 0.3676 | 106.5355 | 114.4036 | +7.8680 |
| Occasional | Excluded | 352 | 346 | 0.6180 | 105.5687 | 109.9195 | +4.3508 |
| Frequent | Included | 109 | 108 | 0.7436 | 92.7104 | 93.7147 | +1.0042 |
| Frequent | Excluded | 109 | 108 | 0.7016 | 94.8566 | 97.7510 | +2.8944 |

`Users in degree comparison` counts users with at least one watch in that condition. Impression and selected degree means, and their difference, use that same subset so the three degree columns are arithmetically comparable. Watch rate uses all users in the group and treats zero-watch users as zero.

### Identical-exposure common-prefix results with ratings shown

All 11,896 paired impressions matched exactly between the two completed conditions. Activity text had a very large effect on how many movies were selected, while the selected-set popularity shift was much smaller.

| Activity group | Activity prompt | Users | Users in degree comparison | Watch rate | Impression mean degree | Watch-selected mean degree | Selected − impression degree |
|---|---|---:|---:|---:|---:|---:|---:|
| Infrequent | Included | 539 | 465 | 0.2063 | 120.3203 | 127.5527 | +7.2324 |
| Infrequent | Excluded | 539 | 465 | 0.5580 | 120.3203 | 124.2349 | +3.9146 |
| Occasional | Included | 352 | 329 | 0.3683 | 107.5350 | 115.6333 | +8.0983 |
| Occasional | Excluded | 352 | 329 | 0.6276 | 107.5350 | 111.9400 | +4.4050 |
| Frequent | Included | 109 | 106 | 0.7410 | 94.5792 | 95.5434 | +0.9642 |
| Frequent | Excluded | 109 | 106 | 0.7003 | 94.5792 | 97.4936 | +2.9144 |

Here `Users in degree comparison` counts users who watched at least one item in both conditions. Impression and selected means use the same paired-user subset. The identical impression means within each group confirm that the compared candidates are the same.

The historical rating cue is a plausible confound because train degree and displayed historical rating are correlated in these impressions (Pearson `r=0.5348`, Spearman `ρ=0.5428`). Conditional on selecting in both conditions, the current rating results are:

| Activity group | Impression mean rating | Selected rating: activity included | Rating uplift | Selected rating: activity excluded | Rating uplift | Included − excluded selected rating |
|---|---:|---:|---:|---:|---:|---:|
| Infrequent | 3.9442 | 4.0629 | +0.1252 | 4.0029 | +0.0652 | +0.0600 |
| Occasional | 3.8545 | 3.9531 | +0.0945 | 3.9042 | +0.0456 | +0.0489 |
| Frequent | 3.7929 | 3.7979 | +0.0078 | 3.8167 | +0.0265 | −0.0187 |

The activity-included versus excluded differences in selected rating are only `+0.0600`, `+0.0489`, and `−0.0187` on a five-point scale for the three groups. Activity text strongly changes **how many** movies are watched, but the current evidence does not show a large practical effect on the mean historical rating of the selected movies. Accordingly, activity is not the main rating-bias hypothesis. The rating-hidden runs instead test whether the explicit numerical rating cue itself explains the positive selected-versus-impression rating uplift, while the no-activity run serves as a robustness check.

## Tables to fill after the additional runs

Replace `TBD` cells only after the corresponding runs pass the acceptance checks.

### Four-way common-prefix coverage

| activity_group | users | mean_common_pages | matched_impressions | candidate_mismatches |
| --- | --- | --- | --- | --- |
| 1 | 539 | 1.929499 | 4160 | 0 |
| 2 | 352 | 3.426136 | 4824 | 0 |
| 3 | 109 | 3.788991 | 1652 | 0 |

### Full-session primary watch metrics

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 480 | 0.205898 | 2.278293 | 2.278293 | 5.842301 | 1.983302 | 94.045689 | 95.486934 | 1.441245 | 3.938684 | 4.067715 | 0.129031 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 333 | 0.367566 | 3.892045 | 3.892045 | 6.900568 | 6.056818 | 93.690463 | 94.719142 | 1.028678 | 3.854038 | 3.950029 | 0.095991 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 108 | 0.743578 | 4.761468 | 4.761468 | 8.247706 | 14.229358 | 91.609339 | 91.773639 | 0.164300 | 3.780910 | 3.787070 | 0.006160 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 503 | 0.212430 | 2.499072 | 2.499072 | 5.858998 | 2.202226 | 93.908492 | 94.969694 | 1.061203 | 3.940480 | 4.032958 | 0.092478 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 334 | 0.366832 | 3.934659 | 3.934659 | 6.971591 | 6.071023 | 93.506963 | 94.325807 | 0.818844 | 3.849015 | 3.916430 | 0.067415 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 109 | 0.772018 | 4.697248 | 4.697248 | 8.541284 | 14.550459 | 91.807616 | 91.984702 | 0.177086 | 3.784423 | 3.795143 | 0.010720 |
| full_session | shown_excluded | 1 | Infrequent | Excluded | True | Identity | watch | 539 | 531 | 0.538397 | 4.150278 | 4.150278 | 7.406308 | 9.307978 | 93.353964 | 93.946688 | 0.592725 | 3.909847 | 3.967637 | 0.057789 |
| full_session | shown_excluded | 2 | Occasional | Excluded | True | Identity | watch | 352 | 346 | 0.617969 | 4.318182 | 4.318182 | 7.875000 | 11.031250 | 93.490581 | 93.996820 | 0.506239 | 3.845416 | 3.891870 | 0.046454 |
| full_session | shown_excluded | 3 | Frequent | Excluded | True | Identity | watch | 109 | 108 | 0.701644 | 4.330275 | 4.330275 | 7.926606 | 12.394495 | 91.946468 | 92.207534 | 0.261066 | 3.790209 | 3.816569 | 0.026360 |
| full_session | R2 | 1 | Infrequent | Excluded | False | Identity | watch | 539 | 535 | 0.552381 | 4.235622 | 4.235622 | 7.625232 | 9.612245 | 93.363827 | 93.832479 | 0.468651 | 3.906613 | 3.949550 | 0.042937 |
| full_session | R2 | 2 | Occasional | Excluded | False | Identity | watch | 352 | 346 | 0.627320 | 4.312500 | 4.312500 | 7.934659 | 11.130682 | 93.582840 | 94.017762 | 0.434922 | 3.853490 | 3.884846 | 0.031356 |
| full_session | R2 | 3 | Frequent | Excluded | False | Identity | watch | 109 | 106 | 0.703020 | 4.229358 | 4.229358 | 8.174312 | 12.284404 | 91.855912 | 92.106716 | 0.250804 | 3.789572 | 3.812395 | 0.022823 |

### Four-condition common-prefix primary watch metrics

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 459 | 0.209841 | 1.929499 | 2.278293 | 5.842301 | 1.686456 | 94.191488 | 95.523197 | 1.331709 | 3.948309 | 4.072112 | 0.123803 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 323 | 0.370656 | 3.426136 | 3.892045 | 6.900568 | 5.403409 | 93.842729 | 94.858144 | 1.015415 | 3.858778 | 3.954225 | 0.095448 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 103 | 0.727982 | 3.788991 | 4.761468 | 8.247706 | 11.366972 | 92.031780 | 92.136782 | 0.105003 | 3.792003 | 3.801604 | 0.009601 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 459 | 0.219156 | 1.929499 | 2.499072 | 5.858998 | 1.721707 | 94.191488 | 95.178991 | 0.987504 | 3.948309 | 4.044569 | 0.096260 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 323 | 0.373284 | 3.426136 | 3.934659 | 6.971591 | 5.357955 | 93.842729 | 94.600123 | 0.757395 | 3.858778 | 3.922214 | 0.063436 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 103 | 0.779931 | 3.788991 | 4.697248 | 8.541284 | 11.935780 | 92.031780 | 92.103906 | 0.072126 | 3.792003 | 3.800111 | 0.008108 |
| common_prefix | shown_excluded | 1 | Infrequent | Excluded | True | Identity | watch | 539 | 496 | 0.568220 | 1.929499 | 4.150278 | 7.406308 | 4.489796 | 94.227717 | 94.832878 | 0.605162 | 3.951757 | 4.011028 | 0.059271 |
| common_prefix | shown_excluded | 2 | Occasional | Excluded | True | Identity | watch | 352 | 339 | 0.627557 | 3.426136 | 4.318182 | 7.875000 | 9.008523 | 94.008131 | 94.497913 | 0.489782 | 3.864150 | 3.907947 | 0.043797 |
| common_prefix | shown_excluded | 3 | Frequent | Excluded | True | Identity | watch | 109 | 105 | 0.690099 | 3.788991 | 4.330275 | 7.926606 | 10.825688 | 92.138468 | 92.463353 | 0.324886 | 3.794121 | 3.828310 | 0.034188 |
| common_prefix | R2 | 1 | Infrequent | Excluded | False | Identity | watch | 539 | 496 | 0.601848 | 1.929499 | 4.235622 | 7.625232 | 4.721707 | 94.227717 | 94.598990 | 0.371274 | 3.951757 | 3.988740 | 0.036983 |
| common_prefix | R2 | 2 | Occasional | Excluded | False | Identity | watch | 352 | 339 | 0.636210 | 3.426136 | 4.312500 | 7.934659 | 9.071023 | 94.008131 | 94.429193 | 0.421063 | 3.864150 | 3.897315 | 0.033164 |
| common_prefix | R2 | 3 | Frequent | Excluded | False | Identity | watch | 109 | 105 | 0.701109 | 3.788991 | 4.229358 | 8.174312 | 11.055046 | 92.138468 | 92.343091 | 0.204623 | 3.794121 | 3.815857 | 0.021735 |

### Secondary like metrics

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 323 | 0.120207 | 2.278293 | 2.278293 | 5.842301 | 1.170686 | 95.010208 | 96.699245 | 1.689037 | 4.005171 | 4.205676 | 0.200505 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 272 | 0.173627 | 3.892045 | 3.892045 | 6.900568 | 2.852273 | 94.096226 | 96.468399 | 2.372173 | 3.888820 | 4.145448 | 0.256628 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 96 | 0.269495 | 4.761468 | 4.761468 | 8.247706 | 5.128440 | 91.960126 | 94.105021 | 2.144895 | 3.805988 | 4.032861 | 0.226872 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 316 | 0.116922 | 2.499072 | 2.499072 | 5.858998 | 1.235622 | 94.676255 | 96.070711 | 1.394456 | 3.988056 | 4.133776 | 0.145721 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 286 | 0.191489 | 3.934659 | 3.934659 | 6.971591 | 3.170455 | 93.801972 | 96.091520 | 2.289548 | 3.873180 | 4.059229 | 0.186049 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 103 | 0.334518 | 4.697248 | 4.697248 | 8.541284 | 6.302752 | 91.711331 | 94.342980 | 2.631649 | 3.794519 | 3.999220 | 0.204701 |
| full_session | shown_excluded | 1 | Infrequent | Excluded | True | Identity | like | 539 | 492 | 0.294612 | 4.150278 | 4.150278 | 7.406308 | 5.172542 | 93.640742 | 95.578641 | 1.937899 | 3.926705 | 4.116952 | 0.190247 |
| full_session | shown_excluded | 2 | Occasional | Excluded | True | Identity | like | 352 | 315 | 0.294188 | 4.318182 | 4.318182 | 7.875000 | 5.281250 | 93.848984 | 95.686712 | 1.837728 | 3.872456 | 4.082661 | 0.210205 |
| full_session | shown_excluded | 3 | Frequent | Excluded | True | Identity | like | 109 | 96 | 0.285665 | 4.330275 | 4.330275 | 7.926606 | 5.174312 | 92.128633 | 94.601093 | 2.472460 | 3.815085 | 4.039928 | 0.224843 |
| full_session | R2 | 1 | Infrequent | Excluded | False | Identity | like | 539 | 492 | 0.315484 | 4.235622 | 4.235622 | 7.625232 | 5.538033 | 93.512130 | 95.290396 | 1.778266 | 3.926169 | 4.081088 | 0.154919 |
| full_session | R2 | 2 | Occasional | Excluded | False | Identity | like | 352 | 316 | 0.324621 | 4.312500 | 4.312500 | 7.934659 | 5.775568 | 93.668140 | 95.401392 | 1.733252 | 3.867566 | 4.027036 | 0.159469 |
| full_session | R2 | 3 | Frequent | Excluded | False | Identity | like | 109 | 98 | 0.316743 | 4.229358 | 4.229358 | 8.174312 | 5.623853 | 91.902840 | 94.381253 | 2.478413 | 3.800534 | 3.990988 | 0.190454 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 240 | 0.122720 | 1.929499 | 2.278293 | 5.842301 | 1.001855 | 95.025342 | 96.260822 | 1.235480 | 4.010741 | 4.178592 | 0.167851 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 248 | 0.172680 | 3.426136 | 3.892045 | 6.900568 | 2.568182 | 94.441297 | 96.522914 | 2.081616 | 3.895710 | 4.136311 | 0.240601 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 90 | 0.258410 | 3.788991 | 4.761468 | 8.247706 | 4.174312 | 92.370930 | 94.463162 | 2.092232 | 3.818433 | 4.043010 | 0.224577 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 240 | 0.121715 | 1.929499 | 2.499072 | 5.858998 | 0.979592 | 95.025342 | 96.246372 | 1.221030 | 4.010741 | 4.160784 | 0.150043 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 248 | 0.195762 | 3.426136 | 3.934659 | 6.971591 | 2.863636 | 94.441297 | 96.554108 | 2.112811 | 3.895710 | 4.085223 | 0.189513 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 90 | 0.340023 | 3.788991 | 4.697248 | 8.541284 | 5.376147 | 92.370930 | 94.318137 | 1.947207 | 3.818433 | 4.010710 | 0.192277 |
| common_prefix | shown_excluded | 1 | Infrequent | Excluded | True | Identity | like | 539 | 429 | 0.308867 | 1.929499 | 4.150278 | 7.406308 | 2.499072 | 94.505942 | 96.003081 | 1.497139 | 3.980744 | 4.145903 | 0.165159 |
| common_prefix | shown_excluded | 2 | Occasional | Excluded | True | Identity | like | 352 | 290 | 0.297597 | 3.426136 | 4.318182 | 7.875000 | 4.326705 | 94.317851 | 95.995894 | 1.678043 | 3.890597 | 4.088421 | 0.197824 |
| common_prefix | shown_excluded | 3 | Frequent | Excluded | True | Identity | like | 109 | 91 | 0.278861 | 3.788991 | 4.330275 | 7.926606 | 4.559633 | 92.318225 | 94.538456 | 2.220231 | 3.819589 | 4.047682 | 0.228092 |
| common_prefix | R2 | 1 | Infrequent | Excluded | False | Identity | like | 539 | 429 | 0.341759 | 1.929499 | 4.235622 | 7.625232 | 2.734694 | 94.505942 | 95.847896 | 1.341954 | 3.980744 | 4.120364 | 0.139620 |
| common_prefix | R2 | 2 | Occasional | Excluded | False | Identity | like | 352 | 290 | 0.331214 | 3.426136 | 4.312500 | 7.934659 | 4.772727 | 94.317851 | 95.938086 | 1.620235 | 3.890597 | 4.050451 | 0.159854 |
| common_prefix | R2 | 3 | Frequent | Excluded | False | Identity | like | 109 | 91 | 0.317469 | 3.788991 | 4.229358 | 8.174312 | 5.165138 | 92.318225 | 94.462970 | 2.144744 | 3.819589 | 4.010541 | 0.190952 |

### Activity-crossover results to fill

Full-session total effects:

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 480 | 0.205898 | 2.278293 | 2.278293 | 5.842301 | 1.983302 | 94.045689 | 95.486934 | 1.441245 | 3.938684 | 4.067715 | 0.129031 |
| full_session | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 323 | 0.120207 | 2.278293 | 2.278293 | 5.842301 | 1.170686 | 95.010208 | 96.699245 | 1.689037 | 4.005171 | 4.205676 | 0.200505 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 333 | 0.367566 | 3.892045 | 3.892045 | 6.900568 | 6.056818 | 93.690463 | 94.719142 | 1.028678 | 3.854038 | 3.950029 | 0.095991 |
| full_session | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 272 | 0.173627 | 3.892045 | 3.892045 | 6.900568 | 2.852273 | 94.096226 | 96.468399 | 2.372173 | 3.888820 | 4.145448 | 0.256628 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 108 | 0.743578 | 4.761468 | 4.761468 | 8.247706 | 14.229358 | 91.609339 | 91.773639 | 0.164300 | 3.780910 | 3.787070 | 0.006160 |
| full_session | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 96 | 0.269495 | 4.761468 | 4.761468 | 8.247706 | 5.128440 | 91.960126 | 94.105021 | 2.144895 | 3.805988 | 4.032861 | 0.226872 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 503 | 0.212430 | 2.499072 | 2.499072 | 5.858998 | 2.202226 | 93.908492 | 94.969694 | 1.061203 | 3.940480 | 4.032958 | 0.092478 |
| full_session | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 316 | 0.116922 | 2.499072 | 2.499072 | 5.858998 | 1.235622 | 94.676255 | 96.070711 | 1.394456 | 3.988056 | 4.133776 | 0.145721 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 334 | 0.366832 | 3.934659 | 3.934659 | 6.971591 | 6.071023 | 93.506963 | 94.325807 | 0.818844 | 3.849015 | 3.916430 | 0.067415 |
| full_session | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 286 | 0.191489 | 3.934659 | 3.934659 | 6.971591 | 3.170455 | 93.801972 | 96.091520 | 2.289548 | 3.873180 | 4.059229 | 0.186049 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 109 | 0.772018 | 4.697248 | 4.697248 | 8.541284 | 14.550459 | 91.807616 | 91.984702 | 0.177086 | 3.784423 | 3.795143 | 0.010720 |
| full_session | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 103 | 0.334518 | 4.697248 | 4.697248 | 8.541284 | 6.302752 | 91.711331 | 94.342980 | 2.631649 | 3.794519 | 3.999220 | 0.204701 |
| full_session | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | watch | 539 | 539 | 0.765724 | 4.727273 | 4.727273 | 8.384045 | 14.558442 | 93.247115 | 93.411647 | 0.164532 | 3.904643 | 3.915854 | 0.011211 |
| full_session | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | like | 539 | 525 | 0.364634 | 4.727273 | 4.727273 | 8.384045 | 6.940631 | 93.314260 | 95.743587 | 2.429327 | 3.907064 | 4.120877 | 0.213813 |
| full_session | R3 | 2 | Occasional | Included | True | Unchanged Occasional | watch | 352 | 336 | 0.370502 | 3.900568 | 3.900568 | 7.039773 | 6.122159 | 93.722457 | 94.693225 | 0.970769 | 3.852195 | 3.954621 | 0.102426 |
| full_session | R3 | 2 | Occasional | Included | True | Unchanged Occasional | like | 352 | 275 | 0.183984 | 3.900568 | 3.900568 | 7.039773 | 3.053977 | 94.157529 | 96.654680 | 2.497151 | 3.890748 | 4.138800 | 0.248052 |
| full_session | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | watch | 109 | 89 | 0.185589 | 2.486239 | 2.486239 | 5.788991 | 2.082569 | 92.413690 | 94.022579 | 1.608890 | 3.801638 | 3.923391 | 0.121753 |
| full_session | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | like | 109 | 44 | 0.060398 | 2.486239 | 2.486239 | 5.788991 | 0.660550 | 92.500688 | 96.278196 | 3.777509 | 3.858714 | 4.165985 | 0.307271 |
| full_session | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | watch | 539 | 539 | 0.737137 | 4.730983 | 4.730983 | 8.443414 | 14.014842 | 93.226788 | 93.341842 | 0.115054 | 3.904188 | 3.911092 | 0.006904 |
| full_session | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | like | 539 | 514 | 0.395841 | 4.730983 | 4.730983 | 8.443414 | 7.558442 | 93.327992 | 95.373098 | 2.045105 | 3.913885 | 4.071962 | 0.158077 |
| full_session | R4 | 2 | Occasional | Included | False | Unchanged Occasional | watch | 352 | 335 | 0.356558 | 3.906250 | 3.906250 | 6.946023 | 5.877841 | 93.624644 | 94.445934 | 0.821289 | 3.849034 | 3.913795 | 0.064760 |
| full_session | R4 | 2 | Occasional | Included | False | Unchanged Occasional | like | 352 | 283 | 0.185239 | 3.906250 | 3.906250 | 6.946023 | 3.099432 | 93.829345 | 96.166395 | 2.337051 | 3.873499 | 4.070406 | 0.196907 |
| full_session | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | watch | 109 | 97 | 0.192278 | 2.706422 | 2.706422 | 5.880734 | 2.247706 | 92.390246 | 93.729527 | 1.339281 | 3.796917 | 3.876848 | 0.079931 |
| full_session | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | like | 109 | 43 | 0.058295 | 2.706422 | 2.706422 | 5.880734 | 0.706422 | 91.395631 | 93.348186 | 1.952555 | 3.813933 | 4.087750 | 0.273817 |

Identical-exposure common-prefix effects:

| scope | condition | activity_group | activity_group_name | activity_prompt | rating_shown | prompt_mapping | event | users | users_in_selected_comparison | selection_rate | mean_pages | mean_full_session_exit_page | mean_full_session_satisfaction | mean_selected_count | impression_popularity_percentile | selected_popularity_percentile | popularity_uplift_pp | impression_rating | selected_rating | rating_uplift |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | watch | 539 | 471 | 0.209609 | 1.935065 | 2.278293 | 5.842301 | 1.690167 | 94.223406 | 95.564796 | 1.341390 | 3.950954 | 4.076301 | 0.125347 |
| common_prefix | shown_included | 1 | Infrequent | Included | True | Identity | like | 539 | 303 | 0.123183 | 1.935065 | 2.278293 | 5.842301 | 1.005566 | 95.167903 | 96.676019 | 1.508116 | 4.017325 | 4.204523 | 0.187198 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | watch | 352 | 323 | 0.369271 | 3.309659 | 3.892045 | 6.900568 | 5.196023 | 93.961135 | 94.931033 | 0.969898 | 3.863350 | 3.957476 | 0.094127 |
| common_prefix | shown_included | 2 | Occasional | Included | True | Identity | like | 352 | 243 | 0.172100 | 3.309659 | 3.892045 | 6.900568 | 2.468750 | 94.433172 | 96.759590 | 2.326418 | 3.902253 | 4.155359 | 0.253105 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | watch | 109 | 82 | 0.721521 | 2.128440 | 4.761468 | 8.247706 | 6.238532 | 92.318519 | 92.586132 | 0.267613 | 3.794727 | 3.799426 | 0.004700 |
| common_prefix | shown_included | 3 | Frequent | Included | True | Identity | like | 109 | 36 | 0.246942 | 2.128440 | 4.761468 | 8.247706 | 2.155963 | 92.700036 | 95.347045 | 2.647009 | 3.856535 | 4.061735 | 0.205200 |
| common_prefix | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | watch | 539 | 471 | 0.822588 | 1.935065 | 4.727273 | 8.384045 | 6.371058 | 94.223406 | 94.289180 | 0.065774 | 3.950954 | 3.954195 | 0.003242 |
| common_prefix | R3 | 1 | Infrequent | Included | True | Swapped to Frequent | like | 539 | 303 | 0.385397 | 1.935065 | 4.727273 | 8.384045 | 3.070501 | 95.167903 | 96.599246 | 1.431343 | 4.017325 | 4.179212 | 0.161887 |
| common_prefix | R3 | 2 | Occasional | Included | True | Unchanged Occasional | watch | 352 | 323 | 0.369721 | 3.309659 | 3.900568 | 7.039773 | 5.210227 | 93.961135 | 94.904640 | 0.943505 | 3.863350 | 3.961983 | 0.098633 |
| common_prefix | R3 | 2 | Occasional | Included | True | Unchanged Occasional | like | 352 | 243 | 0.185144 | 3.309659 | 3.900568 | 7.039773 | 2.650568 | 94.433172 | 96.901224 | 2.468053 | 3.902253 | 4.144657 | 0.242404 |
| common_prefix | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | watch | 109 | 82 | 0.188073 | 2.128440 | 2.486239 | 5.788991 | 1.779817 | 92.318519 | 94.217628 | 1.899109 | 3.794727 | 3.920952 | 0.126226 |
| common_prefix | R3 | 3 | Frequent | Included | True | Swapped to Infrequent | like | 109 | 36 | 0.060971 | 2.128440 | 2.486239 | 5.788991 | 0.568807 | 92.700036 | 96.474232 | 3.774196 | 3.856535 | 4.178204 | 0.321669 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | watch | 539 | 486 | 0.219156 | 1.935065 | 2.499072 | 5.858998 | 1.727273 | 94.053364 | 95.007660 | 0.954296 | 3.949187 | 4.045141 | 0.095954 |
| common_prefix | R1 | 1 | Infrequent | Included | False | Identity | like | 539 | 296 | 0.121947 | 1.935065 | 2.499072 | 5.858998 | 0.981447 | 94.881191 | 96.130331 | 1.249140 | 4.001868 | 4.137382 | 0.135514 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | watch | 352 | 320 | 0.371863 | 3.309659 | 3.934659 | 6.971591 | 5.173295 | 93.986229 | 94.778346 | 0.792117 | 3.862236 | 3.927213 | 0.064977 |
| common_prefix | R1 | 2 | Occasional | Included | False | Identity | like | 352 | 259 | 0.194851 | 3.309659 | 3.934659 | 6.971591 | 2.761364 | 94.316100 | 96.467509 | 2.151409 | 3.892501 | 4.070022 | 0.177521 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | watch | 109 | 91 | 0.785168 | 2.128440 | 4.697248 | 8.541284 | 6.917431 | 92.462563 | 92.556858 | 0.094296 | 3.801087 | 3.806580 | 0.005493 |
| common_prefix | R1 | 3 | Frequent | Included | False | Identity | like | 109 | 40 | 0.329702 | 2.128440 | 4.697248 | 8.541284 | 2.880734 | 91.548482 | 93.634196 | 2.085714 | 3.811470 | 4.038582 | 0.227112 |
| common_prefix | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | watch | 539 | 486 | 0.808905 | 1.935065 | 4.730983 | 8.443414 | 6.269017 | 94.053364 | 94.100287 | 0.046922 | 3.949187 | 3.952046 | 0.002858 |
| common_prefix | R4 | 1 | Infrequent | Included | False | Swapped to Frequent | like | 539 | 296 | 0.431161 | 1.935065 | 4.730983 | 8.443414 | 3.410019 | 94.881191 | 96.045878 | 1.164687 | 4.001868 | 4.121863 | 0.119995 |
| common_prefix | R4 | 2 | Occasional | Included | False | Unchanged Occasional | watch | 352 | 320 | 0.361375 | 3.309659 | 3.906250 | 6.946023 | 5.053977 | 93.986229 | 94.863940 | 0.877712 | 3.862236 | 3.928258 | 0.066023 |
| common_prefix | R4 | 2 | Occasional | Included | False | Unchanged Occasional | like | 352 | 259 | 0.186553 | 3.309659 | 3.906250 | 6.946023 | 2.690341 | 94.316100 | 96.527822 | 2.211722 | 3.892501 | 4.084165 | 0.191664 |
| common_prefix | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | watch | 109 | 91 | 0.202408 | 2.128440 | 2.706422 | 5.880734 | 1.788991 | 92.462563 | 93.989439 | 1.526876 | 3.801087 | 3.892453 | 0.091366 |
| common_prefix | R4 | 3 | Frequent | Included | False | Swapped to Infrequent | like | 109 | 40 | 0.062882 | 2.128440 | 2.706422 | 5.880734 | 0.633028 | 91.548482 | 93.341655 | 1.793173 | 3.811470 | 4.078536 | 0.267066 |

## Analysis implementation notes for the agent doing the work

Start from `scripts/analyze_common_prefix_activity.py`, which already loads behavior records, validates identical candidates, forms user-level common prefixes, and computes paired effects. Extend it to accept four named run directories rather than silently changing the existing two-condition script. Write new outputs under `analysis/artifacts/rating_ablation_*.csv` and update this document in the same commit.

The relevant behavior fields are `recommended_id`, `watch_id`, `like_id`, and `page`. Use item IDs, not normalized-title matches, whenever resolved IDs exist. Preserve one row for users who selected zero items when computing selection rates; selected-item mean popularity/rating is undefined for those users and its coverage must be reported. Never replace an undefined selected mean with zero.

Recommended deliverables:

- `analysis/artifacts/rating_ablation_common_prefix_users.csv`
- `analysis/artifacts/rating_ablation_summary.csv`
- `analysis/artifacts/rating_ablation_paired_comparisons.csv`
- `analysis/artifacts/activity_crossover_summary.csv`
- `analysis/artifacts/activity_crossover_paired_comparisons.csv`
- a page-wise figure showing impression and selected popularity-percentile means for all four conditions
- this Markdown file with `TBD` cells replaced and a short conclusion that distinguishes full-session total effects from identical-exposure common-prefix effects

## References

- An Zhang et al. “On Generative Agents in Recommendation.” SIGIR 2024. [arXiv:2310.10108](https://arxiv.org/abs/2310.10108), [DOI](https://doi.org/10.1145/3626772.3657844).
- Himan Abdollahpouri, Robin Burke, and Bamshad Mobasher. “Managing Popularity Bias in Recommender Systems with Personalized Re-ranking.” FLAIRS 2019. [arXiv:1901.07555](https://arxiv.org/abs/1901.07555).
- Harald Steck. “Calibrated Recommendations.” RecSys 2018. [DOI:10.1145/3240323.3240372](https://doi.org/10.1145/3240323.3240372). This is conceptual support for comparing an output distribution with a user's/profile baseline; the present selected-minus-impression uplift is not Steck's original calibration metric.


## Direct Rating-Cue Paired Comparisons

Shown minus hidden. Watch is the primary outcome; paired means use the same users, with undefined selected-item means excluded only for uplift comparisons. Confidence intervals are 95% t intervals; p-values are raw two-sided paired tests.

| scope | activity_group | event | left | right | metric | paired_users | left_mean | right_mean | mean_difference | ci_low | ci_high | cohens_dz | p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | 1 | watch | shown_included | R1 | selection_rate | 539 | 0.205898 | 0.212430 | -0.006532 | -0.014512 | 0.001448 | -0.069260 | 0.108431 |
| full_session | 1 | watch | shown_included | R1 | popularity_uplift_pp | 459 | 1.420787 | 1.043753 | 0.377034 | -0.049527 | 0.803594 | 0.081076 | 0.083061 |
| full_session | 1 | watch | shown_included | R1 | rating_uplift | 459 | 0.126033 | 0.093901 | 0.032132 | 0.014680 | 0.049584 | 0.168881 | 0.000330 |
| full_session | 1 | watch | shown_included | R1 | selected_count | 539 | 1.983302 | 2.202226 | -0.218924 | -0.341232 | -0.096616 | -0.151450 | 0.000475 |
| full_session | 1 | watch | shown_included | R1 | session_exit_page | 539 | 2.278293 | 2.499072 | -0.220779 | -0.329895 | -0.111664 | -0.171200 | 0.000080 |
| full_session | 1 | watch | shown_excluded | R2 | selection_rate | 539 | 0.538397 | 0.552381 | -0.013984 | -0.028943 | 0.000974 | -0.079102 | 0.066841 |
| full_session | 1 | watch | shown_excluded | R2 | popularity_uplift_pp | 529 | 0.619112 | 0.467231 | 0.151880 | -0.064859 | 0.368620 | 0.059852 | 0.169218 |
| full_session | 1 | watch | shown_excluded | R2 | rating_uplift | 529 | 0.057726 | 0.042168 | 0.015558 | 0.006595 | 0.024521 | 0.148260 | 0.000699 |
| full_session | 1 | watch | shown_excluded | R2 | selected_count | 539 | 9.307978 | 9.612245 | -0.304267 | -0.617265 | 0.008731 | -0.082252 | 0.056718 |
| full_session | 1 | watch | shown_excluded | R2 | session_exit_page | 539 | 4.150278 | 4.235622 | -0.085343 | -0.172441 | 0.001754 | -0.082908 | 0.054780 |
| full_session | 2 | watch | shown_included | R1 | selection_rate | 352 | 0.367566 | 0.366832 | 0.000734 | -0.015070 | 0.016537 | 0.004868 | 0.927279 |
| full_session | 2 | watch | shown_included | R1 | popularity_uplift_pp | 323 | 1.041437 | 0.812054 | 0.229383 | -0.064538 | 0.523305 | 0.085430 | 0.125674 |
| full_session | 2 | watch | shown_included | R1 | rating_uplift | 323 | 0.098544 | 0.066615 | 0.031929 | 0.019254 | 0.044604 | 0.275744 | 0.000001 |
| full_session | 2 | watch | shown_included | R1 | selected_count | 352 | 6.056818 | 6.071023 | -0.014205 | -0.316088 | 0.287679 | -0.004932 | 0.926321 |
| full_session | 2 | watch | shown_included | R1 | session_exit_page | 352 | 3.892045 | 3.934659 | -0.042614 | -0.157605 | 0.072378 | -0.038847 | 0.466586 |
| full_session | 2 | watch | shown_excluded | R2 | selection_rate | 352 | 0.617969 | 0.627320 | -0.009351 | -0.028254 | 0.009552 | -0.051858 | 0.331250 |
| full_session | 2 | watch | shown_excluded | R2 | popularity_uplift_pp | 342 | 0.532060 | 0.438070 | 0.093990 | -0.096201 | 0.284181 | 0.052562 | 0.331721 |
| full_session | 2 | watch | shown_excluded | R2 | rating_uplift | 342 | 0.047057 | 0.031419 | 0.015638 | 0.005832 | 0.025444 | 0.169623 | 0.001856 |
| full_session | 2 | watch | shown_excluded | R2 | selected_count | 352 | 11.031250 | 11.130682 | -0.099432 | -0.515954 | 0.317090 | -0.025024 | 0.639004 |
| full_session | 2 | watch | shown_excluded | R2 | session_exit_page | 352 | 4.318182 | 4.312500 | 0.005682 | -0.093781 | 0.105144 | 0.005988 | 0.910609 |
| full_session | 3 | watch | shown_included | R1 | selection_rate | 109 | 0.743578 | 0.772018 | -0.028440 | -0.065356 | 0.008475 | -0.146269 | 0.129661 |
| full_session | 3 | watch | shown_included | R1 | popularity_uplift_pp | 108 | 0.164300 | 0.179928 | -0.015629 | -0.272031 | 0.240773 | -0.011627 | 0.904049 |
| full_session | 3 | watch | shown_included | R1 | rating_uplift | 108 | 0.006160 | 0.010470 | -0.004310 | -0.016685 | 0.008065 | -0.066439 | 0.491403 |
| full_session | 3 | watch | shown_included | R1 | selected_count | 109 | 14.229358 | 14.550459 | -0.321101 | -1.130271 | 0.488069 | -0.075341 | 0.433250 |
| full_session | 3 | watch | shown_included | R1 | session_exit_page | 109 | 4.761468 | 4.697248 | 0.064220 | -0.049211 | 0.177651 | 0.107490 | 0.264253 |
| full_session | 3 | watch | shown_excluded | R2 | selection_rate | 109 | 0.701644 | 0.703020 | -0.001376 | -0.039159 | 0.036407 | -0.006915 | 0.942580 |
| full_session | 3 | watch | shown_excluded | R2 | popularity_uplift_pp | 105 | 0.312560 | 0.202348 | 0.110213 | -0.207008 | 0.427434 | 0.067237 | 0.492376 |
| full_session | 3 | watch | shown_excluded | R2 | rating_uplift | 105 | 0.028473 | 0.021910 | 0.006563 | -0.007343 | 0.020469 | 0.091335 | 0.351492 |
| full_session | 3 | watch | shown_excluded | R2 | selected_count | 109 | 12.394495 | 12.284404 | 0.110092 | -0.720836 | 0.941019 | 0.025155 | 0.793341 |
| full_session | 3 | watch | shown_excluded | R2 | session_exit_page | 109 | 4.330275 | 4.229358 | 0.100917 | -0.121253 | 0.323088 | 0.086240 | 0.369926 |
| common_prefix | 1 | watch | shown_included | R1 | selection_rate | 539 | 0.209841 | 0.219156 | -0.009315 | -0.017506 | -0.001124 | -0.096221 | 0.025900 |
| common_prefix | 1 | watch | shown_included | R1 | popularity_uplift_pp | 459 | 1.331709 | 0.987504 | 0.344206 | -0.071288 | 0.759699 | 0.075988 | 0.104216 |
| common_prefix | 1 | watch | shown_included | R1 | rating_uplift | 459 | 0.123803 | 0.096260 | 0.027543 | 0.010992 | 0.044094 | 0.152645 | 0.001155 |
| common_prefix | 1 | watch | shown_included | R1 | selected_count | 539 | 1.686456 | 1.721707 | -0.035250 | -0.082297 | 0.011796 | -0.063397 | 0.141645 |
| common_prefix | 1 | watch | shown_excluded | R2 | selection_rate | 539 | 0.568220 | 0.601848 | -0.033627 | -0.054201 | -0.013054 | -0.138297 | 0.001403 |
| common_prefix | 1 | watch | shown_excluded | R2 | popularity_uplift_pp | 496 | 0.605162 | 0.371274 | 0.233888 | -0.006023 | 0.473799 | 0.086006 | 0.056012 |
| common_prefix | 1 | watch | shown_excluded | R2 | rating_uplift | 496 | 0.059271 | 0.036983 | 0.022288 | 0.012264 | 0.032313 | 0.196151 | 0.000015 |
| common_prefix | 1 | watch | shown_excluded | R2 | selected_count | 539 | 4.489796 | 4.721707 | -0.231911 | -0.375529 | -0.088293 | -0.136630 | 0.001600 |
| common_prefix | 2 | watch | shown_included | R1 | selection_rate | 352 | 0.370656 | 0.373284 | -0.002628 | -0.019585 | 0.014330 | -0.016245 | 0.760713 |
| common_prefix | 2 | watch | shown_included | R1 | popularity_uplift_pp | 323 | 1.015415 | 0.757395 | 0.258020 | -0.008211 | 0.524251 | 0.106091 | 0.057452 |
| common_prefix | 2 | watch | shown_included | R1 | rating_uplift | 323 | 0.095448 | 0.063436 | 0.032012 | 0.018774 | 0.045250 | 0.264711 | 0.000003 |
| common_prefix | 2 | watch | shown_included | R1 | selected_count | 352 | 5.403409 | 5.357955 | 0.045455 | -0.154672 | 0.245581 | 0.023809 | 0.655364 |
| common_prefix | 2 | watch | shown_excluded | R2 | selection_rate | 352 | 0.627557 | 0.636210 | -0.008653 | -0.028551 | 0.011245 | -0.045586 | 0.392983 |
| common_prefix | 2 | watch | shown_excluded | R2 | popularity_uplift_pp | 339 | 0.489782 | 0.421063 | 0.068719 | -0.141746 | 0.279185 | 0.034882 | 0.521146 |
| common_prefix | 2 | watch | shown_excluded | R2 | rating_uplift | 339 | 0.043797 | 0.033164 | 0.010633 | 0.000048 | 0.021217 | 0.107323 | 0.048966 |
| common_prefix | 2 | watch | shown_excluded | R2 | selected_count | 352 | 9.008523 | 9.071023 | -0.062500 | -0.323425 | 0.198425 | -0.025110 | 0.637862 |
| common_prefix | 3 | watch | shown_included | R1 | selection_rate | 109 | 0.727982 | 0.779931 | -0.051950 | -0.097931 | -0.005968 | -0.214499 | 0.027177 |
| common_prefix | 3 | watch | shown_included | R1 | popularity_uplift_pp | 103 | 0.105003 | 0.072126 | 0.032876 | -0.143146 | 0.208899 | 0.036503 | 0.711806 |
| common_prefix | 3 | watch | shown_included | R1 | rating_uplift | 103 | 0.009601 | 0.008108 | 0.001493 | -0.008531 | 0.011518 | 0.029111 | 0.768255 |
| common_prefix | 3 | watch | shown_included | R1 | selected_count | 109 | 11.366972 | 11.935780 | -0.568807 | -1.202387 | 0.064772 | -0.170448 | 0.077966 |
| common_prefix | 3 | watch | shown_excluded | R2 | selection_rate | 109 | 0.690099 | 0.701109 | -0.011009 | -0.050676 | 0.028658 | -0.052693 | 0.583362 |
| common_prefix | 3 | watch | shown_excluded | R2 | popularity_uplift_pp | 105 | 0.324886 | 0.204623 | 0.120263 | -0.266712 | 0.507237 | 0.060143 | 0.539055 |
| common_prefix | 3 | watch | shown_excluded | R2 | rating_uplift | 105 | 0.034188 | 0.021735 | 0.012453 | -0.002183 | 0.027089 | 0.164654 | 0.094562 |
| common_prefix | 3 | watch | shown_excluded | R2 | selected_count | 109 | 10.825688 | 11.055046 | -0.229358 | -0.766750 | 0.308034 | -0.081031 | 0.399430 |


## Activity-Crossover Paired Comparisons

Swapped minus identity, stratified by original activity group. Occasional is the unchanged-prompt negative control.

| scope | activity_group | event | left | right | metric | paired_users | left_mean | right_mean | mean_difference | ci_low | ci_high | cohens_dz | p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_session | 1 | watch | R3 | shown_included | selection_rate | 539 | 0.765724 | 0.205898 | 0.559825 | 0.544336 | 0.575315 | 3.058112 | 0.000000 |
| full_session | 1 | watch | R3 | shown_included | popularity_uplift_pp | 480 | 0.153224 | 1.441245 | -1.288021 | -1.733981 | -0.842062 | -0.259032 | 0.000000 |
| full_session | 1 | watch | R3 | shown_included | rating_uplift | 480 | 0.010253 | 0.129031 | -0.118779 | -0.138515 | -0.099042 | -0.539752 | 0.000000 |
| full_session | 1 | watch | R3 | shown_included | selected_count | 539 | 14.558442 | 1.983302 | 12.575139 | 12.259398 | 12.890880 | 3.369873 | 0.000000 |
| full_session | 1 | watch | R3 | shown_included | session_exit_page | 539 | 4.727273 | 2.278293 | 2.448980 | 2.350328 | 2.547631 | 2.100461 | 0.000000 |
| full_session | 1 | watch | R4 | R1 | selection_rate | 539 | 0.737137 | 0.212430 | 0.524706 | 0.508218 | 0.541195 | 2.692591 | 0.000000 |
| full_session | 1 | watch | R4 | R1 | popularity_uplift_pp | 503 | 0.136721 | 1.061203 | -0.924482 | -1.353464 | -0.495500 | -0.188787 | 0.000027 |
| full_session | 1 | watch | R4 | R1 | rating_uplift | 503 | 0.006319 | 0.092478 | -0.086159 | -0.103717 | -0.068602 | -0.429883 | 0.000000 |
| full_session | 1 | watch | R4 | R1 | selected_count | 539 | 14.014842 | 2.202226 | 11.812616 | 11.488918 | 12.136314 | 3.087717 | 0.000000 |
| full_session | 1 | watch | R4 | R1 | session_exit_page | 539 | 4.730983 | 2.499072 | 2.231911 | 2.132677 | 2.331145 | 1.903044 | 0.000000 |
| full_session | 2 | watch | R3 | shown_included | selection_rate | 352 | 0.370502 | 0.367566 | 0.002936 | -0.011076 | 0.016947 | 0.021963 | 0.680544 |
| full_session | 2 | watch | R3 | shown_included | popularity_uplift_pp | 328 | 0.962350 | 1.009249 | -0.046899 | -0.328513 | 0.234714 | -0.018090 | 0.743407 |
| full_session | 2 | watch | R3 | shown_included | rating_uplift | 328 | 0.102049 | 0.096871 | 0.005178 | -0.006412 | 0.016767 | 0.048528 | 0.380114 |
| full_session | 2 | watch | R3 | shown_included | selected_count | 352 | 6.122159 | 6.056818 | 0.065341 | -0.219827 | 0.350509 | 0.024019 | 0.652525 |
| full_session | 2 | watch | R3 | shown_included | session_exit_page | 352 | 3.900568 | 3.892045 | 0.008523 | -0.098664 | 0.115709 | 0.008335 | 0.875822 |
| full_session | 2 | watch | R4 | R1 | selection_rate | 352 | 0.356558 | 0.366832 | -0.010275 | -0.025327 | 0.004778 | -0.071554 | 0.180308 |
| full_session | 2 | watch | R4 | R1 | popularity_uplift_pp | 323 | 0.885724 | 0.784875 | 0.100850 | -0.212739 | 0.414438 | 0.035204 | 0.527379 |
| full_session | 2 | watch | R4 | R1 | rating_uplift | 323 | 0.066527 | 0.066299 | 0.000228 | -0.012269 | 0.012725 | 0.001995 | 0.971420 |
| full_session | 2 | watch | R4 | R1 | selected_count | 352 | 5.877841 | 6.071023 | -0.193182 | -0.486328 | 0.099964 | -0.069081 | 0.195801 |
| full_session | 2 | watch | R4 | R1 | session_exit_page | 352 | 3.906250 | 3.934659 | -0.028409 | -0.138299 | 0.081481 | -0.027100 | 0.611457 |
| full_session | 3 | watch | R3 | shown_included | selection_rate | 109 | 0.185589 | 0.743578 | -0.557989 | -0.601124 | -0.514854 | -2.455986 | 0.000000 |
| full_session | 3 | watch | R3 | shown_included | popularity_uplift_pp | 88 | 1.622944 | 0.205364 | 1.417580 | 0.452777 | 2.382383 | 0.311314 | 0.004452 |
| full_session | 3 | watch | R3 | shown_included | rating_uplift | 88 | 0.121953 | 0.008690 | 0.113263 | 0.070479 | 0.156047 | 0.560910 | 0.000001 |
| full_session | 3 | watch | R3 | shown_included | selected_count | 109 | 2.082569 | 14.229358 | -12.146789 | -12.991850 | -11.301728 | -2.728989 | 0.000000 |
| full_session | 3 | watch | R3 | shown_included | session_exit_page | 109 | 2.486239 | 4.761468 | -2.275229 | -2.518793 | -2.031665 | -1.773539 | 0.000000 |
| full_session | 3 | watch | R4 | R1 | selection_rate | 109 | 0.192278 | 0.772018 | -0.579740 | -0.617481 | -0.541999 | -2.916435 | 0.000000 |
| full_session | 3 | watch | R4 | R1 | popularity_uplift_pp | 97 | 1.339281 | 0.180426 | 1.158855 | 0.203192 | 2.114518 | 0.244397 | 0.017995 |
| full_session | 3 | watch | R4 | R1 | rating_uplift | 97 | 0.079931 | 0.010907 | 0.069024 | 0.024757 | 0.113291 | 0.314262 | 0.002578 |
| full_session | 3 | watch | R4 | R1 | selected_count | 109 | 2.247706 | 14.550459 | -12.302752 | -13.045522 | -11.559983 | -3.144680 | 0.000000 |
| full_session | 3 | watch | R4 | R1 | session_exit_page | 109 | 2.706422 | 4.697248 | -1.990826 | -2.216795 | -1.764856 | -1.672678 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | selection_rate | 539 | 0.822588 | 0.209609 | 0.612979 | 0.592474 | 0.633484 | 2.529413 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | popularity_uplift_pp | 471 | 0.065774 | 1.341390 | -1.275616 | -1.724484 | -0.826748 | -0.257311 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | rating_uplift | 471 | 0.003242 | 0.125347 | -0.122105 | -0.140960 | -0.103250 | -0.586352 | 0.000000 |
| common_prefix | 1 | watch | R3 | shown_included | selected_count | 539 | 6.371058 | 1.690167 | 4.680891 | 4.435556 | 4.926225 | 1.614362 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | selection_rate | 539 | 0.808905 | 0.219156 | 0.589750 | 0.568634 | 0.610865 | 2.363198 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | popularity_uplift_pp | 486 | 0.046922 | 0.954296 | -0.907374 | -1.389117 | -0.425630 | -0.167875 | 0.000239 |
| common_prefix | 1 | watch | R4 | R1 | rating_uplift | 486 | 0.002858 | 0.095954 | -0.093095 | -0.111154 | -0.075037 | -0.459470 | 0.000000 |
| common_prefix | 1 | watch | R4 | R1 | selected_count | 539 | 6.269017 | 1.727273 | 4.541744 | 4.298624 | 4.784864 | 1.580643 | 0.000000 |
| common_prefix | 2 | watch | R3 | shown_included | selection_rate | 352 | 0.369721 | 0.369271 | 0.000450 | -0.014912 | 0.015812 | 0.003069 | 0.954109 |
| common_prefix | 2 | watch | R3 | shown_included | popularity_uplift_pp | 323 | 0.943505 | 0.969898 | -0.026393 | -0.272538 | 0.219752 | -0.011738 | 0.833059 |
| common_prefix | 2 | watch | R3 | shown_included | rating_uplift | 323 | 0.098633 | 0.094127 | 0.004507 | -0.006983 | 0.015996 | 0.042937 | 0.440873 |
| common_prefix | 2 | watch | R3 | shown_included | selected_count | 352 | 5.210227 | 5.196023 | 0.014205 | -0.165624 | 0.194033 | 0.008280 | 0.876633 |
| common_prefix | 2 | watch | R4 | R1 | selection_rate | 352 | 0.361375 | 0.371863 | -0.010488 | -0.026754 | 0.005778 | -0.067589 | 0.205609 |
| common_prefix | 2 | watch | R4 | R1 | popularity_uplift_pp | 320 | 0.877712 | 0.792117 | 0.085595 | -0.178400 | 0.349589 | 0.035660 | 0.523998 |
| common_prefix | 2 | watch | R4 | R1 | rating_uplift | 320 | 0.066023 | 0.064977 | 0.001046 | -0.012230 | 0.014321 | 0.008662 | 0.876960 |
| common_prefix | 2 | watch | R4 | R1 | selected_count | 352 | 5.053977 | 5.173295 | -0.119318 | -0.309804 | 0.071168 | -0.065663 | 0.218794 |
| common_prefix | 3 | watch | R3 | shown_included | selection_rate | 109 | 0.188073 | 0.721521 | -0.533448 | -0.599435 | -0.467461 | -1.534846 | 0.000000 |
| common_prefix | 3 | watch | R3 | shown_included | popularity_uplift_pp | 82 | 1.899109 | 0.267613 | 1.631496 | 0.677127 | 2.585865 | 0.375619 | 0.001044 |
| common_prefix | 3 | watch | R3 | shown_included | rating_uplift | 82 | 0.126226 | 0.004700 | 0.121526 | 0.075911 | 0.167141 | 0.585383 | 0.000001 |
| common_prefix | 3 | watch | R3 | shown_included | selected_count | 109 | 1.779817 | 6.238532 | -4.458716 | -5.059950 | -3.857481 | -1.407974 | 0.000000 |
| common_prefix | 3 | watch | R4 | R1 | selection_rate | 109 | 0.202408 | 0.785168 | -0.582760 | -0.641901 | -0.523619 | -1.870811 | 0.000000 |
| common_prefix | 3 | watch | R4 | R1 | popularity_uplift_pp | 91 | 1.526876 | 0.094296 | 1.432581 | 0.279497 | 2.585665 | 0.258740 | 0.015468 |
| common_prefix | 3 | watch | R4 | R1 | rating_uplift | 91 | 0.091366 | 0.005493 | 0.085873 | 0.039192 | 0.132553 | 0.383113 | 0.000433 |
| common_prefix | 3 | watch | R4 | R1 | selected_count | 109 | 1.788991 | 6.917431 | -5.128440 | -5.810100 | -4.446781 | -1.428388 | 0.000000 |


## Conclusion

Randomized position seed 20261121, Agent4Rec: P1/P4 1.282, user-bootstrap 95% CI [1.210, 1.360]; vanilla 1.335.

Randomized position seed 20261122, Agent4Rec: P1/P4 1.230, user-bootstrap 95% CI [1.164, 1.303]; vanilla 1.335.

Randomized position seed 20261123, Agent4Rec: P1/P4 1.256, user-bootstrap 95% CI [1.184, 1.338]; vanilla 1.335.

Rating shown minus hidden (shown_included, Infrequent), watch-selected rating uplift: difference 0.0275, 95% CI [0.0110, 0.0441], paired users 459, dz 0.1526, raw p 0.00115533.

Rating shown minus hidden (shown_excluded, Infrequent), watch-selected rating uplift: difference 0.0223, 95% CI [0.0123, 0.0323], paired users 496, dz 0.1962, raw p 1.52495e-05.

Rating shown minus hidden (shown_included, Occasional), watch-selected rating uplift: difference 0.0320, 95% CI [0.0188, 0.0452], paired users 323, dz 0.2647, raw p 2.96449e-06.

Rating shown minus hidden (shown_excluded, Occasional), watch-selected rating uplift: difference 0.0106, 95% CI [0.0000, 0.0212], paired users 339, dz 0.1073, raw p 0.0489656.

Rating shown minus hidden (shown_included, Frequent), watch-selected rating uplift: difference 0.0015, 95% CI [-0.0085, 0.0115], paired users 103, dz 0.0291, raw p 0.768255.

Rating shown minus hidden (shown_excluded, Frequent), watch-selected rating uplift: difference 0.0125, 95% CI [-0.0022, 0.0271], paired users 105, dz 0.1647, raw p 0.0945621.

Activity swap R3 minus shown_included: original Infrequent watch-rate difference 0.6130, original Frequent -0.5334; confidence intervals support opposite-direction reversal: True. Unchanged Occasional negative control: difference 0.0004, 95% CI [-0.0149, 0.0158], raw p 0.954109.

Activity swap R4 minus R1: original Infrequent watch-rate difference 0.5897, original Frequent -0.5828; confidence intervals support opposite-direction reversal: True. Unchanged Occasional negative control: difference -0.0105, 95% CI [-0.0268, 0.0058], raw p 0.205609.

Full-session estimates include condition-dependent page reach; identical-exposure results compare the matched common prefix only. Selection rates include zero-selection users; uplift estimates are conditional on selection in both paired conditions. The numerical rating cue is the manipulated factor, while conformity remains unchanged and may contribute residual rating sensitivity. Raw p-values are not multiplicity-adjusted.
