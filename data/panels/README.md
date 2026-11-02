# Fixed panels

Commit the already sampled 1,000-user CSV here as `users_1000_seed42.csv`.
The runner never resamples a committed panel. Required columns are `user_id` and
`raw_user_id`; provenance columns and per-model Top-20 held-out counts are strongly
recommended.

MovieLens interaction rows are not stored in Git. Run `agent-reranking download-data`
and `agent-reranking prepare-bundle` locally to materialize profile inputs.
