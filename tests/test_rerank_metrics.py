import json
import unittest

from jsonschema import ValidationError

from agent_reranking.metrics import evaluate
from agent_reranking.rerank import all_rankings
from agent_reranking.agent import TwoStageAgent


class RerankMetricTests(unittest.TestCase):
    def test_v2_agent_exposes_train_only_average_rating_at_both_stages(self):
        class RecordingClient:
            def __init__(inner):
                inner.calls = []
                inner.systems = []
                inner.last_call = {"usage": {}, "estimated_cost_usd": 0.0}

            def respond_json(inner, system, user, schema, name):
                inner.systems.append(system)
                inner.calls.append(json.loads(user))
                if name == "click_selection":
                    return {"clicked_item_ids": [3],
                            "click_motives": {"3": "Strong aggregate rating supports inspection."}}
                return {"converted_item_ids": [], "motive_assessments": {
                    "3": {"outcome": "insufficient",
                          "decision_note": "The details remain insufficient for viewing."}}}

        catalog = {3: {"item_id": 3, "title": "Movie", "release_year": "1999",
                       "genres": ["Drama"], "average_rating": 4.27}}
        client = RecordingClient()
        agent = TwoStageAgent(client, prompt_version="behavior-motive-assessment-v2")
        agent.simulate({"user_id": 7}, {"item_ids": [3], "scores": [1.0]}, catalog)
        self.assertEqual(client.calls[0]["items"][0]["average_rating"], 4.27)
        self.assertEqual(client.calls[1]["candidate_slate"][0]["average_rating"], 4.27)
        self.assertEqual(client.calls[1]["clicked_items"][0]["average_rating"], 4.27)
        self.assertIn("mean 1–5 rating for that movie", client.systems[0])
        self.assertNotIn("checkpoint-training", client.systems[0])
        self.assertIn("not this user's rating", client.systems[1])

    def test_social_trait_protocol_exposes_rating_and_routes_each_trait(self):
        agent = TwoStageAgent(type("Client", (), {})(),
                              prompt_version="behavior-social-traits")
        self.assertTrue(agent.exposes_average_rating)
        for trait in ("Activity", "Diversity", "Conformity"):
            self.assertIn(trait, agent.click_prompt)
            self.assertIn(trait, agent.conversion_prompt)
        self.assertIn("do not infer or invent trait levels", agent.click_prompt)
        self.assertNotIn("checkpoint-training", agent.click_prompt)
        self.assertNotIn("demographics as a stereotype", agent.conversion_prompt)

    def test_align_rating_protocol_runs_and_records_structured_decisions(self):
        from agent_reranking.client import MockClient

        catalog = {
            item: {"item_id": item, "title": f"Movie {item}", "release_year": "1999",
                   "genres": ["Drama"], "average_rating": 4.0,
                   "overview": "A detailed story"}
            for item in (3, 4, 5)
        }
        agent = TwoStageAgent(
            MockClient(), prompt_version="behavior-align-rating-social-traits")
        result, attempts = agent.simulate(
            {"user_id": 7}, {"item_ids": [3, 4, 5], "scores": [3.0, 2.0, 1.0]}, catalog)
        self.assertEqual(result["click_count"], 2)
        self.assertEqual(set(result["candidate_assessments"]), {"3", "4", "5"})
        self.assertEqual(result["watch_decision"], "watch")
        self.assertEqual(len(result["converted_item_ids"]), 1)
        self.assertEqual(result["motive_assessments"]["3"]["predicted_rating"], 4)
        self.assertEqual([attempt["status"] for attempt in attempts], ["valid", "valid"])

    def test_align_rating_conversion_nests_each_click_motive_in_its_movie(self):
        class RecordingClient:
            def __init__(inner):
                inner.calls = []
                inner.last_call = {"usage": {}, "estimated_cost_usd": 0.0}

            def respond_json(inner, system, user, schema, name):
                payload = json.loads(user)
                inner.calls.append(payload)
                if name == "alignment_click_selection":
                    return {
                        "candidate_assessments": {
                            "3": {"alignment": "strong",
                                  "evidence": "Drama matches established tastes"}},
                        "clicked_item_ids": [3],
                    }
                return {
                    "watch_decision": "not_ready", "converted_item_ids": [],
                    "motive_assessments": {"3": {
                        "outcome": "insufficient", "predicted_rating": 3,
                        "reason": "The details provide mixed preference evidence"}},
                    "decision_reason": "No movie is sufficiently compelling to start now",
                }

        catalog = {3: {"item_id": 3, "title": "Movie", "release_year": "1999",
                       "genres": ["Drama"], "average_rating": 4.0, "overview": "Story"}}
        client = RecordingClient()
        result, _ = TwoStageAgent(
            client, prompt_version="behavior-align-rating-social-traits").simulate(
                {"user_id": 7}, {"item_ids": [3], "scores": [1.0]}, catalog)
        self.assertEqual(result["click_count"], 1)
        self.assertEqual(client.calls[1]["clicked_items"][0]["click_hypothesis"],
                         "Drama matches established tastes")
        self.assertNotIn("click_motives", client.calls[1])

    def test_align_rating_protocol_enforces_click_and_conversion_invariants(self):
        alignments = {
            "3": {"alignment": "strong", "evidence": "Established drama preference"},
            "4": {"alignment": "none", "evidence": "No supported preference connection"},
        }
        with self.assertRaisesRegex(ValueError, "alignment=none"):
            TwoStageAgent._validate_align_click({
                "candidate_assessments": alignments,
                "clicked_item_ids": [4]},
                {3, 4})

        assessments = {"3": {
            "outcome": "confirmed", "predicted_rating": 4,
            "reason": "The details fit established preferences",
        }}
        with self.assertRaisesRegex(ValueError, "not_ready requires an empty"):
            TwoStageAgent._validate_rating_conversion({
                "watch_decision": "not_ready", "converted_item_ids": [3],
                "motive_assessments": assessments,
                "decision_reason": "No option clears the viewing threshold",
            }, [3])

    def test_align_click_request_uses_strict_schema_for_every_candidate(self):
        from agent_reranking.client import OpenAICompatibleClient

        payload = json.dumps({
            "items": [{"item_id": 3}, {"item_id": 4}], "retry_feedback": None})
        body = OpenAICompatibleClient.request_body(
            "system", payload, None, "alignment_click_selection", "model", 0.0)
        response_format = body["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        schema = response_format["json_schema"]["schema"]
        candidate_schema = schema["properties"]["candidate_assessments"]
        self.assertEqual(set(candidate_schema["required"]), {"3", "4"})
        self.assertEqual(
            set(candidate_schema["properties"]["3"]["required"]),
            {"alignment", "evidence"})

    def test_object_shaped_agent_output_can_be_canonicalized_for_import_only(self):
        click = TwoStageAgent._canonicalize_click({
            "clicked_item_ids": [{"item_id": 3, "click_motive": "Genre match"}],
            "click_motives": []})
        self.assertEqual(click, {"clicked_item_ids": [3],
                                "click_motives": {"3": "Genre match"}})
        conversion = TwoStageAgent._canonicalize_conversion({
            "converted_item_ids": [{"item_id": 3}],
            "motive_assessments": [{"item_id": 3, "outcome": "confirmed",
                                     "decision_note": "Details support viewing"}]})
        self.assertEqual(conversion["converted_item_ids"], [3])
        self.assertEqual(conversion["motive_assessments"]["3"]["outcome"], "confirmed")

    def test_runtime_rejects_nonlegacy_object_shaped_selection(self):
        with self.assertRaises((TypeError, ValueError, ValidationError)):
            TwoStageAgent._validate_click({
                "clicked_item_ids": [{"item_id": 3}],
                "click_motives": {"3": "Genre match"}}, {3})

    def test_one_action_supports_all_policies_without_more_agent_calls(self):
        candidate = {"item_ids": [1, 2, 3, 4], "scores": [4.0, 3.0, 2.0, 1.0]}
        actions = {"clicked_item_ids": [3, 4], "converted_item_ids": [4]}
        rankings = all_rankings(candidate, actions, 3)
        self.assertEqual(rankings["sampled_baseline"], [1, 2, 3])
        self.assertEqual(rankings["click_only"], [3, 4, 1])
        self.assertEqual(rankings["converted_then_original"], [4, 1, 2])
        self.assertEqual(rankings["three_tier"], [4, 3, 1])

    def test_metrics_treat_every_heldout_interaction_as_primary_relevance(self):
        heldout = [{"item_id": 2, "rating": 1}, {"item_id": 4, "rating": 5}]
        row = evaluate([2, 1], [1, 2, 3, 4], heldout, 2)
        self.assertEqual(row["recall@2"], 0.5)
        self.assertEqual(row["candidate_recall@4"], 1.0)
