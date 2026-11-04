"""Versioned profile generation for ours, Agent4Rec, and SimUSER."""

import json
import hashlib
import math
import random
import fcntl
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jsonschema import ValidationError, validate

from .bundle import select_users
from .io import read_jsonl, sha256_file, stable_hash, write_json, write_jsonl
from .profile_format import labeled_social_traits, natural_demographics, taste_summary


PROFILE_METHODS = ("ours", "agent4rec", "simuser")
PROFILE_COMPONENTS = ("history", "unique_tastes", "social_traits", "demographics")


class _ProfileCacheMiss(Exception):
    pass


class _ProfileClient:
    def __init__(self, client, exchanges, allow_requests=True):
        self.client, self.exchanges = client, exchanges
        self.allow_requests = allow_requests
        self.replayed_call_ids = []

    def respond_json(self, system, user, schema, name):
        expected = {"model": getattr(self.client, "model", None),
                    "temperature": getattr(self.client, "temperature", None)}
        for exchange in reversed(self.exchanges):
            if (exchange.get("response_name") != name or exchange.get("user_prompt") != user
                    or exchange.get("system_prompt_sha256") != hashlib.sha256(system.encode()).hexdigest()
                    or exchange.get("request_params") != expected or exchange.get("error")):
                continue
            try:
                result = json.loads(exchange["raw_response"])
                validate(result, schema)
            except (ValueError, TypeError, KeyError, ValidationError):
                continue
            self.replayed_call_ids.append(exchange.get("call_id"))
            return result
        if not self.allow_requests:
            raise _ProfileCacheMiss("No matching successful profile response")
        for attempt in range(getattr(self.client, "max_retries", 0) + 1):
            if hasattr(self.client, "set_context"):
                self.client.set_context(profile_retry=attempt)
            result = self.client.respond_json(system, user, schema, name)
            call_id = self.client.last_call.get("call_id")
            try:
                validate(result, schema)
            except ValidationError:
                if call_id:
                    self.client.record_validation(call_id, "invalid", "Profile schema validation failed")
                if attempt == getattr(self.client, "max_retries", 0):
                    raise
            else:
                if call_id:
                    self.client.record_validation(call_id, "valid")
                return result


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
    return taste_summary(result)


def _shown(bundle, rows):
    return [{**bundle.movie(row["item_id"]), "rating": row["rating"]} for row in rows]


def generate_persona(method, bundle, user, client, seed, traits):
    rows = bundle.histories[user]["train_interactions"]
    prompt_root = Path(__file__).resolve().parents[1] / "prompts"
    if method == "ours":
        sample = _sample(rows, user, seed, 25, "ours-v1")
        system_path = prompt_root / "profile_ours_system.txt"
        user_path = prompt_root / "profile_ours_user.txt"
        system = system_path.read_text(encoding="utf-8")
        template = user_path.read_text(encoding="utf-8")
        shown = [{"title": row["title"], "release_year": row.get("release_year", ""),
                  "genres": row["genres"], "rating": row["rating"]}
                 for row in _shown(bundle, sample)]
        user_prompt = template.replace("{history_records}",
                                       json.dumps(shown, ensure_ascii=False))
        result = client.respond_json(system, user_prompt, _ours_schema(), "ours_profile")
        result["summary"] = _taste_summary(result)
        return result, {"sampled_item_ids": [row["item_id"] for row in sample],
                        "calls": 1, "method_version": "ours_profile_v1",
                        "system_prompt_sha256": sha256_file(system_path),
                        "user_prompt_sha256": sha256_file(user_path)}
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
                      concurrency=20, persona_file=None, selected_user_ids=None,
                      resume=False, recover_only=False):
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "profile.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _generate_profiles(bundle, client, method, components, seed, history_size,
            num_users, output_dir, concurrency, persona_file, selected_user_ids, resume, recover_only)


