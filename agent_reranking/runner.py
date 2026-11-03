"""Concurrent, resumable agent execution followed by pure policy evaluation."""

import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .agent import TwoStageAgent
from .bundle import DataBundle
from .client import MockClient, OpenAICompatibleClient, RateBudget
from .io import read_jsonl, stable_hash, write_csv, write_json
from .metrics import evaluate, rating_strata
from .rerank import all_rankings
from .results import append_jsonl, create_run, summarize, upsert_index


def _client(config):
    if config["llm_provider"] == "mock":
        return MockClient()
    budget = RateBudget(config["requests_per_minute"], config["tokens_per_minute"],
                        config["max_cost_usd"], config["input_cost_per_million"],
                        config["output_cost_per_million"])
    return OpenAICompatibleClient(config["llm_model"], config["llm_base_url"],
                                  config["api_key_env"], config["temperature"],
                                  config["request_timeout_seconds"], budget)


def _profile_payload(profile, components, protocol="separated"):
    enabled = set(components)
    result = {"user_id": profile["user_id"]}
    mapping = {"history": "interaction_history", "unique_tastes": "unique_tastes",
               "social_traits": "social_traits", "demographics": "demographics"}
    legacy_summary = None
    if protocol == "legacy_combined":
        mapping.pop("unique_tastes")
        mapping.pop("social_traits")
        if enabled.intersection({"unique_tastes", "social_traits"}):
            if "legacy_persona_summary" not in profile:
                raise ValueError("legacy_combined requires an imported legacy persona summary")
            legacy_summary = profile["legacy_persona_summary"]
    elif protocol != "separated":
        raise ValueError(f"Unknown profile protocol: {protocol}")
    for component, field in mapping.items():
        if component in enabled and field in profile:
            if field == "interaction_history":
                fields = ("title", "release_year", "genres", "overview", "director",
                          "cast", "release_date", "language", "country")
                result[field] = [{key: movie[key] for key in fields if key in movie}
                                 for movie in profile[field]]
            else:
                result[field] = profile[field]
    if legacy_summary is not None:
        result["persona_summary"] = legacy_summary
    return result


def run(config, bundle_path, profiles_path, resume=None, case_limit=None):
    bundle = DataBundle(bundle_path)
    profiles = {int(row["user_id"]): row for row in read_jsonl(profiles_path)}
    users = bundle.users[:config["num_users"]]
    if any(user not in profiles for user in users):
        raise ValueError("A selected user is missing a generated profile")
    root = create_run(config["output_root"], config, resume)
    completed = {(row["model"], int(row["user_id"])): row for row in
                 read_jsonl(root / "actions.jsonl")}
    keys = [(model, user) for model in config["models"] for user in users]
    keys = [key for key in keys if int(stable_hash(key), 16) % config["num_shards"]
            == config["shard_index"] and key not in completed]
    if case_limit is not None:
        keys = keys[:case_limit]
    client = _client(config)
    agent = TwoStageAgent(client, config["retry_count"])

    def one(model, user):
        candidate = bundle.candidates[(model, user)]
        profile = _profile_payload(profiles[user], config["profile_components"],
                                   config["profile_protocol"])
        actions, calls = agent.simulate(profile, candidate, bundle.catalog)
        return {"model": model, "user_id": user, "actions": actions,
                "profile_hash": stable_hash(profile), "candidate_hash": stable_hash(candidate)}, calls

    # Match the legacy execution order: one model at a time, in bounded user
    # batches, with every batch joined before the next batch is submitted.
    for model in config["models"]:
        model_keys = [key for key in keys if key[0] == model]
        for start in range(0, len(model_keys), config["concurrency"]):
            batch = model_keys[start:start + config["concurrency"]]
            with ThreadPoolExecutor(max_workers=config["concurrency"]) as pool:
                futures = [(key, pool.submit(one, *key)) for key in batch]
                for (case_model, user), future in futures:
                    try:
                        row, calls = future.result()
                        for call in calls:
                            append_jsonl(root / "calls.jsonl",
                                         {"model": case_model, "user_id": user, **call})
                        append_jsonl(root / "actions.jsonl", row)
                        completed[(case_model, user)] = row
                    except Exception as exc:
                        append_jsonl(root / "failures.jsonl", {
                            "model": case_model, "user_id": user,
                            "error_type": type(exc).__name__, "error": str(exc)[:300]})

    metric_rows, strata_rows, ranking_rows = [], [], []
    for (model, user), row in sorted(completed.items()):
        if user not in users or model not in config["models"]:
            continue
        candidate = bundle.candidates[(model, user)]
        rankings = all_rankings(candidate, row["actions"], config["top_k"])
        heldout = bundle.labels[user]["heldout_items"]
        ranking_rows.append({"model": model, "user_id": user, "rankings": rankings})
        for stage, ranking in rankings.items():
            metric_rows.append({"model": model, "user_id": user, "stage": stage,
                                **evaluate(ranking, candidate["item_ids"], heldout,
                                           config["top_k"])})
            for stratum, labels in rating_strata(heldout).items():
                if labels:
                    strata_rows.append({"model": model, "user_id": user, "stage": stage,
                                        "rating_stratum": stratum,
                                        **evaluate(ranking, candidate["item_ids"], labels,
                                                   config["top_k"])})
    from .io import write_jsonl
    write_jsonl(root / "rankings.jsonl", ranking_rows)
    metric_fields = ["model", "user_id", "stage", f"recall@{config['top_k']}",
                     f"ndcg@{config['top_k']}", f"candidate_recall@{config['candidate_size']}"]
    write_csv(root / "per_user_metrics.csv", metric_rows, metric_fields)
    summary = summarize(metric_rows, config["top_k"], config["candidate_size"]) if metric_rows else []
    summary_fields = ["model", "stage", "num_users", f"recall@{config['top_k']}",
                      f"ndcg@{config['top_k']}", f"candidate_recall@{config['candidate_size']}",
                      "recall_absolute_change", "recall_relative_change",
                      "ndcg_absolute_change", "ndcg_relative_change"]
    write_csv(root / "summary.csv", summary, summary_fields)
    write_csv(root / "rating_stratified_metrics.csv", strata_rows,
              metric_fields[:3] + ["rating_stratum"] + metric_fields[3:])
    failures = read_jsonl(root / "failures.jsonl")
    calls = read_jsonl(root / "calls.jsonl")
    cost = sum(row.get("estimated_cost_usd", 0) for row in calls)
    status = "complete" if len(completed) == len([(m, u) for m in config["models"] for u in users
        if int(stable_hash((m, u)), 16) % config["num_shards"] == config["shard_index"]]) else "partial"
    manifest = {"schema_version": 1, "run_id": root.name,
                "created_at_utc": datetime.now(timezone.utc).isoformat(), "status": status,
                "bundle_id": bundle.manifest["bundle_id"], "num_users": len(users),
                "completed_cases": len(completed), "failure_count": len(failures),
                "estimated_cost_usd": cost,
                "behavior_prompt_sha256": agent.prompt_hashes}
    write_json(root / "run_manifest.json", manifest)
    upsert_index(Path(config["output_root"]).parent, {**manifest,
        "num_cases": len(completed), "models": ",".join(config["models"]),
        "profile_method": config["profile_method"],
        "profile_components": ",".join(config["profile_components"]),
        "llm_model": config["llm_model"], "prompt_version": config["prompt_version"],
        "run_dir": str(root)})
    return {"run_dir": str(root), **manifest}
