import unittest

from agent_reranking.bundle import select_users
from agent_reranking.runner import _profile_payload


class ProfilePayloadTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "user_id": 7,
            "interaction_history": [{"title": "Seen", "genres": ["Drama"]}],
            "unique_tastes": {"summary": "Likes drama", "liked_patterns": ["Drama"]},
            "social_traits": {"activity": {"level": 2}},
            "demographics": {"age": "25-34"},
            "legacy_persona_summary": "Likes drama. Social traits: activity is medium.",
        }

    def test_separated_protocol_uses_independent_keys_without_legacy_summary(self):
        value = _profile_payload(self.profile,
            ["history", "unique_tastes", "social_traits", "demographics"], "separated")
        self.assertEqual(set(value), {"user_id", "interaction_history", "unique_tastes",
                                      "social_traits", "demographics"})
        self.assertNotIn("persona_summary", value)

    def test_explicit_user_selection_is_reused_in_declared_order(self):
        self.assertEqual(select_users([1, 2, 3, 4], 2, [4, 2]), [4, 2])
        with self.assertRaisesRegex(ValueError, "absent from bundle"):
            select_users([1, 2, 3], None, [4])

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
