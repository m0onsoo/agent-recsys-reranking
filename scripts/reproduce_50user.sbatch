#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --account=annavara_668
#SBATCH --job-name=agent-rerank-repro50
#SBATCH --output=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/repro50-%j.out
#SBATCH --error=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/repro50-%j.err

set -euo pipefail

repo_root=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench
cd "$repo_root"

module purge
module load legacy/CentOS7
module load gcc/11.3.0
module load cuda/11.8.0
module load python/3.9.21
source /home1/moonsoo/projects/venv/bin/activate

export AGENT_RERANKING_ENV="$repo_root/../.env"
export PYTHONWARNINGS=ignore

python -m agent_reranking.cli generate-profiles \
  --bundle data/derived/repro50 \
  --method ours \
  --persona-file "$repo_root/../outputs/persona_generation_v3/20261025_010926_561214_RO_seed42_openai_100users/personas.jsonl" \
  --num-users 50 \
  --profile-components history,persona \
  --output-dir artifacts/profiles/repro50_no_demographics

python -m agent_reranking.cli run \
  --bundle data/derived/repro50 \
  --profiles artifacts/profiles/repro50_no_demographics/profiles.jsonl \
  --num-users 50 \
  --profile-components history,persona \
  --concurrency 20 \
  --output-root results/runs \
  "$@"
