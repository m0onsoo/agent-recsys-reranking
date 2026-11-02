"""Dependency-free ranking and rating-stratified metrics."""

import math


def evaluate(ranking, candidate_ids, heldout, top_k):
    positives = {int(row["item_id"]) for row in heldout}
    if not positives:
        raise ValueError("Every user requires at least one held-out interaction")
    hits = [int(item in positives) for item in ranking[:top_k]]
    dcg = sum(hit / math.log2(index + 2) for index, hit in enumerate(hits))
    ideal = sum(1 / math.log2(index + 2) for index in range(min(len(positives), top_k)))
    return {f"recall@{top_k}": sum(hits) / len(positives),
            f"ndcg@{top_k}": dcg / ideal if ideal else 0.0,
            f"candidate_recall@{len(candidate_ids)}":
                len(set(candidate_ids) & positives) / len(positives)}


def rating_strata(heldout):
    return {"low_1_2": [row for row in heldout if row["rating"] <= 2],
            "neutral_3": [row for row in heldout if row["rating"] == 3],
            "high_4_5": [row for row in heldout if row["rating"] >= 4]}

