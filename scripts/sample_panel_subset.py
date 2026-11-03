#!/usr/bin/env python3
"""Draw a reproducible simple-random subset from a committed panel CSV."""

import argparse
import csv
import hashlib
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with Path(args.source).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows, fields = list(reader), list(reader.fieldnames or ())
    if not rows or "user_id" not in fields or not 0 < args.size <= len(rows):
        raise ValueError("Source panel or requested subset size is invalid")
    ordered = sorted(rows, key=lambda row: int(row["user_id"]))
    sampled = sorted(random.Random(args.seed).sample(ordered, args.size),
                     key=lambda row: int(row["user_id"]))
    extra = ["subset_sampling_seed", "parent_panel_sha256"]
    parent_hash = hashlib.sha256(Path(args.source).read_bytes()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields + extra)
        writer.writeheader()
        for row in sampled:
            writer.writerow({**row, "subset_sampling_seed": args.seed,
                             "parent_panel_sha256": parent_hash})
    temporary.replace(output)


if __name__ == "__main__":
    main()
