#!/usr/bin/env bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=06:00:00
#SBATCH --account=annavara_668
#SBATCH --array=0-3
#SBATCH --job-name=agent-rerank-ablate50
#SBATCH --output=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/ablate50-%A_%a.out
#SBATCH --error=/home1/moonsoo/projects/ara/click_conversion_reranker/agent-reranking-bench/results/ablate50-%A_%a.err

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

conditions=(full no_demographics no_persona no_interaction_history)
components=(
  history,unique_tastes,social_traits,demographics
  history,unique_tastes,social_traits
  history,demographics
  unique_tastes,social_traits,demographics
)
condition="${conditions[$SLURM_ARRAY_TASK_ID]}"
selected_components="${components[$SLURM_ARRAY_TASK_ID]}"
profile_dir="artifacts/profiles/repro50_legacy_${condition}"

python -m agent_reranking.cli generate-profiles \
  --bundle data/derived/repro50 \
  --method ours \
  --persona-file "$repo_root/../outputs/persona_generation_v3/20261025_010926_561214_RO_seed42_openai_100users/personas.jsonl" \
  --num-users 50 \
  --profile-components all \
  --output-dir "$profile_dir"

python -m agent_reranking.cli run \
  --bundle data/derived/repro50 \
  --profiles "$profile_dir/profiles.jsonl" \
  --num-users 50 \
  --profile-components "$selected_components" \
  --profile-protocol legacy_combined \
  --concurrency 20 \
  --output-root "results/ablations/$condition/runs" \
  "$@"
