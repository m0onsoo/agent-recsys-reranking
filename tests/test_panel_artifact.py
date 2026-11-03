import csv
import hashlib
import json
import random
import unittest
from pathlib import Path

import yaml


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
        self.assertEqual(panel_manifest["source_manifest_sha256"], _sha256(
            PANEL_ROOT / "eligible_users_joint_top20.manifest.json"))
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

    def test_registry_metrics_match_saved_1000_user_evaluation(self):
        result = json.loads((ROOT / "results" /
            "ml1m_ro_n1000_seed42_baselines.json").read_text(encoding="utf-8"))
        registry_path = ROOT / "registry" / "models.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry_hash = _sha256(registry_path)
        eligible_manifest = json.loads((PANEL_ROOT /
            "eligible_users_joint_top20.manifest.json").read_text(encoding="utf-8"))
        panel_manifest = json.loads((PANEL_ROOT /
            "users_1000_seed42.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(eligible_manifest["model_registry_sha256"], registry_hash)
        self.assertEqual(panel_manifest["model_registry_sha256"], registry_hash)
        for entry in registry["models"]:
            saved = entry["joint_eligible_panel_1000_seed42_metrics"]
            measured = result["models"][entry["display_name"]]
            self.assertEqual(saved["test_users"], 1000)
            self.assertEqual(saved["panel_sha256"], result["panel_sha256"])
            self.assertEqual(saved["bundle_id"], result["bundle_id"])
            for metric in ("recall@10", "ndcg@10", "candidate_recall@20"):
                self.assertAlmostEqual(saved[metric], measured[metric], places=9)
