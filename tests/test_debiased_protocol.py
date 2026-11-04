import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from jsonschema import ValidationError

from agent_reranking.agent import TwoStageAgent, presentation_order
from agent_reranking.client import MockClient, OpenAICompatibleClient
from agent_reranking.config import load_config
from agent_reranking.io import read_jsonl
from agent_reranking.profiles import generate_profiles
from agent_reranking.runner import _profile_payload, match_history_ratings, run


class DebiasedProtocolTests(unittest.TestCase):
    def test_presentation_is_deterministic_without_mutating_candidates(self):
        items = list(range(20))
        original = list(items)
        order = presentation_order(items, "MF", 153)
        self.assertEqual(order, presentation_order(items, "MF", 153))
        self.assertNotEqual(order, items)
        self.assertNotEqual(order, presentation_order(items, "LightGCN", 153))
        self.assertEqual(set(order), set(items))
        self.assertEqual(items, original)

    def test_interest_schema_and_click_threshold(self):
        value = {"candidate_assessments": {
            "11": {"interest": 3, "evidence": "Matches your liked comedies"}},
            "clicked_item_ids": [11]}
        TwoStageAgent._validate_debiased_click(value, {11})
        invalid = copy.deepcopy(value)
        invalid["candidate_assessments"]["11"]["interest"] = 2
        with self.assertRaisesRegex(ValueError, "interest >= 3"):
            TwoStageAgent._validate_debiased_click(invalid, {11})
        for interest in (0, 6, True, 3.5):
            invalid["candidate_assessments"]["11"]["interest"] = interest
            with self.assertRaises(ValidationError):
                TwoStageAgent._validate_debiased_click(invalid, {11})
        with self.assertRaisesRegex(ValueError, "keys must exactly match"):
            TwoStageAgent._validate_debiased_click(value, {11, 22})

    def test_watch_likelihood_replaces_predicted_rating(self):
        value = {"watch_decision": "watch", "converted_item_ids": [11],
                 "motive_assessments": {"11": {"outcome": "confirmed",
                     "watch_likelihood": 4, "reason": "Matches your liked comedies"}},
                 "decision_reason": "Your history supports watching this comedy"}
        TwoStageAgent._validate_debiased_conversion(value, [11])
        value["motive_assessments"]["11"]["predicted_rating"] = 4
        with self.assertRaises(ValidationError):
            TwoStageAgent._validate_debiased_conversion(value, [11])

    def test_both_payloads_exclude_aggregate_ratings_and_conformity(self):
        class RecordingClient(MockClient):
            def __init__(self):
                super().__init__()
                self.requests = []

            def respond_json(self, system, user, schema, name):
                body = OpenAICompatibleClient.request_body(system, user, schema, name, "test", 0)
                self.requests.append(body)
                return super().respond_json(system, user, schema, name)

        raw = {"user_id": 7, "interaction_history": [{"title": "Seen", "average_rating": 4.9}],
               "social_traits": {name: {"level": 2, "value": 10}
                                  for name in ("activity", "diversity", "conformity")}}
        raw = match_history_ratings(raw, {"history_item_ids": [19]},
                                    [{"item_id": 19, "rating": 2}])
        profile = _profile_payload(raw, ["history", "social_traits"], "separated",
                                   "behavior-v3-debiased")
        self.assertEqual(profile["interaction_history"][0]["user_rating"], 2)
        self.assertNotIn("conformity", json.dumps(profile).lower())
        catalog = {item: {"item_id": item, "title": f"Movie {item}", "genres": ["Drama"],
                          "release_year": "1999", "average_rating": 4.99}
                   for item in range(20)}
        candidate = {"item_ids": list(range(20)), "scores": list(range(20))}
        original = copy.deepcopy(candidate)
        client = RecordingClient()
        result, calls = TwoStageAgent(client, prompt_version="behavior-v3-debiased").simulate(
            profile, candidate, catalog, model="MF")
        self.assertEqual(len(client.requests), 2)
        for body in client.requests:
            serialized = json.dumps(body)
            self.assertNotIn("average_rating", serialized)
            self.assertNotIn("predicted_rating", serialized)
            self.assertNotIn("conformity", serialized.lower())
            payload = json.loads(body["messages"][1]["content"])
            self.assertEqual(payload["profile"]["interaction_history"][0]["user_rating"], 2)
            field = "items" if payload["stage"] == "click" else "candidate_slate"
            self.assertEqual([item["item_id"] for item in payload[field]],
                             result["shown_candidate_item_ids"])
        self.assertEqual(candidate, original)
        self.assertEqual(result["shown_clicked_item_ids"], result["clicked_item_ids"])
        self.assertEqual([row["status"] for row in calls], ["valid", "valid"])
        assessments = client.requests[0]["response_format"]["json_schema"]["schema"][
            "properties"]["candidate_assessments"]
        self.assertEqual(set(assessments["required"]), {str(item) for item in range(20)})
        self.assertFalse(assessments["additionalProperties"])

    def test_history_ratings_follow_manifest_not_training_order(self):
        profile = {"interaction_history": [{"title": "First"}, {"title": "Second"}]}
        manifest = {"history_item_ids": [22, 11]}
        rows = [{"item_id": 11, "rating": 1}, {"item_id": 22, "rating": 5}]
        matched = match_history_ratings(profile, manifest, rows)
        self.assertEqual([movie["user_rating"] for movie in matched["interaction_history"]], [5, 1])
        self.assertNotIn("user_rating", profile["interaction_history"][0])
        with self.assertRaisesRegex(ValueError, "Missing or invalid"):
            match_history_ratings(profile, manifest, rows[:1])

    def test_all_old_protocol_requests_match_pre_v3_frozen_bytes(self):
        expected = {
            "behavior-motive-assessment-v1": [
                "b219ab94297195039b4b37f3e1895e03065cbb09d03b313ddb66ab8f431285a2",
                "8be9d603e0b6f0a35f2460d2dfb7136e3bf6d8682fb184ac278f1e18f3961afb"],
            "behavior-motive-assessment-v2": [
                "8fb3ff15d7fca86e7cb754bc611b9e718aebb1ae795fa5446db5ea6ac641d02d",
                "290e1f937cd1cccfe9b7e1294747bb4988de816122432bf0b49ab91fece7abad"],
            "behavior-social-traits": [
                "331e2b96f29309b4422fd9ac09f9f57750bb032b488a649081924aec4edc0ead",
                "2207ce8d292c5d1be45e8aed32109bb64696b6824f0bb428e007f93a6a0c1f96"],
            "behavior-align-rating-social-traits": [
                "7bed3e2515fcf21337176c5ca348c47ba0d55f636f65138eeb41837b094efcf0",
                "d27cf56df9f776cb9d01779e23593f36749aaa27fa10e62f8bc21f2b9a2ef4cc"],
        }

        class RecordingClient(MockClient):
            def __init__(self):
                super().__init__()
                self.hashes = []

            def respond_json(self, system, user, schema, name):
                body = OpenAICompatibleClient.request_body(system, user, schema, name,
                                                            "gpt-4o-mini", 0.0)
                self.hashes.append(hashlib.sha256(json.dumps(body).encode()).hexdigest())
                return super().respond_json(system, user, schema, name)

        catalog = {item: {"item_id": item, "title": f"Movie {item}", "release_year": "1999",
                          "genres": ["Drama"], "average_rating": 4.0,
                          "overview": "A detailed story"} for item in (3, 4, 5)}
        for version, hashes in expected.items():
            with self.subTest(version=version):
                client = RecordingClient()
                TwoStageAgent(client, prompt_version=version).simulate(
                    {"user_id": 7}, {"item_ids": [3, 4, 5], "scores": [3.0, 2.0, 1.0]}, catalog)
                self.assertEqual(client.hashes, hashes)

    def test_debiased_profiles_and_pilot_never_evaluate_metrics(self):
        traits = {name: {"level": 2, "value": 10}
                  for name in ("activity", "diversity", "conformity")}
        catalog = {item: {"item_id": item, "title": f"Movie {item}", "release_year": "1999",
                          "genres": ["Drama"], "average_rating": 4.0}
                   for item in range(1, 21)}
        bundle = SimpleNamespace(
            users=[7], social_traits={7: traits}, trait_thresholds={},
            trait_population_scope="materialized_panel", manifest={"bundle_id": "test"},
            histories={7: {"raw_user_id": "7", "demographics": {},
                           "train_interactions": [{"item_id": 1, "rating": 2, "timestamp": 1}]}},
            movie=lambda item, detail=False: dict(catalog[item]), catalog=catalog,
            candidates={("MF", 7): {"item_ids": list(range(1, 21)), "scores": list(range(20))}})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profiles = root / "profiles"
            generate_profiles(bundle, MockClient(), output_dir=profiles,
                              prompt_version="ours_profile_v3_debiased")
            profile = read_jsonl(profiles / "profiles.jsonl")[0]
            self.assertEqual(profile["interaction_history"][0]["user_rating"], 2)
            self.assertNotIn("average_rating", json.dumps(profile))
            self.assertNotIn("conformity", profile["social_traits"])
            version = json.loads((profiles / "run_manifest.json").read_text())["configuration"]
            self.assertEqual(version["profile_prompt_version"], "ours_profile_v3_debiased")
            config = load_config(Path(__file__).resolve().parents[1] / "configs/default.yaml")
            config.update(llm_provider="mock", models=["MF"], num_users=1,
                          prompt_version="behavior-v3-debiased", evaluate_metrics=False,
                          profile_protocol="separated", output_root=str(root / "runs"))
            with patch("agent_reranking.runner.DataBundle", return_value=bundle), \
                 patch("agent_reranking.runner.evaluate", side_effect=AssertionError("Pilot metric leak")), \
                 patch("agent_reranking.runner.rating_strata", side_effect=AssertionError("Pilot label leak")):
                result = run(config, "unused", profiles / "profiles.jsonl")
            self.assertEqual(result["completed_cases"], 1)
            run_root = Path(result["run_dir"])
            self.assertEqual(len((run_root / "per_user_metrics.csv").read_text().splitlines()), 1)
            actions = read_jsonl(run_root / "actions.jsonl")[0]["actions"]
            self.assertEqual(len(actions["shown_candidate_item_ids"]), 20)

    def test_zero_clicks_skip_conversion(self):
        class ZeroClickClient(MockClient):
            def respond_json(self, system, user, schema, name):
                if name != "debiased_click_selection":
                    raise AssertionError("Unexpected conversion call")
                return {"candidate_assessments": {"1": {"interest": 1,
                        "evidence": "No personal evidence supports opening this movie"}},
                        "clicked_item_ids": []}

        result, calls = TwoStageAgent(ZeroClickClient(), prompt_version="behavior-v3-debiased").simulate(
            {"user_id": 7}, {"item_ids": [1]}, {1: {"item_id": 1, "title": "Movie"}}, model="MF")
        self.assertEqual(result["watch_decision"], "not_ready")
        self.assertEqual(len(calls), 1)

    def test_transport_stop_saves_error_and_blocks_followup_calls(self):
        errors = [HTTPError("https://test.invalid", 429, "limited", {}, io.BytesIO(b"limited")),
                  URLError("offline"), TimeoutError("timeout")]
        for error in errors:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as temporary, \
                 patch("agent_reranking.client.api_key", return_value="fake-key"), \
                 patch("agent_reranking.client.urlopen", side_effect=error) as request:
                client = OpenAICompatibleClient("test", "https://test.invalid/v1",
                                                 stop_on_transport_error=True)
                client.transcript_dir = temporary
                with self.assertRaises((RuntimeError, URLError, TimeoutError)):
                    client.respond_json("system", "user", None)
                with self.assertRaisesRegex(RuntimeError, "safety stop"):
                    client.respond_json("system", "user", None)
                self.assertEqual(request.call_count, 1)
                rows = read_jsonl(Path(temporary) / "transcripts.jsonl")
                self.assertTrue(rows[0]["error"])
                self.assertEqual(rows[-1]["kind"], "safety_stop")