def _generate_profiles(bundle, client, method, components, seed, history_size,
                       num_users, output_dir, concurrency, persona_file,
                       selected_user_ids, resume, recover_only):
    if recover_only and not resume:
        raise ValueError("recover_only requires resume=True")
    if method not in PROFILE_METHODS:
        raise ValueError(f"Unknown profile method: {method}")
    enabled = set(PROFILE_COMPONENTS if "all" in components else components)
    unknown = enabled - set(PROFILE_COMPONENTS)
    if unknown:
        raise ValueError(f"Unknown profile components: {sorted(unknown)}")
    users = select_users(bundle.users, num_users, selected_user_ids)
    traits, thresholds = compute_social_traits(bundle)
    imported = {}
    if persona_file:
        for row in read_jsonl(persona_file):
            imported[str(row.get("raw_user_id", row["user_id"]))] = row

    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    checkpoints = root / "checkpoints"
    configuration = {
        "method": method, "components": sorted(enabled), "seed": seed,
        "history_size": history_size, "selected_user_ids_hash": stable_hash(users),
        "source_hash": stable_hash({user: bundle.histories[user] for user in users}),
        "traits_hash": stable_hash(traits),
        "movies_hash": stable_hash({item: bundle.movie(item, detail=True) for item in
            {row["item_id"] for user in users for row in bundle.histories[user]["train_interactions"]}}),
        "persona_hash": sha256_file(persona_file) if persona_file else None,
        "model": getattr(client, "model", None), "temperature": getattr(client, "temperature", None),
        "endpoint_hash": stable_hash(getattr(client, "url", None)),
        "prompt_hashes": {path.name: sha256_file(path) for path in
            (Path(__file__).resolve().parents[1] / "prompts").glob("profile_*.txt")},
    }
    configuration_hash = stable_hash(configuration)
    manifest_path = root / "run_manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not resume:
            raise ValueError("Profile output already exists; use resume=True")
        if previous.get("configuration_hash") != configuration_hash:
            raise ValueError("Profile resume configuration does not match")
    elif not resume and (checkpoints.exists() or (root / "transcripts.jsonl").exists()):
        raise ValueError("Partial profile output exists; use resume=True")
    pairs = {}
    cached = defaultdict(list)
    previous_cost = 0.0
    transcript_path = root / "transcripts.jsonl"
    if resume and transcript_path.exists():
        with transcript_path.open("r+b") as source:
            while True:
                position = source.tell()
                line = source.readline()
                if not line:
                    break
                try:
                    exchange = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    if not line.endswith(b"\n"):
                        (root / "transcripts.incomplete").write_bytes(line)
                        source.truncate(position)
                        break
                    raise ValueError("Corrupt profile transcript") from None
                if not line.endswith(b"\n"):
                    source.write(b"\n")
                if exchange.get("kind") == "exchange":
                    cached[exchange.get("user_id")].append(exchange)
                    budget = getattr(client, "budget", None)
                    if budget is not None:
                        usage = exchange.get("usage", {})
                        previous_cost += (usage.get("prompt_tokens", 0) * budget.input_rate
                                          + usage.get("completion_tokens", 0) * budget.output_rate) / 1_000_000
        budget = getattr(client, "budget", None)
        if budget is not None:
            budget.cost = max(budget.cost, previous_cost)
    for path in sorted(checkpoints.glob("*.json")):
        saved = json.loads(path.read_text(encoding="utf-8"))
        user = saved["profile"]["user_id"]
        if (saved.get("configuration_hash") != configuration_hash or user not in users
            or saved["manifest"]["user_id"] != user or user in pairs
            or saved.get("checkpoint_hash") != stable_hash([saved["profile"], saved["manifest"]])):
            raise ValueError(f"Invalid profile checkpoint: {path.name}")
        pairs[user] = saved["profile"], saved["manifest"]
    run_manifest = {"schema_version": 1, "method": method,
        "components": sorted(enabled), "num_users": len(users), "seed": seed,
        "selected_user_ids_hash": stable_hash(users), "concurrency": concurrency,
        "persona_file": str(persona_file or ""),
        "trait_population_scope": bundle.trait_population_scope or "materialized_panel",
        "trait_thresholds": thresholds, "configuration": configuration,
        "configuration_hash": configuration_hash, "status": "running",
        "completed_users": len(pairs)}
    write_json(manifest_path, run_manifest)
    if hasattr(client, "transcript_dir"):
        client.transcript_dir = root

    def one(user):
        if hasattr(client, "set_context"):
            client.set_context(reset=True, user_id=user, stage="profile")
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
            profile["demographics"] = natural_demographics(source["demographics"])
        if "social_traits" in enabled:
            profile["social_traits"] = labeled_social_traits(traits[user])
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
                profile_client = _ProfileClient(client, cached[user], allow_requests=not recover_only)
                tastes, persona_manifest = generate_persona(method, bundle, user,
                    profile_client, seed, traits)
                if profile_client.replayed_call_ids:
                    persona_manifest["recovered_call_ids"] = profile_client.replayed_call_ids
            profile["unique_tastes"] = tastes
            manifest.update(persona_manifest)
        write_json(checkpoints / f"{user}.json", {"configuration_hash": configuration_hash,
                   "profile": profile, "manifest": manifest,
                   "checkpoint_hash": stable_hash([profile, manifest])})
        return profile, manifest

    failures = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(one, user): user for user in users if user not in pairs}
        for future in as_completed(futures):
            user = futures[future]
            try:
                pairs[user] = future.result()
            except _ProfileCacheMiss:
                continue
            except Exception as exception:
                failures.append({"user_id": user, "error_type": type(exception).__name__,
                                 "error": (client._safe_error(exception) if hasattr(client, "_safe_error")
                                           else str(exception))[:500]})
                write_jsonl(root / "profile_failures.jsonl", failures)
    profiles = [pairs[user][0] for user in users if user in pairs]
    manifests = [pairs[user][1] for user in users if user in pairs]
    write_jsonl(root / "profiles.jsonl", profiles)
    write_jsonl(root / "profile_manifests.jsonl", manifests)
    run_manifest.update(status="partial" if len(pairs) < len(users) else "complete", completed_users=len(pairs))
    write_json(manifest_path, run_manifest)
    if failures:
        raise RuntimeError(f"Profile generation incomplete: {len(pairs)}/{len(users)} saved; "
                           "resume to retry failed users")
    return {"output_dir": str(root), "num_users": len(users), "completed_users": len(pairs),
            "method": method, "recover_only": recover_only}
