#!/usr/bin/env python3
"""Audit the migrated 50-user path without making API calls."""

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_reranking.bundle import DataBundle
from agent_reranking.io import read_jsonl, sha256_file
from agent_reranking.metrics import evaluate
from agent_reranking.rerank import all_rankings
from agent_reranking.runner import _profile_payload


CONDITIONS = {
    "full": {
        "components": ["history", "unique_tastes", "social_traits", "demographics"],
        "profile_dir": "repro50_legacy_full",
        "legacy_run": ("all_ratings_ro_original_code_full_no_cache_reproduction/"
                       "20261102_1238_mf-lightgcn-multivae_gpt-4o-mini_c876396c"),
        "expected_keys": ["demographics", "interaction_history", "persona_summary", "user_id"],
    },
    "no_demographics": {
        "components": ["history", "unique_tastes", "social_traits"],
        "profile_dir": "repro50_legacy_no_demographics",
        "legacy_run": ("all_ratings_ro_mf_v3_motive_v4_50_no_demographics_experiments/"
                       "20261102_1241_mf-lightgcn-multivae_gpt-4o-mini_683ddbd9"),
        "expected_keys": ["interaction_history", "persona_summary", "user_id"],
    },
    "no_interaction_history": {
        "components": ["unique_tastes", "social_traits", "demographics"],
        "profile_dir": "repro50_legacy_no_interaction_history",
        "legacy_run": ("all_ratings_ro_mf_v3_motive_v4_50_no_history_experiments/"
                       "20261102_1245_mf-lightgcn-multivae_gpt-4o-mini_c6d6c002"),
        "expected_keys": ["demographics", "persona_summary", "user_id"],
    },
    "no_persona": {
        "components": ["history", "demographics"],
        "profile_dir": "repro50_legacy_no_persona",
        "legacy_run": ("all_ratings_ro_mf_v3_motive_v4_50_no_persona_experiments/"
                       "20261102_1249_mf-lightgcn-multivae_gpt-4o-mini_6de2d1d3"),
        "expected_keys": ["demographics", "interaction_history", "user_id"],
    },
}


def _maximum_metric_delta(current, legacy):
    return max(abs(current[key] - legacy[key]) for key in current)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", default="data/derived/repro50")
    parser.add_argument("--profiles-root", default="artifacts/profiles")
    parser.add_argument("--legacy-outputs-root", default="../outputs")
    parser.add_argument("--legacy-prompts-root", default="../prompts")
    args = parser.parse_args()

    bundle = DataBundle(args.bundle)
    profiles_root = Path(args.profiles_root)
    legacy_outputs = Path(args.legacy_outputs_root)
    report = {"bundle": bundle.summary(), "conditions": {}}

    stage_map = {
        "sampled_baseline": "sampled_baseline",
        "click_only": "click_rerank",
        "converted_then_original": "conversion_rerank",
    }
    for condition, spec in CONDITIONS.items():
        profiles = {int(row["user_id"]): row for row in read_jsonl(
            profiles_root / spec["profile_dir"] / "profiles.jsonl")}
        payload_mismatches = []
        for user in bundle.users:
            payload = _profile_payload(
                profiles[user], spec["components"], protocol="legacy_combined")
            if sorted(payload) != spec["expected_keys"]:
                payload_mismatches.append(user)

        cases = read_jsonl(legacy_outputs / spec["legacy_run"] / "cases.jsonl")
        candidate_id_mismatches = 0
        ranking_mismatches = {stage: 0 for stage in stage_map}
        max_score_delta = 0.0
        max_metric_delta = 0.0
        for case in cases:
            key = (case["model"], int(case["user_id"]))
            candidate = bundle.candidates[key]
            if candidate["item_ids"] != case["candidate_ids"]:
                candidate_id_mismatches += 1
            max_score_delta = max(max_score_delta, *(
                abs(left - right) for left, right in
                zip(candidate["scores"], case["candidate_scores"])))
            current_rankings = all_rankings(candidate, {
                "clicked_item_ids": case["clicked_item_ids"],
                "converted_item_ids": case["converted_item_ids"],
            }, 10)
            heldout = bundle.labels[key[1]]["heldout_items"]
            for current_stage, legacy_stage in stage_map.items():
                if current_rankings[current_stage] != case["rankings"][legacy_stage]:
                    ranking_mismatches[current_stage] += 1
                current_metrics = evaluate(
                    current_rankings[current_stage], candidate["item_ids"], heldout, 10)
                max_metric_delta = max(
                    max_metric_delta,
                    _maximum_metric_delta(current_metrics, case["metrics"][legacy_stage]))

        report["conditions"][condition] = {
            "num_profiles": len(profiles),
            "profile_payload_key_mismatches": payload_mismatches,
            "num_legacy_cases_replayed": len(cases),
            "candidate_id_order_mismatches": candidate_id_mismatches,
            "maximum_candidate_score_absolute_delta": max_score_delta,
            "ranking_mismatches": ranking_mismatches,
            "maximum_metric_absolute_delta": max_metric_delta,
        }

    prompt_root = Path(__file__).resolve().parents[1] / "prompts"
    legacy_prompt_root = Path(args.legacy_prompts_root)
    report["action_prompts"] = {
        "click_current": sha256_file(
            prompt_root / "legacy/click_behavior_motive_assessment_v1.txt"),
        "click_legacy": sha256_file(
            legacy_prompt_root / "click_behavior_v4_motive_assessment.txt"),
        "conversion_current": sha256_file(
            prompt_root / "legacy/conversion_behavior_motive_assessment_v1.txt"),
        "conversion_legacy": sha256_file(
            legacy_prompt_root / "conversion_behavior_v4_motive_assessment.txt"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
