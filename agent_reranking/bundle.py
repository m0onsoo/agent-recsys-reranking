"""Read and validate a materialized experiment bundle."""

from pathlib import Path

from .io import read_jsonl, sha256_file


def select_users(available_users, num_users=None, selected_user_ids=None):
    available = list(available_users)
    if selected_user_ids is None:
        return available[:num_users] if num_users is not None else available
    selected = [int(user) for user in selected_user_ids]
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("Selected user IDs must be nonempty and unique")
    missing = set(selected) - set(available)
    if missing:
        raise ValueError(f"Selected users are absent from bundle: {sorted(missing)}")
    return selected


class DataBundle:
    def __init__(self, root):
        self.root = Path(root).resolve()
        import json
        self.manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        for name, digest in self.manifest["files"].items():
            if sha256_file(self.root / name) != digest:
                raise ValueError(f"Bundle file hash mismatch: {name}")
        self.histories = {int(row["user_id"]): row for row in
                          read_jsonl(self.root / "train_interactions.jsonl")}
        self.labels = {int(row["user_id"]): row for row in
                       read_jsonl(self.root / "evaluation_labels.jsonl")}
        self.catalog = {int(row["item_id"]): row for row in
                        read_jsonl(self.root / "item_catalog.jsonl")}
        self.candidates = {(row["model"], int(row["user_id"])): row for row in
                           read_jsonl(self.root / "candidates.jsonl")}
        traits_path = self.root / "social_traits.json"
        if traits_path.is_file():
            import json
            value = json.loads(traits_path.read_text(encoding="utf-8"))
            self.social_traits = {int(key): row for key, row in value["users"].items()}
            self.trait_thresholds = value["thresholds"]
            self.trait_population_scope = value["population_scope"]
        else:
            self.social_traits = None
            self.trait_thresholds = None
            self.trait_population_scope = None
        self._validate_structure()

    def _validate_structure(self):
        schema_version = int(self.manifest.get("schema_version", 0))
        if schema_version not in (1, 2):
            raise ValueError(f"Unsupported bundle schema: {schema_version}")
        expected_users = set(self.histories)
        if not expected_users:
            raise ValueError("Bundle contains no users")
        if set(self.labels) != expected_users:
            raise ValueError("Evaluation-label users do not exactly match history users")
        models = tuple(self.manifest.get("models", ()))
        if not models:
            raise ValueError("Bundle manifest contains no models")
        expected_cases = {(model, user) for model in models for user in expected_users}
        if set(self.candidates) != expected_cases:
            raise ValueError("Candidate model-user cases do not exactly match the manifest")
        candidate_size = int(self.manifest["candidate_size"])
        for key, row in self.candidates.items():
            if len(row["item_ids"]) != candidate_size:
                raise ValueError(f"Candidate length differs from manifest: {key}")
            if len(row.get("scores", ())) != candidate_size:
                raise ValueError(f"Candidate scores are incomplete: {key}")
            if len(set(row["item_ids"])) != candidate_size:
                raise ValueError(f"Candidate items are not unique: {key}")
            missing = set(row["item_ids"]) - set(self.catalog)
            if missing:
                raise ValueError(f"Candidate items are absent from catalog: {key}: {missing}")
            if schema_version >= 2:
                for item in row["item_ids"]:
                    value = self.catalog[item].get("average_rating")
                    if value is not None and (not isinstance(value, (int, float))
                                              or not 1 <= value <= 5):
                        raise ValueError(
                            f"Invalid train-only average rating: {key}: item {item}")
        if int(self.manifest["num_users"]) != len(expected_users):
            raise ValueError("Bundle user count differs from manifest")
        if self.social_traits is not None and set(self.social_traits) != expected_users:
            raise ValueError("Social-trait users do not exactly match history users")

    def summary(self):
        return {
            "status": "valid",
            "bundle": str(self.root),
            "bundle_id": self.manifest.get("bundle_id"),
            "schema_version": self.manifest.get("schema_version"),
            "num_users": len(self.histories),
            "models": list(self.manifest["models"]),
            "candidate_size": int(self.manifest["candidate_size"]),
            "num_model_user_cases": len(self.candidates),
            "has_social_traits": self.social_traits is not None,
        }

    @property
    def users(self):
        return list(self.histories)

    def movie(self, item_id, detail=False):
        row = dict(self.catalog[int(item_id)])
        if detail:
            row = {**{"overview": "unknown", "director": "unknown", "cast": [],
                      "release_date": "unknown", "language": "unknown", "country": []},
                   **row}
        fields = ("item_id", "title", "release_year", "genres", "overview", "director",
                  "cast", "release_date", "language", "country") if detail else (
                      "item_id", "title", "release_year", "genres")
        return {key: row[key] for key in fields if key in row}

