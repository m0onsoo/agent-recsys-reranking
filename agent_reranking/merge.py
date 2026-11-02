"""Merge disjoint shard action artifacts and recompute global metrics."""

from pathlib import Path

import yaml

from .io import read_jsonl, stable_hash
from .results import append_jsonl, create_run
from .runner import run


def merge_runs(bundle_path, profiles_path, run_dirs, output_root=None):
    roots = [Path(value).resolve() for value in run_dirs]
    if len(roots) < 2:
        raise ValueError("merge-runs requires at least two shard run directories")
    configs = [yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
               for root in roots]

    def comparable(config):
        return {key: value for key, value in config.items()
                if key not in {"num_shards", "shard_index", "output_root"}}

    if any(comparable(config) != comparable(configs[0]) for config in configs[1:]):
        raise ValueError("Shard configurations differ beyond shard/output fields")
    count = configs[0]["num_shards"]
    indices = {config["shard_index"] for config in configs}
    if any(config["num_shards"] != count for config in configs) or indices != set(range(count)):
        raise ValueError(f"Expected exactly shard indices 0..{count - 1}")

    actions = {}
    calls, failures = [], []
    for root in roots:
        for row in read_jsonl(root / "actions.jsonl"):
            key = (row["model"], int(row["user_id"]))
            if key in actions and stable_hash(actions[key]) != stable_hash(row):
                raise ValueError(f"Conflicting action record for {key}")
            actions[key] = row
        calls.extend(read_jsonl(root / "calls.jsonl"))
        failures.extend(read_jsonl(root / "failures.jsonl"))

    config = dict(configs[0])
    config.update({"num_shards": 1, "shard_index": 0,
                   "output_root": output_root or configs[0]["output_root"]})
    merged = create_run(config["output_root"], config)
    for row in sorted(actions.values(), key=lambda x: (x["model"], int(x["user_id"]))):
        append_jsonl(merged / "actions.jsonl", row)
    for row in calls:
        append_jsonl(merged / "calls.jsonl", row)
    for row in failures:
        append_jsonl(merged / "failures.jsonl", row)
    result = run(config, bundle_path, profiles_path, resume=merged, case_limit=0)
    result.update({"source_runs": [str(root) for root in roots],
                   "merged_action_count": len(actions)})
    return result
