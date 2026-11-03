import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import ValidationError

from agent_reranking.agent import FULL_SLATE_CONTEXT, TwoStageAgent, _instruction
from agent_reranking.client import OpenAICompatibleClient


class LegacyRequestParityTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.click_template = (root / "prompts/click_behavior_motive_assessment.txt").read_text(
            encoding="utf-8").strip()
        self.conversion_template = (
            root / "prompts/conversion_behavior_motive_assessment.txt").read_text(
                encoding="utf-8").strip()
        self.profile = {"user_id": 153,
                        "interaction_history": [{"title": "Fargo", "release_year": "1996",
                                                  "genres": ["Crime", "Drama"]}],
                        "persona_summary": "Likes comedy. Social traits: selective viewer."}
        self.items = [{"item_id": 11, "title": "Movie A", "release_year": "1999",
                       "genres": ["Comedy"]},
                      {"item_id": 22, "title": "Movie B", "release_year": "2000",
                       "genres": ["Drama"]}]

    def test_rendered_prompts_use_exact_legacy_substitutions(self):
        click = self.click_template.replace("{history_instruction}", _instruction(self.profile))
        conversion = self.conversion_template.replace(
            "{history_instruction}", _instruction(self.profile)).replace(
            "{conversion_context_instruction}", FULL_SLATE_CONTEXT)
        self.assertNotIn("{history_instruction}", click)
        self.assertNotIn("{conversion_context_instruction}", conversion)
        self.assertIn("it does not provide recommender scores or ranks", conversion)
        self.assertIn("detailed metadata for those movies", conversion)

    def test_action_prompt_hashes_are_recorded(self):
        agent = TwoStageAgent(type("Client", (), {})())
        self.assertEqual(agent.prompt_hashes, {
            "click": "7af5392a64f8f7577bcf2f7e1262580f8f3d5039cbd3809c497d236308275b50",
            "conversion": "c5d9ccd1b029ab7cda342be3b853d8a1ad151b9386cca623caa9c4dcd38e5e1e",
        })

    def test_request_body_matches_frozen_legacy_shape(self):
        system = self.click_template.replace("{history_instruction}", _instruction(self.profile))
        user = json.dumps({"stage": "click", "profile": self.profile, "items": self.items,
                           "retry_feedback": None}, ensure_ascii=False)
        body = OpenAICompatibleClient.request_body(
            system, user, None, "click_selection", "gpt-4o-mini", 0.0)
        self.assertEqual(list(body), ["model", "temperature", "messages", "response_format"])
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["messages"][1]["content"], user)

    def test_retry_instruction_and_enum_match_legacy_protocol(self):
        feedback = "click_motives[11] must contain at most 20 words"
        system = TwoStageAgent._retry_system("SYSTEM", feedback)
        self.assertEqual(system, "SYSTEM\n\nThe previous response failed validation: " + feedback
            + " Return a corrected complete JSON object. Do not repeat the invalid format or wording."
            + " Rewrite every motive and decision_note using no more than 15 space-separated words."
              " Count the words before returning the complete JSON.")
        payload = {"stage": "conversion", "profile": self.profile,
                   "candidate_slate": self.items, "clicked_item_ids": [11],
                   "clicked_items": [self.items[0]], "click_motives": {"11": "Comedy cue"},
                   "retry_feedback": "invalid ID"}
        body = OpenAICompatibleClient.request_body(
            "SYSTEM", json.dumps(payload, ensure_ascii=False), None,
            "conversion_selection", "gpt-4o-mini", 0.0)
        item_schema = body["response_format"]["json_schema"]["schema"]["properties"][
            "converted_item_ids"]["items"]
        self.assertEqual(item_schema, {"type": "integer", "enum": [11]})

    def test_legacy_sentence_validation_is_enforced(self):
        TwoStageAgent._validate_short_sentence("L.A. Confidential supports inspection.", "note")
        with self.assertRaisesRegex(ValueError, "at most 20 words"):
            TwoStageAgent._validate_short_sentence(" ".join(["word"] * 21), "note")
        with self.assertRaisesRegex(ValueError, "at most one sentence"):
            TwoStageAgent._validate_short_sentence("First sentence. Second sentence.", "note")

    def test_validation_feedback_matches_legacy_key_diagnostics(self):
        with self.assertRaisesRegex(
                ValueError,
                r"click_motives keys must exactly match clicked_item_ids; "
                r"missing keys=\['11'\]; extra keys=\[\]"):
            TwoStageAgent._validate_click(
                {"clicked_item_ids": [11], "click_motives": {}}, {11, 22})
        with self.assertRaisesRegex(ValidationError, "non-unique elements"):
            TwoStageAgent._validate_click(
                {"clicked_item_ids": [11, 11],
                 "click_motives": {"11": "Comedy makes this worth inspecting."}}, {11, 22})

    def test_missing_detail_metadata_uses_legacy_explicit_defaults(self):
        class RecordingClient:
            def __init__(inner):
                inner.calls = []
                inner.last_call = {"usage": {}, "estimated_cost_usd": 0.0}

            def respond_json(inner, system, user, schema, name):
                payload = json.loads(user)
                inner.calls.append(payload)
                if name == "click_selection":
                    return {"clicked_item_ids": [11],
                            "click_motives": {"11": "Comedy makes this worth inspecting."}}
                return {"converted_item_ids": [], "motive_assessments": {
                    "11": {"outcome": "insufficient",
                           "decision_note": "The details remain insufficient."}}}

        catalog = {11: {"item_id": 11, "title": "Movie 11", "release_year": "1999",
                        "genres": ["Comedy"]}}
        client = RecordingClient()
        TwoStageAgent(client).simulate(
            self.profile, {"item_ids": [11], "scores": [1.0]}, catalog)
        detail = client.calls[1]["clicked_items"][0]
        self.assertEqual(detail, {"item_id": 11, "title": "Movie 11",
            "release_year": "1999", "genres": ["Comedy"], "overview": "unknown",
            "director": "unknown", "cast": [], "release_date": "unknown",
            "language": "unknown", "country": []})

    def test_full_chain_request_bytes_match_frozen_legacy_hashes(self):
        responses = iter([
            {"clicked_item_ids": [11],
             "click_motives": {"11": " ".join(["word"] * 21)}},
            {"clicked_item_ids": [11],
             "click_motives": {"11": "Comedy makes this worth inspecting."}},
            {"converted_item_ids": [11], "motive_assessments": {
                "11": {"outcome": "confirmed", "decision_note": " ".join(["word"] * 21)}}},
            {"converted_item_ids": [11], "motive_assessments": {
                "11": {"outcome": "confirmed",
                       "decision_note": "The details support immediate viewing."}}},
        ])

        class RecordingClient:
            def __init__(self):
                self.bodies = []
                self.last_call = {"usage": {}, "estimated_cost_usd": 0.0}

            def respond_json(inner, system, user, schema, name):
                body = OpenAICompatibleClient.request_body(
                    system, user, schema, name, "gpt-4o-mini", 0.0)
                inner.bodies.append(json.dumps(body).encode())
                return next(responses)

        catalog = {
            item: {"item_id": item, "title": f"Movie {item}", "release_year": "1999",
                   "genres": ["Comedy"], "overview": "A comedy premise",
                   "director": "Director", "cast": ["Actor"],
                   "release_date": "1999-01-01", "language": "English",
                   "country": ["United States of America"]}
            for item in (11, 22)
        }
        client = RecordingClient()
        TwoStageAgent(client).simulate(
            self.profile, {"item_ids": [11, 22], "scores": [1.0, 0.5]}, catalog)
        self.assertEqual([hashlib.sha256(body).hexdigest() for body in client.bodies], [
            "4181441d0400a4adca6fc4be556f280aedb7447c41244705117ed760b7729389",
            "ecab70e6717e26fa23f9a789e56500e2b280e1e4af26d023103d48aa0f4b3023",
            "8712cf85fc78c16100c098d84b61b5826f35357604b8c7c882e8aea4fde07a85",
            "fb765bbe105bd5ecdfb47195e3e8f66f156c8dda253a67e537c25acd938dca83",
        ])
