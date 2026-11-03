# Fixed panels

`eligible_users_joint_top20.csv` is the audited sampling population. Its 4,588 users
have at least ten checkpoint-train interactions and at least one checkpoint-test
interaction in every registered model's genuine full-sort Top-20.

`users_1000_seed42.csv` is a simple random sample without replacement from that
population, using Python's `random.Random(42)`. It is sorted by internal user ID only
after selection. The adjacent manifest pins the population, model checkpoints,
mapping, split, sampling rule, seed, and panel hashes.

`users_30_from_1000_seed42.csv` is the fixed pilot subset sampled without replacement
from the committed 1,000-user panel with `random.Random(42)`. Pass this same file via
`--users-file` during both profile generation and reranking. The row order is retained
across both stages, and the parent panel hash is recorded in every row.

The runner never resamples the committed panel. Movie histories, candidate IDs and
scores, held-out labels, item metadata, and social traits belong in the separately
shared precomputed bundle, not in this directory.
