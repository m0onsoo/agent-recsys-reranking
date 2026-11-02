import unittest

from agent_reranking.metrics import evaluate
from agent_reranking.rerank import all_rankings
from agent_reranking.agent import TwoStageAgent


class RerankMetricTests(unittest.TestCase):
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
        with self.assertRaises((TypeError, ValueError)):
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
