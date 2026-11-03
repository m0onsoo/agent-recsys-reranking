#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
parent_root="$(cd "$repo_root/.." && pwd)"
python_bin="${PYTHON_BIN:-/home1/moonsoo/projects/venv/bin/python}"

export MODEL_ARTIFACT_ROOT="${MODEL_ARTIFACT_ROOT:-/home1/moonsoo/projects/ara/checkpoints}"

cd "$repo_root"
"$python_bin" scripts/prepare_bundle_maintainer.py \
  --panel "$parent_root/panels/all_ratings_ro_v3_50_seed42/sampled_users_50_seed42.csv" \
  --registry registry/models.yaml \
  --recbole-root /home1/moonsoo/projects/RecBole \
  --recbole-debias-root /home1/moonsoo/projects/Recbole-Debias \
  --dataset-root /home1/moonsoo/projects/RecBole/dataset \
  --extended-movie-path /home1/moonsoo/projects/RecBole/dataset/ml-1m/ml1m_extended_movie.csv \
  --allow-ineligible \
  --output-dir data/derived/repro50

"$python_bin" -m agent_reranking.cli generate-profiles \
  --bundle data/derived/repro50 \
  --method ours \
  --persona-file "$parent_root/outputs/persona_generation_v3/20261025_010926_561214_RO_seed42_openai_100users/personas.jsonl" \
  --num-users 50 \
  --profile-components history,unique_tastes,social_traits,demographics \
  --output-dir artifacts/profiles/repro50_no_demographics

"$python_bin" -m agent_reranking.cli run \
  --bundle data/derived/repro50 \
  --profiles artifacts/profiles/repro50_no_demographics/profiles.jsonl \
  --num-users 50 \
  --profile-components history,unique_tastes,social_traits \
  --profile-protocol legacy_combined
