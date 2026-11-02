"""Configuration loading and CLI override validation."""

from pathlib import Path

import yaml

from .profiles import PROFILE_COMPONENTS, PROFILE_METHODS


def load_config(path, overrides=None):
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    value.update({key: item for key, item in (overrides or {}).items() if item is not None})
    if value["profile_method"] not in PROFILE_METHODS:
        raise ValueError("Invalid profile_method")
    if value["profile_protocol"] not in {"separated", "legacy_combined"}:
        raise ValueError("Invalid profile_protocol")
    if not set(value["profile_components"]) <= set(PROFILE_COMPONENTS):
        raise ValueError("Invalid profile_components")
    if value["concurrency"] < 1 or value["requests_per_minute"] < 1 or value["tokens_per_minute"] < 1:
        raise ValueError("Concurrency and rate limits must be positive")
    if value["num_shards"] < 1 or not 0 <= value["shard_index"] < value["num_shards"]:
        raise ValueError("Require 0 <= shard_index < num_shards")
    if not 0 < value["top_k"] <= value["candidate_size"]:
        raise ValueError("Require 0 < top_k <= candidate_size")
    return value

