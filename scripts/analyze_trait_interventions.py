#!/usr/bin/env python3
"""Audit one-trait-at-a-time interventions with user-clustered uncertainty."""

import argparse
import json
import random
import statistics
from pathlib import Path


TRAITS = ("activity", "conformity", "diversity")
LEVELS = (1, 2, 3)


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def latest_run(root):
    manifests = sorted(Path(root).glob("*/run_manifest.json"))
    complete = [path for path in manifests
                if json.loads(path.read_text(encoding="utf-8")).get("status") == "complete"]
    if not complete:
        raise ValueError(f"No complete run under {root}")
    return complete[-1].parent


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def cluster_interval(differences, seed, samples):
    """Bootstrap users, retaining all backbone cases within each sampled user."""
    by_user = {}
    for (_, user), value in differences.items():
        by_user.setdefault(user, []).append(value)
    users = sorted(by_user)
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        selected = [rng.choice(users) for _ in users]
        values = [value for user in selected for value in by_user[user]]
        estimates.append(statistics.mean(values))
    point = statistics.mean(differences.values())
    return point, percentile(estimates, .025), percentile(estimates, .975)


def case_metrics(key, action, profiles, candidates, catalog):
    _, user = key
    clicked = action["clicked_item_ids"]
    converted = action["converted_item_ids"]
    slate = candidates[key]["item_ids"]
    visible_genres = {genre for movie in profiles[user]["interaction_history"]
                      for genre in movie["genres"]}
    clicked_ratings = [catalog[item]["average_rating"] for item in clicked
                       if catalog[item].get("average_rating") is not None]
    slate_ratings = [catalog[item]["average_rating"] for item in slate
                     if catalog[item].get("average_rating") is not None]
    clicked_genres = {genre for item in clicked for genre in catalog[item]["genres"]}
    novel = [bool(set(catalog[item]["genres"]) - visible_genres) for item in clicked]
    rated = sorted((catalog[item]["average_rating"], item) for item in slate
                   if catalog[item].get("average_rating") is not None)
    width = max(1, len(rated) // 3)
    bottom = {item for _, item in rated[:width]}
    top = {item for _, item in rated[-width:]}
    selected = set(clicked)
    return {
        "click_count": len(clicked),
        "conversion_count": len(converted),
        "conversion_abstention": int(not converted),
        "unique_clicked_genres": len(clicked_genres),
        "novel_genre_fraction": statistics.mean(novel) if novel else 0.0,
        "clicked_average_rating": statistics.mean(clicked_ratings) if clicked_ratings else 0.0,
        "rating_selection_lift": ((statistics.mean(clicked_ratings)
                                   - statistics.mean(slate_ratings))
                                  if clicked_ratings and slate_ratings else 0.0),
        "top_bottom_rating_click_gap": (len(selected & top) / len(top)
                                         - len(selected & bottom) / len(bottom)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", default="results/pilot30_trait_interventions")
    parser.add_argument("--profiles", default="artifacts/profiles/pilot30_ours_all_v2/profiles.jsonl")
    parser.add_argument("--bundle", default="data/derived/ml1m_ro_n1000_seed42")
    parser.add_argument("--output", default="results/pilot30_trait_interventions_audit.md")
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    profiles = {int(row["user_id"]): row for row in read_jsonl(args.profiles)}
    bundle = Path(args.bundle)
    catalog = {int(row["item_id"]): row for row in read_jsonl(bundle / "item_catalog.jsonl")}
    candidates = {(row["model"], int(row["user_id"])): row
                  for row in read_jsonl(bundle / "candidates.jsonl")}
    runs, actions = {}, {}
    for trait in TRAITS:
        for level in LEVELS:
            condition = f"{trait}_level{level}"
            run = latest_run(Path(args.runs_root) / condition / "runs")
            rows = read_jsonl(run / "actions.jsonl")
            runs[(trait, level)] = run
            actions[(trait, level)] = {
                (row["model"], int(row["user_id"])): row["actions"] for row in rows}

    primary = {
        "activity": ("click_count", 1),
        "diversity": ("novel_genre_fraction", 1),
        "conformity": ("rating_selection_lift", -1),
    }
    lines = ["# Pilot-30 social-trait counterfactual audit", "", "## Design", "",
             "Same users, profiles, backbone candidates, and action prompt; one social-trait "
             "level is assigned at a time. Confidence intervals use a user-cluster bootstrap.", ""]
    for trait in TRAITS:
        common = set.intersection(*(set(actions[(trait, level)]) for level in LEVELS))
        metrics = {level: {key: case_metrics(
            key, actions[(trait, level)][key], profiles, candidates, catalog)
                           for key in common} for level in LEVELS}
        lines += [f"## {trait.title()}", "",
                  f"Common cases: {len(common)}. Runs: " + ", ".join(
                      f"L{level} `{runs[(trait, level)].name}`" for level in LEVELS), ""]
        names = ("click_count", "conversion_abstention", "unique_clicked_genres",
                 "novel_genre_fraction", "clicked_average_rating",
                 "rating_selection_lift", "top_bottom_rating_click_gap")
        lines += ["| Metric | Level 1 | Level 2 | Level 3 |", "|---|---:|---:|---:|"]
        for name in names:
            values = [statistics.mean(metrics[level][key][name] for key in common)
                      for level in LEVELS]
            lines.append(f"| {name} | {values[0]:.4f} | {values[1]:.4f} | {values[2]:.4f} |")
        measure, direction = primary[trait]
        difference = {key: direction * (metrics[3][key][measure] - metrics[1][key][measure])
                      for key in common}
        point, low, high = cluster_interval(
            difference, args.seed, args.bootstrap_samples)
        monotonic = sum(
            direction * metrics[1][key][measure]
            <= direction * metrics[2][key][measure]
            <= direction * metrics[3][key][measure] for key in common) / len(common)
        orientation = "L3-L1" if direction == 1 else "L1-L3"
        lines += ["", f"Primary measure: `{measure}`.", "",
                  f"Expected-direction {orientation}: {point:.4f} "
                  f"(95% user-cluster bootstrap CI [{low:.4f}, {high:.4f}]).", "",
                  f"Case-level non-strict monotonicity: {monotonic:.1%}.", ""]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
