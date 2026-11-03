import csv
import hashlib
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL_ROOT = ROOT / "data" / "panels"


def _rows(path):
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PanelArtifactTests(unittest.TestCase):
    def test_committed_panel_is_seed42_srs_from_joint_eligible_population(self):
        eligible_path = PANEL_ROOT / "eligible_users_joint_top20.csv"
        panel_path = PANEL_ROOT / "users_1000_seed42.csv"
        eligible = sorted(_rows(eligible_path), key=lambda row: int(row["user_id"]))
        panel = _rows(panel_path)
        eligible_manifest = json.loads((PANEL_ROOT /
            "eligible_users_joint_top20.manifest.json").read_text(encoding="utf-8"))
        panel_manifest = json.loads((PANEL_ROOT /
            "users_1000_seed42.manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(len(eligible), 4588)
        self.assertEqual(len(panel), 1000)
        self.assertEqual(eligible_manifest["eligible_after_history_filter"], len(eligible))
        self.assertEqual(eligible_manifest["users_csv_sha256"], _sha256(eligible_path))
        self.assertEqual(panel_manifest["source_users_sha256"], _sha256(eligible_path))
        self.assertEqual(panel_manifest["panel_sha256"], _sha256(panel_path))

        expected_ids = sorted(int(row["user_id"]) for row in
                              random.Random(42).sample(eligible, 1000))
        actual_ids = [int(row["user_id"]) for row in panel]
        self.assertEqual(actual_ids, expected_ids)
        self.assertEqual(len(set(actual_ids)), 1000)
        self.assertGreaterEqual(min(int(row["train_interaction_count"])
                                    for row in panel), 10)
        for field in ("mf_positive_count_top20", "lightgcn_positive_count_top20",
                      "multivae_positive_count_top20"):
            self.assertGreaterEqual(min(int(row[field]) for row in panel), 1)
