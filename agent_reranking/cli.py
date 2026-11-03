"""Command-line entry point for data, profile, and agent workflows."""

import argparse
import csv
import json
from pathlib import Path

from .bundle import DataBundle
from .client import MockClient, OpenAICompatibleClient, RateBudget
from .config import load_config
from .merge import merge_runs
from .profiles import PROFILE_COMPONENTS, PROFILE_METHODS, generate_profiles
from .runner import run


def _print(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _user_ids(path):
    if not path:
        return None
    with Path(path).open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows or "user_id" not in rows[0]:
        raise ValueError("--users-file must be a nonempty CSV with a user_id column")
    values = [int(row["user_id"]) for row in rows]
    if len(set(values)) != len(values):
        raise ValueError("--users-file contains duplicate user IDs")
    return values


def _components(args, fallback=None):
    value = args.profile_components
    if value is None:
        enabled = set(fallback or PROFILE_COMPONENTS)
    elif value == "all":
        enabled = set(PROFILE_COMPONENTS)
    else:
        enabled = {item.strip() for item in value.split(",") if item.strip()}
    for component in PROFILE_COMPONENTS:
        if getattr(args, "no_use_" + component, False):
            enabled.discard(component)
    return sorted(enabled)


def _common_profile_flags(parser, default="all"):
    parser.add_argument("--profile-components", default=default,
                        help="all or comma-separated history,unique_tastes,social_traits,demographics")
    for component in PROFILE_COMPONENTS:
        parser.add_argument("--no-use-" + component.replace("_", "-"), action="store_true")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agent-reranking")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "validate-bundle", help="Verify a precomputed bundle without RecBole or checkpoints")
    validate.add_argument("--bundle", required=True)

    profiles = commands.add_parser("generate-profiles")
    profiles.add_argument("--bundle", required=True)
    profiles.add_argument("--method", choices=PROFILE_METHODS, default="ours")
    profiles.add_argument("--client", choices=("mock", "openai_compatible"), default="openai_compatible")
    profiles.add_argument("--model", default="gpt-4o-mini")
    profiles.add_argument("--base-url", default="https://api.openai.com/v1")
    profiles.add_argument("--api-key-env", default="OPENAI_API_KEY")
    profiles.add_argument("--num-users", type=int, default=1000)
    profiles.add_argument("--users-file",
                          help="Fixed user CSV; when supplied, overrides --num-users")
    profiles.add_argument("--history-size", type=int, default=10)
    profiles.add_argument("--seed", type=int, default=42)
    profiles.add_argument("--concurrency", type=int, default=20,
                          help="Maximum concurrent profile API workers")
    profiles.add_argument("--persona-file",
                          help="Import existing personas by raw user ID (zero profile API calls)")
    profiles.add_argument("--requests-per-minute", type=int, default=300)
    profiles.add_argument("--tokens-per-minute", type=int, default=1_000_000)
    profiles.add_argument("--max-cost-usd", type=float, default=25.0)
    profiles.add_argument("--input-cost-per-million", type=float, default=0.15)
    profiles.add_argument("--output-cost-per-million", type=float, default=0.60)
    profiles.add_argument("--output-dir", default="artifacts/profiles")
    _common_profile_flags(profiles)

    execute = commands.add_parser("run")
    execute.add_argument("--config", default="configs/default.yaml")
    execute.add_argument("--bundle", required=True)
    execute.add_argument("--profiles", required=True)
    execute.add_argument("--num-users", type=int)
    execute.add_argument("--users-file",
                         help="Fixed user CSV; when supplied, overrides --num-users")
    execute.add_argument("--candidate-size", type=int)
    execute.add_argument("--top-k", type=int)
    execute.add_argument("--concurrency", type=int)
    execute.add_argument("--requests-per-minute", type=int)
    execute.add_argument("--tokens-per-minute", type=int)
    execute.add_argument("--max-cost-usd", type=float)
    execute.add_argument("--case-limit", type=int)
    execute.add_argument("--resume")
    execute.add_argument("--num-shards", type=int)
    execute.add_argument("--shard-index", type=int)
    execute.add_argument("--llm-provider", choices=("mock", "openai_compatible"))
    execute.add_argument("--llm-model")
    execute.add_argument("--prompt-version", choices=(
        "behavior-motive-assessment-v1", "behavior-motive-assessment-v2"))
    execute.add_argument("--output-root")
    execute.add_argument("--profile-protocol", choices=("separated", "legacy_combined"))
    _common_profile_flags(execute, default=None)

    merge = commands.add_parser("merge-runs", help="Merge complete disjoint shard runs")
    merge.add_argument("--bundle", required=True)
    merge.add_argument("--profiles", required=True)
    merge.add_argument("--runs", nargs="+", required=True)
    merge.add_argument("--output-root")

    args = parser.parse_args(argv)
    if args.command == "validate-bundle":
        _print(DataBundle(args.bundle).summary())
        return
    if args.command == "generate-profiles":
        budget = RateBudget(args.requests_per_minute, args.tokens_per_minute, args.max_cost_usd,
                            args.input_cost_per_million, args.output_cost_per_million)
        client = (MockClient() if args.client == "mock" or args.persona_file else
                  OpenAICompatibleClient(args.model, args.base_url, args.api_key_env,
                                         budget=budget))
        _print(generate_profiles(DataBundle(args.bundle), client, args.method,
                                 _components(args), args.seed, args.history_size,
                                 args.num_users, args.output_dir, args.concurrency,
                                 args.persona_file, _user_ids(args.users_file)))
        return
    if args.command == "merge-runs":
        _print(merge_runs(args.bundle, args.profiles, args.runs, args.output_root))
        return
    overrides = {name: getattr(args, name) for name in (
        "num_users", "candidate_size", "top_k", "concurrency", "requests_per_minute",
        "tokens_per_minute", "max_cost_usd", "num_shards", "shard_index",
        "llm_provider", "llm_model", "prompt_version", "output_root",
        "profile_protocol")}
    config = load_config(args.config, overrides)
    selected_user_ids = _user_ids(args.users_file)
    if selected_user_ids is not None:
        config["selected_user_ids"] = selected_user_ids
        config["num_users"] = len(selected_user_ids)
    config["profile_components"] = _components(args, config["profile_components"])
    _print(run(config, args.bundle, args.profiles, args.resume, args.case_limit))


if __name__ == "__main__":
    main()
