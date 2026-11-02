"""Command-line entry point for data, profile, and agent workflows."""

import argparse
import json
from pathlib import Path

from .bundle import DataBundle
from .client import MockClient, OpenAICompatibleClient, RateBudget
from .config import load_config
from .data import prepare_bundle
from .download import convert_ml1m, download_ml1m
from .profiles import PROFILE_COMPONENTS, PROFILE_METHODS, generate_profiles
from .runner import run


def _print(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _components(args):
    if args.profile_components == "all":
        enabled = set(PROFILE_COMPONENTS)
    else:
        enabled = {item.strip() for item in args.profile_components.split(",") if item.strip()}
    for component in PROFILE_COMPONENTS:
        if getattr(args, "no_use_" + component, False):
            enabled.discard(component)
    return sorted(enabled)


def _common_profile_flags(parser):
    parser.add_argument("--profile-components", default="all",
                        help="all or comma-separated history,persona,social_traits,pickiness,demographics")
    for component in PROFILE_COMPONENTS:
        parser.add_argument("--no-use-" + component.replace("_", "-"), action="store_true")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agent-reranking")
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser("download-data", help="Download official MovieLens-1M")
    download.add_argument("--output-root", default="data/raw")
    download.add_argument("--convert-root", default="data/recbole")

    prepare = commands.add_parser("prepare-bundle", help="Reconstruct split and materialize local inputs")
    prepare.add_argument("--panel", required=True)
    prepare.add_argument("--registry", default="registry/models.yaml")
    prepare.add_argument("--recbole-root", required=True)
    prepare.add_argument("--recbole-debias-root")
    prepare.add_argument("--dataset-root", default="data/recbole")
    prepare.add_argument("--extended-movie-path")
    prepare.add_argument("--candidate-size", type=int, default=20)
    prepare.add_argument("--output-dir", default="data/derived/ml1m_ro_n1000_seed42")

    profiles = commands.add_parser("generate-profiles")
    profiles.add_argument("--bundle", required=True)
    profiles.add_argument("--method", choices=PROFILE_METHODS, default="ours")
    profiles.add_argument("--client", choices=("mock", "openai_compatible"), default="openai_compatible")
    profiles.add_argument("--model", default="gpt-4o-mini")
    profiles.add_argument("--base-url", default="https://api.openai.com/v1")
    profiles.add_argument("--api-key-env", default="OPENAI_API_KEY")
    profiles.add_argument("--num-users", type=int, default=1000)
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
    execute.add_argument("--output-root")
    _common_profile_flags(execute)

    args = parser.parse_args(argv)
    if args.command == "download-data":
        result = download_ml1m(args.output_root)
        result["recbole_dataset_dir"] = convert_ml1m(result["dataset_dir"], args.convert_root)
        _print(result)
        return
    if args.command == "prepare-bundle":
        _print(prepare_bundle(args.panel, args.registry, args.recbole_root, args.dataset_root,
                              args.output_dir, args.recbole_debias_root,
                              args.extended_movie_path, args.candidate_size))
        return
    if args.command == "generate-profiles":
        budget = RateBudget(args.requests_per_minute, args.tokens_per_minute, args.max_cost_usd,
                            args.input_cost_per_million, args.output_cost_per_million)
        client = (MockClient() if args.client == "mock" else
                  OpenAICompatibleClient(args.model, args.base_url, args.api_key_env,
                                         budget=budget))
        _print(generate_profiles(DataBundle(args.bundle), client, args.method,
                                 _components(args), args.seed, args.history_size,
                                 args.num_users, args.output_dir, args.concurrency,
                                 args.persona_file))
        return
    overrides = {name: getattr(args, name) for name in (
        "num_users", "candidate_size", "top_k", "concurrency", "requests_per_minute",
        "tokens_per_minute", "max_cost_usd", "num_shards", "shard_index",
        "llm_provider", "llm_model", "output_root")}
    config = load_config(args.config, overrides)
    config["profile_components"] = _components(args)
    _print(run(config, args.bundle, args.profiles, args.resume, args.case_limit))


if __name__ == "__main__":
    main()
