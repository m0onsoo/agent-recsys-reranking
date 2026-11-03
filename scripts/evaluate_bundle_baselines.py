#!/usr/bin/env python3
"""Evaluate precomputed backbone rankings without loading model checkpoints."""

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_reranking.bundle import DataBundle
from agent_reranking.io import write_json
from agent_reranking.metrics import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()
    bundle = DataBundle(args.bundle)
    if args.top_k < 1 or args.top_k > bundle.manifest["candidate_size"]:
        parser.error("--top-k must be between 1 and the bundle candidate size")

    metric_names = [f"recall@{args.top_k}", f"ndcg@{args.top_k}",
                    f"candidate_recall@{bundle.manifest['candidate_size']}"]
    models = {}
    for model in bundle.manifest["models"]:
        rows = []
        for user in bundle.users:
            candidate = bundle.candidates[(model, user)]
            rows.append(evaluate(candidate["item_ids"][:args.top_k],
                                 candidate["item_ids"],
                                 bundle.labels[user]["heldout_items"], args.top_k))
        models[model] = {"test_users": len(rows), **{
            metric: sum(row[metric] for row in rows) / len(rows)
            for metric in metric_names}}

    result = {
        "schema_version": 1,
        "bundle_id": bundle.manifest["bundle_id"],
        "panel_sha256": bundle.manifest["panel_sha256"],
        "split_hash": bundle.manifest["split_hash"],
        "candidate_size": bundle.manifest["candidate_size"],
        "top_k": args.top_k,
        "relevance_definition": "all checkpoint test interactions, independent of rating",
        "panel_conditioning": "all three models have at least one held-out interaction in Top-20",
        "models": models,
    }
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
