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
        self.assertIn("checkpoint-training interactions", client.systems[0])
        self.assertIn("not this user's rating", client.systems[1])

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
