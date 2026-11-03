# Repository data policy

This repository is intended for private collaboration on the fixed MovieLens-1M
agent-reranking study. Review this policy before pushing a new artifact.

## Commit

- source code, prompts, tests, configs, and documentation;
- the fixed eligibility population and 1,000-user panel with manifests;
- `data/derived/ml1m_ro_n1000_seed42/`, the validated precomputed bundle needed to
  generate profiles and run the agent without RecBole or model checkpoints;
- model registry entries, aggregate metrics, and concise experiment reports;
- `.gitkeep` placeholders for profile and run output directories.

The fixed bundle contains MovieLens-derived histories and held-out labels plus
enriched movie metadata. Keep the GitHub repository private unless redistribution
has been reviewed separately.

## Do not commit

- `.env` or any API key, token, credential, provider response header, or account ID;
- model checkpoints (`.pth`, `.pt`, `.ckpt`) or local RecBole installations;
- raw MovieLens downloads or the source `ml1m_extended_movie.csv`;
- API caches, metadata caches, Python environments, or bytecode;
- generated profile directories until a specific profile release is intentionally
  reviewed and versioned;
- raw per-call transcripts, action logs, Slurm stdout/stderr, or resumable run
  directories;
- unrelated historical outputs from the parent experimental repository.

Share aggregate result tables and compact reports through Git. If a future fixed
bundle exceeds repository limits, publish the archive separately and replace it with
a manifest containing its exact SHA-256 and retrieval instructions.
