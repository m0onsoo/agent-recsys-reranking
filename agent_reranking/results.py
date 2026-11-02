"""Immutable run artifacts and a durable CSV experiment registry."""

import csv
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .io import atomic_text, stable_hash, write_csv


LOCK = threading.Lock()
INDEX_FIELDS = ["run_id", "created_at_utc", "status", "num_users", "num_cases",
                "models", "profile_method", "profile_components", "llm_model",
                "prompt_version", "bundle_id", "estimated_cost_usd", "run_dir"]


def append_jsonl(path, value):
    with LOCK:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("a", encoding="utf-8") as target:
            target.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
            target.flush()
            os.fsync(target.fileno())


def create_run(output_root, config, resume=None):
    if resume:
        root = Path(resume).resolve()
        stored = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
        if stored != config:
            raise ValueError("Resume configuration differs from the original run")
        return root
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{stamp}_{stable_hash(config)[:10]}"
    root = Path(output_root).resolve() / run_id
    root.mkdir(parents=True, exist_ok=False)
    atomic_text(root / "config.yaml", yaml.safe_dump(config, sort_keys=True))
    for name in ("actions.jsonl", "calls.jsonl", "failures.jsonl"):
        (root / name).touch()
    return root


def upsert_index(results_root, row):
    path = Path(results_root).resolve() / "index.csv"
    rows = []
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
    by_id = {item["run_id"]: item for item in rows}
    by_id[row["run_id"]] = {field: row.get(field, "") for field in INDEX_FIELDS}
    write_csv(path, [by_id[key] for key in sorted(by_id)], INDEX_FIELDS)


def summarize(rows, top_k, candidate_size):
    fields = [f"recall@{top_k}", f"ndcg@{top_k}", f"candidate_recall@{candidate_size}"]
    summary = []
    keys = sorted({(row["model"], row["stage"]) for row in rows})
    for model, stage in keys:
        selected = [row for row in rows if row["model"] == model and row["stage"] == stage]
        summary.append({"model": model, "stage": stage, "num_users": len(selected),
                        **{field: sum(float(row[field]) for row in selected) / len(selected)
                           for field in fields}})
    baseline = {row["model"]: row for row in summary if row["stage"] == "sampled_baseline"}
    for row in summary:
        base = baseline[row["model"]]
        for metric in ("recall", "ndcg"):
            field = f"{metric}@{top_k}"
            row[f"{metric}_absolute_change"] = row[field] - base[field]
            row[f"{metric}_relative_change"] = ((row[field] - base[field]) / base[field]
                                                       if base[field] else "")
    return summary

