"""Render real-input v3 approval examples using only an offline mock client."""

import argparse
import csv
import json
import random
import tempfile
import subprocess
from pathlib import Path

from agent_reranking.agent import TwoStageAgent
from agent_reranking.bundle import DataBundle
from agent_reranking.client import MockClient, OpenAICompatibleClient
from agent_reranking.io import read_jsonl, sha256_file, write_csv, write_json
from agent_reranking.profiles import _runtime_history_sample, _sample, generate_profiles
from agent_reranking.runner import _profile_payload, match_history_ratings


class PreviewClient(MockClient):
    def __init__(self):
        super().__init__()
        self.requests = {}

    def respond_json(self, system, user, schema, name):
        body = OpenAICompatibleClient.request_body(system, user, schema, name, "gpt-4o-mini", 0.0)
        self.requests[name] = {"system_prompt": system, "payload": json.loads(user)
                               if name != "ours_profile" else user,
                               "response_format": body["response_format"]}
        return super().respond_json(system, user, schema, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--users-file", required=True)
    parser.add_argument("--reference-profiles", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    bundle = DataBundle(args.bundle)
    with Path(args.users_file).open(newline="") as source:
        users = [int(row["user_id"]) for row in csv.DictReader(source)]
    if len(users) != 1000 or len(set(users)) != 1000:
        raise ValueError("Expected the fixed 1,000-user panel")
    reference = {int(row["user_id"]): row for row in
                 read_jsonl(Path(args.reference_profiles) / "profile_manifests.jsonl")}
    for user in users:
        rows = bundle.histories[user]["train_interactions"]
        for field, sample in (
            ("history_item_ids", _runtime_history_sample(rows, user, 42, 10)),
            ("sampled_item_ids", _sample(rows, user, 42, 25, "ours-v1")),
        ):
            if [row["item_id"] for row in sample] != reference[user][field]:
                raise ValueError(f"Reference sample differs for user {user}: {field}")
    pilot = sorted(random.Random(42).sample(users, 100))
    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    write_csv(root.parent / "pilot100/users_100_seed42.csv",
              [{"user_id": user} for user in pilot], ["user_id"])
    client = PreviewClient()
    with tempfile.TemporaryDirectory() as temporary:
        generate_profiles(bundle, client, selected_user_ids=[pilot[0]], output_dir=temporary,
                          prompt_version="ours_profile_v3_debiased")
        profile = read_jsonl(Path(temporary) / "profiles.jsonl")[0]
        manifest = read_jsonl(Path(temporary) / "profile_manifests.jsonl")[0]
        user = profile["user_id"]
        for field in ("history_item_ids", "sampled_item_ids"):
            if manifest[field] != reference[user][field]:
                raise ValueError(f"Reference history sample differs: {field}")
        profile = match_history_ratings(profile, manifest, bundle.histories[user]["train_interactions"])
        payload = _profile_payload(profile,
            ["history", "unique_tastes", "social_traits", "demographics"],
            "separated", "behavior-v3-debiased")
        actions, _ = TwoStageAgent(client, prompt_version="behavior-v3-debiased").simulate(
            payload, bundle.candidates[("MF", user)], bundle.catalog, model="MF")
    for name, request in client.requests.items():
        stage = {"ours_profile": "profile", "debiased_click_selection": "click",
                 "debiased_conversion_selection": "conversion"}[name]
        write_json(root / f"{stage}_example.json", request)
    prompt_root = Path(__file__).resolve().parents[1] / "prompts"
    names = ["click_behavior_v3_debiased.txt", "conversion_behavior_v3_debiased.txt",
             "profile_ours_v3_debiased_system.txt", "profile_ours_v3_debiased_user.txt"]
    write_json(root / "approval_required.json", {
        "status": "awaiting_user_approval_before_any_paid_call", "paid_calls": 0,
        "example_kind": "Real panel inputs; mock persona and behavior, not experiment results",
        "reference_history_samples_verified": len(users),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=prompt_root.parent, text=True).strip(),
        "shuffle_rule": "SHA256 of compact JSON [42, model, user_id]; clicked list filters the same permutation",
        "user_id": user, "model": "MF", "pilot_users": pilot,
        "shown_candidate_item_ids": actions["shown_candidate_item_ids"],
        "prompt_sha256": {name: sha256_file(prompt_root / name) for name in names}})
    sections = ["# V3 Approval Packet", "",
        "Status: awaiting explicit user OK before any paid call. Paid calls: 0.",
        "", "All 1,000 users' 10-item runtime and 25-item taste samples match the reference manifests.",
        "The example uses real inputs for user 31 (or the smallest pilot user) and MF.",
        "Persona and behavior responses are mock fixtures, not model judgments or experiment results.",
        "The mock persona has empty tastes; the two clicked movies only exercise conversion rendering.",
        "No pilot Recall or NDCG has been calculated. The protocol is not frozen until after pilot checks.",
        "", "## Prompt Files", ""]
    for name in names:
        sections.extend([f"### {name}", "", "```text",
                         (prompt_root / name).read_text().rstrip(), "```", ""])
    sections.extend(["## Rendered Requests", ""])
    for stage in ("profile", "click", "conversion"):
        sections.extend([f"### {stage}", "", "```json",
                         (root / f"{stage}_example.json").read_text().rstrip(), "```", ""])
    (root / "APPROVAL.md").write_text("\n".join(sections), encoding="utf-8")
    print(json.dumps({"status": "awaiting_user_approval", "paid_calls": 0,
                      "user_id": user, "directory": str(root)}, indent=2))


if __name__ == "__main__":
    main()