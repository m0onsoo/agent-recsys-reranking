#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --account=annavara_668
#SBATCH --job-name=agent-rerank-pilot30
#SBATCH --output=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-%j.out
#SBATCH --error=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-%j.err

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

users_file=data/panels/users_30_from_1000_seed42.csv
profile_dir=artifacts/profiles/pilot30_ours_all_v2

python -m agent_reranking.cli generate-profiles \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file "$users_file" \
  --method ours \
  --model gpt-4o-mini \
  --profile-components all \
  --concurrency 20 \
  --output-dir "$profile_dir"

python -m agent_reranking.cli run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file "$users_file" \
  --profiles "$profile_dir/profiles.jsonl" \
  --llm-model gpt-4o-mini \
  --profile-components all \
  --profile-protocol separated \
  --concurrency 20 \
  --output-root results/pilot30/runs
