"""Versioned profile generation for ours, Agent4Rec, and SimUSER."""

import json
import hashlib
import math
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .io import read_jsonl, stable_hash, write_json, write_jsonl


PROFILE_METHODS = ("ours", "agent4rec", "simuser")
PROFILE_COMPONENTS = ("history", "unique_tastes", "social_traits", "demographics")


def _sample(rows, user_id, seed, limit, namespace):
    ordered = sorted(rows, key=lambda row: (row["item_id"], row["timestamp"]))
    rng = random.Random(stable_hash({"namespace": namespace, "seed": seed,
                                    "user_id": int(user_id)}))
    return sorted(rng.sample(ordered, min(limit, len(ordered))),
                  key=lambda row: row["item_id"])


def _runtime_history_sample(rows, user_id, seed, limit):
    """Match the established ProfileBuilder uniform-history protocol exactly."""
    ordered = sorted(rows, key=lambda row: (row["item_id"], row["timestamp"]))
    user_seed = int.from_bytes(
        hashlib.sha256(f"{seed}:{int(user_id)}".encode("utf-8")).digest()[:8], "big")
    indices = random.Random(user_seed).sample(range(len(ordered)), min(limit, len(ordered)))
    return [ordered[index] for index in indices]


def _percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low, high = math.floor(position), math.ceil(position)
    return values[low] if low == high else values[low] + (values[high] - values[low]) * (position - low)


def compute_social_traits(bundle):
    if bundle.social_traits is not None:
        return bundle.social_traits, bundle.trait_thresholds
    item_ratings = defaultdict(list)
    for record in bundle.histories.values():
        for row in record["train_interactions"]:
            item_ratings[row["item_id"]].append(row["rating"])
    means = {item: sum(values) / len(values) for item, values in item_ratings.items()}
    raw = {}
    for user, record in bundle.histories.items():
        rows = record["train_interactions"]
        genres = {genre for row in rows for genre in bundle.movie(row["item_id"])["genres"]}
        conformity = sum((row["rating"] - means[row["item_id"]]) ** 2 for row in rows) / len(rows)
        raw[user] = {"activity": len(rows), "diversity": len(genres),
                     "conformity": conformity}
    thresholds = {"activity": [_percentile([x["activity"] for x in raw.values()], .6),
                                _percentile([x["activity"] for x in raw.values()], .9)],
                  "diversity": [_percentile([x["diversity"] for x in raw.values()], .33),
                                 _percentile([x["diversity"] for x in raw.values()], .66)],
                  "conformity": [_percentile([x["conformity"] for x in raw.values()], .25),
                                  _percentile([x["conformity"] for x in raw.values()], .8)]}
    def level(value, bounds):
        return 1 if value < bounds[0] else 2 if value < bounds[1] else 3
    traits = {user: {name: {"value": value, "level": level(value, thresholds[name])}
                     for name, value in values.items()} for user, values in raw.items()}
    return traits, thresholds


def _simple_schema():
    text = {"type": "string"}
    return {"type": "object", "properties": {
        "unique_tastes": {"type": "array", "items": text, "maxItems": 5},
        "liked_patterns": {"type": "array", "items": text, "maxItems": 3},
        "disliked_patterns": {"type": "array", "items": text, "maxItems": 3},
        "summary": text},
        "required": ["unique_tastes", "liked_patterns", "disliked_patterns", "summary"],
        "additionalProperties": False}


def _ours_schema():
    return {"type": "object", "properties": {
        "unique_tastes": {"type": "array", "maxItems": 5, "items": {
            "type": "object", "properties": {"taste": {"type": "string"},
            "reason": {"type": "string"}}, "required": ["taste", "reason"],
            "additionalProperties": False}},
        "liked_patterns": {"type": "array", "maxItems": 3,
                           "items": {"type": "string"}},
        "disliked_patterns": {"type": "array", "maxItems": 3,
                              "items": {"type": "string"}}},
        "required": ["unique_tastes", "liked_patterns", "disliked_patterns"],
        "additionalProperties": False}


