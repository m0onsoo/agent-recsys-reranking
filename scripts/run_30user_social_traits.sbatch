#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --account=annavara_668
#SBATCH --job-name=agent-rerank-p30-social
#SBATCH --output=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-social-%j.out
#SBATCH --error=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-social-%j.err

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

# Controlled comparison with job 13691697: reuse its exact users, profiles,
# candidates, model alias, profile components, and concurrency. Change only the
# behavior prompt to route each social trait to a concrete decision role.
python -m agent_reranking.cli run \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_30_from_1000_seed42.csv \
  --profiles artifacts/profiles/pilot30_ours_all_v2/profiles.jsonl \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-social-traits \
  --profile-components all \
  --profile-protocol separated \
  --concurrency 20 \
  --output-root results/pilot30_social_traits/runs
