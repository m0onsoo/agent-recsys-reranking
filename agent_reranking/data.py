"""Materialize a local, split-bound experiment bundle for a committed panel."""

import csv
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import yaml

from .checkpoints import CheckpointAdapter
from .io import sha256_file, stable_hash, write_json, write_jsonl


def _rows(path, delimiter="\t"):
    with Path(path).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source, delimiter=delimiter))


def _expand(value):
    return os.path.expandvars(value)


def load_registry(path):
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("Unsupported model registry schema")
    return value["models"]


def _extended_movies(path):
    if not path:
        return {}
    result = {}
    for row in _rows(path, delimiter=","):
        result[str(row["MovieID"])] = {
            "overview": row.get("overview", ""), "director": row.get("director", ""),
            "cast": [name.strip() for name in row.get("actors", "").split("|")
                     if name.strip()][:5],
            "release_date": row.get("release_date", ""),
            "language": row.get("original_language", ""),
            "country": [name.strip() for name in row.get("production_countries", "").split("|")
                        if name.strip()],
        }
    return result


def _percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return (values[low] if low == high else
            values[low] + (values[high] - values[low]) * (position - low))


def _population_traits(adapter, rating_by_raw, movie_rows):
    uid_field, iid_field = adapter.config["USER_ID_FIELD"], adapter.config["ITEM_ID_FIELD"]
    item_ratings = defaultdict(list)
    for user, items in adapter.train_seen.items():
        raw_uid = str(adapter.dataset.id2token(uid_field, user))
        for item in items:
            raw_iid = str(adapter.dataset.id2token(iid_field, item))
            item_ratings[item].append(float(rating_by_raw[(raw_uid, raw_iid)]["rating:float"]))
    item_means = {item: sum(values) / len(values) for item, values in item_ratings.items()}
    raw = {}
    for user, items in adapter.train_seen.items():
        raw_uid = str(adapter.dataset.id2token(uid_field, user))
        genres, squared = set(), []
        for item in items:
            raw_iid = str(adapter.dataset.id2token(iid_field, item))
            rating = float(rating_by_raw[(raw_uid, raw_iid)]["rating:float"])
            squared.append((rating - item_means[item]) ** 2)
            genres.update(movie_rows[raw_iid]["genre:token_seq"].split())
        raw[user] = {"activity": len(items), "diversity": len(genres),
                     "conformity": sum(squared) / len(squared)}
    thresholds = {
        "activity": [_percentile([x["activity"] for x in raw.values()], .6),
                     _percentile([x["activity"] for x in raw.values()], .9)],
        "diversity": [_percentile([x["diversity"] for x in raw.values()], .33),
                      _percentile([x["diversity"] for x in raw.values()], .66)],
        "conformity": [_percentile([x["conformity"] for x in raw.values()], .25),
                       _percentile([x["conformity"] for x in raw.values()], .8)],
    }
    def level(value, bounds):
        return 1 if value < bounds[0] else 2 if value < bounds[1] else 3
    return ({user: {name: {"value": value, "level": level(value, thresholds[name])}
                    for name, value in values.items()} for user, values in raw.items()}, thresholds)