def _taste_summary(result):
    tastes = "; ".join(f"{row['taste']} ({row['reason']})"
                       for row in result["unique_tastes"])
    liked = ", ".join(result["liked_patterns"])
    disliked = ", ".join(result["disliked_patterns"])
    return f"Unique tastes: {tastes}. Liked patterns: {liked}. Disliked patterns: {disliked}."


def _shown(bundle, rows):
    return [{**bundle.movie(row["item_id"]), "rating": row["rating"]} for row in rows]


def generate_persona(method, bundle, user, client, seed, traits):
    rows = bundle.histories[user]["train_interactions"]
    prompt_root = Path(__file__).resolve().parents[1] / "prompts"
    if method == "ours":
        sample = _sample(rows, user, seed, 25, "ours-v1")
        system = (prompt_root / "persona_v3_system.txt").read_text(encoding="utf-8")
        template = (prompt_root / "persona_v3_user.txt").read_text(encoding="utf-8")
        shown = [{"title": row["title"], "release_year": row.get("release_year", ""),
                  "genres": row["genres"], "rating": row["rating"]}
                 for row in _shown(bundle, sample)]
        user_prompt = template.replace("{history_records}",
                                       json.dumps(shown, ensure_ascii=False))
        result = client.respond_json(system, user_prompt, _ours_schema(), "ours_profile")
        result["summary"] = _taste_summary(result)
        return result, {"sampled_item_ids": [row["item_id"] for row in sample],
                        "calls": 1, "method_version": "ours_agent4rec_train25_v4"}
    if method == "agent4rec":
        sample = sorted(rows, key=lambda row: (-row["rating"], row["item_id"]))[:25]
        system = (prompt_root / "profile_agent4rec_system.txt").read_text(encoding="utf-8")
        user_payload = {"history": _shown(bundle, sample), "social_traits": traits[user]}
        result = client.respond_json(system, json.dumps(user_payload, ensure_ascii=False),
                                     _simple_schema(), "agent4rec_profile")
        return result, {"sampled_item_ids": [row["item_id"] for row in sample],
                        "calls": 1, "method_version": "agent4rec_profile_v1"}

    sample = _sample(rows, user, seed, 50, "simuser-v1")
    system = (prompt_root / "profile_simuser_system.txt").read_text(encoding="utf-8")
    summary = client.respond_json(system, json.dumps({"history": _shown(bundle, sample)},
                                                    ensure_ascii=False),
                                  _simple_schema(), "simuser_taste_summary")
    personality = {name: {"type": "integer", "minimum": 1, "maximum": 3} for name in
                   ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")}
    candidate_schema = {"type": "object", "properties": {"candidate_personas": {
        "type": "array", "minItems": 5, "maxItems": 5, "items": {"type": "object",
        "properties": {"age": {"type": "string"}, "occupation": {"type": "string"},
                       "personality": {"type": "object", "properties": personality,
                                       "required": list(personality), "additionalProperties": False},
                       "summary": {"type": "string"}},
        "required": ["age", "occupation", "personality", "summary"],
        "additionalProperties": False}}}, "required": ["candidate_personas"],
        "additionalProperties": False}
    candidates = client.respond_json(system, json.dumps({"taste_summary": summary,
                                                         "history": _shown(bundle, sample)},
                                                        ensure_ascii=False),
                                     candidate_schema, "simuser_candidates")["candidate_personas"]
    other_users = [value for value in sorted(bundle.users) if value != user]
    negative_user = other_users[int(stable_hash({"seed": seed, "user": user})[:8], 16)
                                % len(other_users)]
    negative = _sample(bundle.histories[negative_user]["train_interactions"], negative_user,
                       seed, min(10, len(sample)), "simuser-negative-v1")
    score_schema = {"type": "object", "properties": {
        "best_index": {"type": "integer", "minimum": 0, "maximum": 4},
        "scores": {"type": "array", "minItems": 5, "maxItems": 5,
                   "items": {"type": "number"}}},
        "required": ["best_index", "scores"], "additionalProperties": False}
    scored = client.respond_json(system, json.dumps({"candidate_personas": candidates,
        "target_history": _shown(bundle, sample[:10]),
        "other_user_history": _shown(bundle, negative)}, ensure_ascii=False),
        score_schema, "simuser_consistency")
    selected = candidates[scored["best_index"]]
    result = {**summary, "summary": selected["summary"], "matched_persona": selected,
              "consistency_scores": scored["scores"]}
    return result, {"sampled_item_ids": [row["item_id"] for row in sample],
                    "negative_user_id": negative_user, "calls": 3,
                    "method_version": "simuser_phase1_v1"}


def generate_profiles(bundle, client, method="ours", components=("all",), seed=42,
                      history_size=10, num_users=None, output_dir="profiles",
                      concurrency=20, persona_file=None):
    if method not in PROFILE_METHODS:
        raise ValueError(f"Unknown profile method: {method}")
    enabled = set(PROFILE_COMPONENTS if "all" in components else components)
    unknown = enabled - set(PROFILE_COMPONENTS)
    if unknown:
        raise ValueError(f"Unknown profile components: {sorted(unknown)}")
    users = bundle.users[:num_users] if num_users is not None else bundle.users
    traits, thresholds = compute_social_traits(bundle)
    imported = {}
    if persona_file:
        for row in read_jsonl(persona_file):
            imported[str(row.get("raw_user_id", row["user_id"]))] = row

    def one(user):
        source = bundle.histories[user]
        rows = source["train_interactions"]
        profile = {"user_id": user, "raw_user_id": source["raw_user_id"]}
        manifest = {"user_id": user, "method": method, "seed": seed,
                    "enabled_components": sorted(enabled),
                    "source_hash": stable_hash(rows)}
        if "history" in enabled:
            sample = _runtime_history_sample(rows, user, seed, history_size)
            profile["interaction_history"] = []
            for row in sample:
                movie = bundle.movie(row["item_id"], detail=True)
                movie.pop("item_id", None)
                profile["interaction_history"].append(movie)
            manifest["history_item_ids"] = [row["item_id"] for row in sample]
        if "demographics" in enabled:
            profile["demographics"] = source["demographics"]
        if "social_traits" in enabled:
            profile["social_traits"] = traits[user]
        if "unique_tastes" in enabled:
            legacy = imported.get(str(source["raw_user_id"]))
            if legacy is not None:
                tastes = {key: legacy[key] for key in
                          ("unique_tastes", "liked_patterns", "disliked_patterns")
                          if key in legacy}
                tastes["summary"] = legacy.get("taste_summary", legacy["summary"])
                profile["legacy_persona_summary"] = legacy["summary"]
                persona_manifest = {"method_version": "imported_persona",
                                    "source_persona_hash": stable_hash(legacy), "calls": 0}
                if "social_traits" in legacy:
                    profile["social_traits"] = legacy["social_traits"]
            elif persona_file:
                raise ValueError(f"Imported persona missing raw user {source['raw_user_id']}")
            else:
                tastes, persona_manifest = generate_persona(method, bundle, user, client, seed, traits)
            profile["unique_tastes"] = tastes
            manifest.update(persona_manifest)
        return profile, manifest

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pairs = list(pool.map(one, users))
    profiles = [pair[0] for pair in pairs]
    manifests = [pair[1] for pair in pairs]
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    write_jsonl(root / "profiles.jsonl", profiles)
    write_jsonl(root / "profile_manifests.jsonl", manifests)
    write_json(root / "run_manifest.json", {"schema_version": 1, "method": method,
               "components": sorted(enabled), "num_users": len(users), "seed": seed,
               "concurrency": concurrency, "persona_file": str(persona_file or ""),
               "trait_population_scope": bundle.trait_population_scope or "materialized_panel",
               "trait_thresholds": thresholds})
    return {"output_dir": str(root), "num_users": len(users), "method": method}
