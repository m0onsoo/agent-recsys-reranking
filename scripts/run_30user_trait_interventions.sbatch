#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00
#SBATCH --account=annavara_668
#SBATCH --job-name=agent-rerank-trait-cf
#SBATCH --output=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-trait-cf-%j.out
#SBATCH --error=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/pilot30-trait-cf-%j.err

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

profile_root=artifacts/profiles/pilot30_trait_interventions
python scripts/create_trait_intervention_profiles.py \
  --profiles artifacts/profiles/pilot30_ours_all_v2/profiles.jsonl \
  --output-dir "$profile_root"

# Fixed interleaved order reduces alignment between elapsed time and trait level.
conditions=(
  activity:1 diversity:2 conformity:3
  activity:2 diversity:3 conformity:1
  activity:3 diversity:1 conformity:2
)

for condition in "${conditions[@]}"; do
  trait=${condition%%:*}
  level=${condition##*:}
  python -m agent_reranking.cli run \
    --bundle data/derived/ml1m_ro_n1000_seed42 \
    --users-file data/panels/users_30_from_1000_seed42.csv \
    --profiles "$profile_root/${trait}_level${level}.jsonl" \
    --llm-model gpt-4o-mini \
    --prompt-version behavior-social-traits \
    --profile-components all \
    --profile-protocol separated \
    --concurrency 20 \
    --max-cost-usd 0.5 \
    --output-root "results/pilot30_trait_interventions/${trait}_level${level}/runs"
done
