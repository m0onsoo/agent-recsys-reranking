#!/usr/bin/env python3
"""Create profiles that change one rendered social-trait level at a time."""

import argparse
import copy
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_reranking.io import read_jsonl, sha256_file, write_json, write_jsonl


TRAITS = ("activity", "conformity", "diversity")
LEVELS = (1, 2, 3)


def intervene(profiles, trait, assigned_level):
    """Preserve observed values/levels and add one explicit prompt assignment."""
    if trait not in TRAITS or assigned_level not in LEVELS:
        raise ValueError("Unknown trait intervention")
    result = []
    for source in profiles:
        row = copy.deepcopy(source)
        social = row.get("social_traits")
        if not isinstance(social, dict) or any(name not in social for name in TRAITS):
            raise ValueError(f"User {row.get('user_id')} lacks structured social traits")
        for name in TRAITS:
            social[name].pop("assigned_level", None)
        observed = int(social[trait]["level"])
        social[trait]["assigned_level"] = assigned_level
        row["trait_intervention"] = {
            "trait": trait,
            "observed_level": observed,
            "assigned_level": assigned_level,
        }
        result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    source_path = Path(args.profiles)
    profiles = read_jsonl(source_path)
    if not profiles or len({int(row["user_id"]) for row in profiles}) != len(profiles):
        raise ValueError("Profiles must contain unique users")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for trait in TRAITS:
        for level in LEVELS:
            path = output / f"{trait}_level{level}.jsonl"
            write_jsonl(path, intervene(profiles, trait, level))
            files[f"{trait}_level{level}"] = {
                "path": str(path), "sha256": sha256_file(path),
                "assigned_level": level, "trait": trait,
            }
    write_json(output / "manifest.json", {
        "schema_version": 1,
        "design": "one_trait_at_a_time_within_user_intervention",
        "source_profiles": str(source_path),
        "source_profiles_sha256": sha256_file(source_path),
        "num_users": len(profiles),
        "traits": list(TRAITS),
        "levels": list(LEVELS),
        "files": files,
    })


if __name__ == "__main__":
    main()
