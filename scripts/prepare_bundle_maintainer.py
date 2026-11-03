#!/usr/bin/env python3
"""Maintainer-only checkpoint materialization; not needed by experiment runners."""

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def main():
    parser = argparse.ArgumentParser(
        description="Build a portable bundle from registered RecBole checkpoints")
    parser.add_argument("--panel", required=True)
    parser.add_argument("--registry", default="registry/models.yaml")
    parser.add_argument("--recbole-root", required=True)
    parser.add_argument("--recbole-debias-root")
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--extended-movie-path")
    parser.add_argument("--candidate-size", type=int, default=20)
    parser.add_argument("--allow-ineligible", action="store_true")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    # Keep torch/RecBole imports out of the installed runner and its CLI startup.
    from agent_reranking.data import prepare_bundle

    result = prepare_bundle(
        args.panel, args.registry, args.recbole_root, args.dataset_root,
        args.output_dir, args.recbole_debias_root, args.extended_movie_path,
        args.candidate_size, not args.allow_ineligible)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
