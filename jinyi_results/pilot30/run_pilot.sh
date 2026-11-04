#!/bin/zsh
# Moved into jinyi_results/pilot30/ on 2026-11-03; paths updated (repo and gpt5.env are two levels up).
set -euo pipefail

output_dir="${0:A:h}"
repo_dir="${output_dir:h:h}/agent-recsys-reranking"
python="${repo_dir}/.venv/bin/python"
cd "$repo_dir"
export AGENT_RERANKING_ENV="${output_dir:h:h}/gpt5.env"

resume_dir=""
if (( $# > 0 )); then
  if [[ "$1" != "--resume" || $# != 2 ]]; then
    printf 'Usage: zsh run_pilot.sh [--resume RUN_DIR]\n' >&2
    exit 1
  fi
  resume_dir="${2:A}"
else
  run_dirs=("$output_dir"/runs/*(N/))
  if (( ${#run_dirs} > 0 )); then
    resume_dir="${run_dirs[-1]}"
  fi
fi

if [[ -n "$resume_dir" ]]; then
  if [[ ! -f "$resume_dir/config.yaml" || ! -f "$output_dir/profiles/profiles.jsonl" ]]; then
    printf 'Resume requires saved config and complete pilot profiles.\n' >&2
    exit 1
  fi
  printf 'Resuming %s with its unchanged saved configuration.\n' "$resume_dir"
  "$python" -m agent_reranking.cli run \
    --config "$resume_dir/config.yaml" \
    --bundle data/derived/ml1m_ro_n1000_seed42 \
    --profiles "$output_dir/profiles/profiles.jsonl" \
    --resume "$resume_dir" \
    2>&1 | tee -a "$output_dir/agent_run.log"
  exit 0
fi

git rev-parse HEAD > "$output_dir/code_version.txt"
git status --short >> "$output_dir/code_version.txt"
"$python" -m agent_reranking.cli validate-bundle \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  2>&1 | tee "$output_dir/bundle_validation.log"
"$python" scripts/evaluate_bundle_baselines.py \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --top-k 10 --output "$output_dir/baselines.json" \
  2>&1 | tee "$output_dir/baselines.log"

"$python" -c 'from agent_reranking.client import api_key; assert api_key("OPENAI_API_KEY"), "OPENAI_API_KEY is empty"; print("API key configured; value not displayed")'
base_url=$("$python" -c 'from agent_reranking.client import api_key; endpoint = api_key("OPENAI_ENDPOINT").rstrip("/"); print(endpoint if endpoint.endswith("/v1") else endpoint + "/v1")')
"$python" -c 'import sys, yaml; from pathlib import Path; config = yaml.safe_load(Path("configs/default.yaml").read_text()); config["llm_base_url"] = sys.argv[1]; config["temperature"] = 0.0; Path(sys.argv[2]).write_text(yaml.safe_dump(config, sort_keys=False))' "$base_url" "$output_dir/pilot_config.yaml"

if [[ ! -f "$output_dir/profiles/profiles.jsonl" ]]; then
  "$python" -m agent_reranking.cli generate-profiles \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_30_from_1000_seed42.csv \
  --method ours --model gpt-4o-mini --base-url "$base_url" --profile-components all \
  --history-size 10 --seed 42 --concurrency 32 \
  --requests-per-minute 60 --tokens-per-minute 100000 \
  --max-cost-usd 2 --output-dir "$output_dir/profiles" \
    2>&1 | tee -a "$output_dir/profile_generation.log"
fi

"$python" -m agent_reranking.cli run \
  --config "$output_dir/pilot_config.yaml" \
  --bundle data/derived/ml1m_ro_n1000_seed42 \
  --users-file data/panels/users_30_from_1000_seed42.csv \
  --profiles "$output_dir/profiles/profiles.jsonl" \
  --llm-model gpt-4o-mini \
  --prompt-version behavior-align-rating-social-traits \
  --profile-components all --profile-protocol separated \
  --concurrency 32 --requests-per-minute 60 --tokens-per-minute 100000 \
  --max-cost-usd 2 --output-root "$output_dir/runs" \
  2>&1 | tee "$output_dir/agent_run.log"