"""Read and validate a materialized experiment bundle."""

from pathlib import Path

from .io import read_jsonl, sha256_file


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

    @property
    def users(self):
        return list(self.histories)

    def movie(self, item_id, detail=False):
        row = dict(self.catalog[int(item_id)])
        fields = ("item_id", "title", "release_year", "genres", "overview", "director",
                  "cast", "release_date", "language", "country") if detail else (
                      "item_id", "title", "release_year", "genres")
        return {key: row[key] for key in fields if key in row}