def prepare_bundle(panel_path, registry_path, recbole_root, dataset_root, output_dir,
                   recbole_debias_root=None, extended_movie_path=None,
                   candidate_size=20, require_joint_positive=True):
    panel = _rows(panel_path, delimiter=",")
    if not panel or len({row["user_id"] for row in panel}) != len(panel):
        raise ValueError("Panel must contain unique users")
    users = [int(row["user_id"]) for row in panel]
    registry = load_registry(registry_path)
    adapters = {}
    for entry in registry:
        name = entry["display_name"]
        checkpoint = _expand(entry["artifact_path"])
        adapter = CheckpointAdapter(checkpoint, recbole_root, dataset_root, name,
                                    recbole_debias_root)
        if sha256_file(checkpoint) != entry["checkpoint_sha256"]:
            raise ValueError(f"{name} checkpoint SHA-256 differs from registry")
        if (adapter.mapping_hash != entry["mapping_hash"]
                or adapter.split_hash != entry["split_hash"]):
            raise ValueError(f"{name} mapping or split differs from registry")
        if any(user not in adapter.test_items for user in users):
            raise ValueError(f"Panel user is absent from {name} test split")
        adapters[name] = adapter
    first = next(iter(adapters.values()))
    if any(adapter.mapping_hash != first.mapping_hash or adapter.split_hash != first.split_hash
           for adapter in adapters.values()):
        raise ValueError("Registered models do not share one mapping and split")

    dataset_dir = Path(dataset_root).resolve() / first.config["dataset"]
    interactions = _rows(dataset_dir / f"{first.config['dataset']}.inter")
    rating_by_raw = {(row["user_id:token"], row["item_id:token"]): row
                     for row in interactions}
    movie_rows = {row["item_id:token"]: row for row in
                  _rows(dataset_dir / f"{first.config['dataset']}.item")}
    user_rows = {row["user_id:token"]: row for row in
                 _rows(dataset_dir / f"{first.config['dataset']}.user")}
    extended = _extended_movies(extended_movie_path)
    population_traits, trait_thresholds = _population_traits(first, rating_by_raw, movie_rows)
    uid_field, iid_field = first.config["USER_ID_FIELD"], first.config["ITEM_ID_FIELD"]

    def raw_user(user):
        return str(first.dataset.id2token(uid_field, user))

    def raw_item(item):
        return str(first.dataset.id2token(iid_field, item))

    histories, labels, catalog_ids = [], [], set()
    for user in users:
        raw_uid = raw_user(user)
        train = []
        for item in sorted(first.train_seen[user]):
            raw_iid = raw_item(item)
            source = rating_by_raw[(raw_uid, raw_iid)]
            train.append({"item_id": item, "raw_item_id": raw_iid,
                          "rating": float(source["rating:float"]),
                          "timestamp": float(source["timestamp:float"])})
            catalog_ids.add(item)
        demo = user_rows[raw_uid]
        histories.append({"user_id": user, "raw_user_id": raw_uid,
                          "demographics": {"age": demo["age:token"],
                                           "gender": demo["gender:token"],
                                           "occupation": demo["occupation:token"]},
                          "train_interactions": train})
        heldout = []
        for item in sorted(first.test_items[user]):
            raw_iid = raw_item(item)
            source = rating_by_raw[(raw_uid, raw_iid)]
            heldout.append({"item_id": item, "raw_item_id": raw_iid,
                            "rating": float(source["rating:float"])})
        labels.append({"user_id": user, "raw_user_id": raw_uid,
                       "heldout_items": heldout})

    candidate_rows = []
    for name, adapter in adapters.items():
        inferred = adapter.candidates(users, candidate_size)
        for user in users:
            ids = inferred[user]["item_ids"]
            positive_count = len(set(ids) & adapter.test_items[user])
            if require_joint_positive and positive_count < 1:
                raise ValueError(f"{name} user {user} violates joint Top-{candidate_size} eligibility")
            catalog_ids.update(ids)
            candidate_rows.append({"model": name, "user_id": user,
                                   "item_ids": ids,
                                   "raw_item_ids": [raw_item(item) for item in ids],
                                   "scores": inferred[user]["scores"],
                                   "heldout_count_in_candidates": positive_count})

    catalog = []
    for item in sorted(catalog_ids):
        raw_iid = raw_item(item)
        row = movie_rows[raw_iid]
        catalog.append({"item_id": item, "raw_item_id": raw_iid,
                        "title": row["movie_title:token_seq"],
                        "release_year": row["release_year:token"],
                        "genres": row["genre:token_seq"].split(),
                        **{key: value for key, value in extended.get(raw_iid, {}).items()
                           if value}})

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "train_interactions.jsonl", histories)
    write_jsonl(output / "candidates.jsonl", candidate_rows)
    write_jsonl(output / "evaluation_labels.jsonl", labels)
    write_jsonl(output / "item_catalog.jsonl", catalog)
    write_json(output / "social_traits.json", {
        "population_scope": "checkpoint_train_only_all_users",
        "population_size": len(population_traits),
        "thresholds": trait_thresholds,
        "users": {str(user): population_traits[user] for user in users},
    })
    panel_copy = output / "users.csv"
    panel_copy.write_bytes(Path(panel_path).read_bytes())
    files = ["users.csv", "train_interactions.jsonl", "candidates.jsonl",
             "evaluation_labels.jsonl", "item_catalog.jsonl", "social_traits.json"]
    manifest = {"schema_version": 1, "num_users": len(users),
                "candidate_size": candidate_size, "models": list(adapters),
                "joint_positive_required": require_joint_positive,
                "mapping_hash": first.mapping_hash, "split_hash": first.split_hash,
                "panel_sha256": sha256_file(panel_path),
                "model_registry_sha256": sha256_file(registry_path),
                "files": {name: sha256_file(output / name) for name in files},
                "bundle_id": stable_hash({"users": users, "split": first.split_hash,
                                           "candidate_size": candidate_size,
                                           "models": list(adapters)})}
    write_json(output / "manifest.json", manifest)
    return manifest

