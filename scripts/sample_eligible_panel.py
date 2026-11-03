#!/usr/bin/env python3
"""Create a fixed SRS panel from a pre-audited joint Top-K eligible population."""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_reranking.checkpoints import CheckpointAdapter
from agent_reranking.io import sha256_file, stable_hash


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def _atomic_text(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_csv(path, rows, fieldnames):
    lines = []

    class Writer:
        def write(self, value):
            lines.append(value)

    writer = csv.DictWriter(Writer(), fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    _atomic_text(path, "".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--eligible-users", default="data/panels/eligible_users_joint_top20.csv")
    parser.add_argument(
        "--eligible-manifest",
        default="data/panels/eligible_users_joint_top20.manifest.json")
    parser.add_argument("--registry", default="registry/models.yaml")
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--recbole-root", required=True)
    parser.add_argument("--recbole-debias-root", required=True)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--panel-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--minimum-train-interactions", type=int, default=10)
    parser.add_argument("--output", default="data/panels/users_1000_seed42.csv")
    args = parser.parse_args()

    source_rows = _read_csv(args.eligible_users)
    source_manifest = json.loads(
        Path(args.eligible_manifest).read_text(encoding="utf-8"))
    registry_document = yaml.safe_load(Path(args.registry).read_text(encoding="utf-8"))
    registry = registry_document["models"]
    if [entry["display_name"] for entry in registry] != ["MF", "LightGCN", "MultiVAE"]:
        raise ValueError("Registry must contain MF, LightGCN, and MultiVAE in order")
    if source_manifest["candidate_size"] != 20:
        raise ValueError("Eligible population was not created with Top-20")
    if source_manifest["common_reachable_users"] != len(source_rows):
        raise ValueError("Eligible population count differs from its manifest")
    if len({int(row["user_id"]) for row in source_rows}) != len(source_rows):
        raise ValueError("Eligible population contains duplicate users")
    count_fields = ["mf_positive_count_top20", "lightgcn_positive_count_top20",
                    "multivae_positive_count_top20"]
    if any(int(row[field]) < 1 for row in source_rows for field in count_fields):
        raise ValueError("Eligible population contains a non-positive Top-20 count")

    artifact_root = Path(args.artifact_root).resolve()
    for entry in registry:
        checkpoint = Path(os.path.expandvars(
            entry["artifact_path"].replace("${MODEL_ARTIFACT_ROOT}", str(artifact_root))))
        source = source_manifest["models"][entry["display_name"]]
        if sha256_file(checkpoint) != entry["checkpoint_sha256"]:
            raise ValueError(f"Registry checkpoint hash mismatch: {entry['display_name']}")
        if source["checkpoint_sha256"] != entry["checkpoint_sha256"]:
            raise ValueError(f"Eligible population used another checkpoint: {entry['display_name']}")
        if (entry["mapping_hash"] != source_manifest["mapping_hash"]
                or entry["split_hash"] != source_manifest["split_hash"]):
            raise ValueError(f"Eligible population mapping/split mismatch: {entry['display_name']}")

    mf = registry[0]
    mf_checkpoint = Path(os.path.expandvars(
        mf["artifact_path"].replace("${MODEL_ARTIFACT_ROOT}", str(artifact_root))))
    adapter = CheckpointAdapter(
        mf_checkpoint, args.recbole_root, args.dataset_root, "MF",
        args.recbole_debias_root)
    if adapter.mapping_hash != mf["mapping_hash"] or adapter.split_hash != mf["split_hash"]:
        raise ValueError("Reconstructed MF mapping or split differs from registry")

    population = []
    for source in source_rows:
        user = int(source["user_id"])
        train_count = len(adapter.train_seen.get(user, ()))
        if train_count < args.minimum_train_interactions:
            continue
        population.append({
            "user_id": user,
            "raw_user_id": source["raw_user_id"],
            "train_interaction_count": train_count,
            "test_positive_count": int(source["test_positive_count"]),
            **{field: int(source[field]) for field in count_fields},
            "sampling_seed": args.seed,
            "sampling_design": "simple_random_without_replacement",
        })
    population.sort(key=lambda row: row["user_id"])
    if len(population) < args.panel_size:
        raise ValueError("Eligible population is smaller than requested panel")
    sampled = sorted(random.Random(args.seed).sample(population, args.panel_size),
                     key=lambda row: row["user_id"])

    output = Path(args.output)
    fields = ["user_id", "raw_user_id", "train_interaction_count",
              "test_positive_count", *count_fields, "sampling_seed", "sampling_design"]
    _write_csv(output, sampled, fields)
    manifest = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sampling_design": "simple_random_without_replacement",
        "sampling_seed": args.seed,
        "panel_size": len(sampled),
        "source_population_size": len(source_rows),
        "eligible_after_history_filter": len(population),
        "minimum_train_interactions": args.minimum_train_interactions,
        "joint_top20_positive_required": True,
        "relevance_definition": "all checkpoint test interactions, independent of rating",
        "source_users_sha256": sha256_file(args.eligible_users),
        "source_manifest_sha256": sha256_file(args.eligible_manifest),
        "model_registry_sha256": sha256_file(args.registry),
        "mapping_hash": adapter.mapping_hash,
        "split_hash": adapter.split_hash,
        "checkpoint_sha256": {
            entry["display_name"]: entry["checkpoint_sha256"] for entry in registry},
        "panel_sha256": sha256_file(output),
        "panel_user_ids_hash": stable_hash([row["user_id"] for row in sampled]),
        "columns": {
            "user_id": "Checkpoint-internal user ID",
            "raw_user_id": "Original MovieLens user token",
            "train_interaction_count": "Checkpoint train-split interactions",
            "test_positive_count": "All checkpoint test interactions",
            "*_positive_count_top20": "Held-out interactions in that model's Top-20",
        },
    }
    manifest_path = output.with_suffix(".manifest.json")
    _atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"panel": str(output.resolve()),
                      "manifest": str(manifest_path.resolve()),
                      "population": len(population), "sampled": len(sampled)}, indent=2))


if __name__ == "__main__":
    main()
