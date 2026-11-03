import unittest

from agent_reranking.bundle import select_users
from agent_reranking.runner import _profile_payload


class ProfilePayloadTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "user_id": 7,
            "interaction_history": [{"title": "Seen", "genres": ["Drama"]}],
            "unique_tastes": {"unique_tastes": [{"taste": "Drama",
                "reason": "Character-focused stories recur"}],
                "liked_patterns": ["Drama"], "disliked_patterns": []},
            "social_traits": {
                "activity": {"level": 2, "value": 150},
                "conformity": {"level": 3, "value": 1.5},
                "diversity": {"level": 1, "value": 8}},
            "demographics": {"age": "25", "gender": "F", "occupation": "12"},
            "legacy_persona_summary": "Likes drama. Social traits: activity is medium.",
        }

    def test_separated_protocol_uses_independent_keys_without_legacy_summary(self):
        value = _profile_payload(self.profile,
            ["history", "unique_tastes", "social_traits", "demographics"], "separated")
        self.assertEqual(set(value), {"user_id", "interaction_history", "unique_tastes",
                                      "social_traits", "demographics"})
        self.assertNotIn("persona_summary", value)
        self.assertEqual(value["demographics"], {
            "age": "25-34", "gender": "female", "occupation": "programmer"})
        self.assertEqual(value["unique_tastes"],
            "Unique tastes: Drama (Character-focused stories recur). "
            "Liked patterns: Drama. Disliked patterns: no repeated disliked pattern identified.")
        self.assertEqual(value["social_traits"],
            "Social traits: activity is occasional viewer (moderate movie-interaction frequency); "
            "conformity is independent critic (ratings often depart from average item ratings); "
            "diversity is selective viewer (genre choices are concentrated).")

    def test_explicit_user_selection_is_reused_in_declared_order(self):
        self.assertEqual(select_users([1, 2, 3, 4], 2, [4, 2]), [4, 2])
        with self.assertRaisesRegex(ValueError, "absent from bundle"):
            select_users([1, 2, 3], None, [4])

    def test_assigned_trait_level_changes_only_that_rendered_trait(self):
        original = _profile_payload(
            self.profile, ["social_traits"], "separated")["social_traits"]
        self.profile["social_traits"]["activity"]["assigned_level"] = 1
        intervened = _profile_payload(
            self.profile, ["social_traits"], "separated")["social_traits"]
        self.assertIn("activity is occasional viewer", original)
        self.assertIn("activity is infrequent viewer", intervened)
        self.assertIn("conformity is independent critic", intervened)
        self.assertIn("diversity is selective viewer", intervened)

    def test_legacy_protocol_combines_tastes_and_traits_once(self):
        value = _profile_payload(self.profile,
            ["history", "unique_tastes", "social_traits"], "legacy_combined")
        self.assertEqual(set(value), {"user_id", "interaction_history", "persona_summary"})
        self.assertNotIn("unique_tastes", value)
        self.assertNotIn("social_traits", value)

    def test_legacy_without_persona_has_no_taste_or_trait_input(self):
        value = _profile_payload(self.profile, ["history", "demographics"],
                                 "legacy_combined")
        self.assertEqual(set(value), {"user_id", "interaction_history", "demographics"})
