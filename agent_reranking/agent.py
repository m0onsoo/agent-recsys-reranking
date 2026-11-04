"""Current two-stage click and conversion behavior protocol."""

import json
import re
import hashlib
import random
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from .io import sha256_file


MOTIVE_CLICK_SCHEMA = {
    "type": "object", "properties": {
        "clicked_item_ids": {"type": "array", "items": {"type": "integer"},
                             "uniqueItems": True},
        "click_motives": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["clicked_item_ids", "click_motives"], "additionalProperties": False,
}
MOTIVE_CONVERSION_SCHEMA = {
    "type": "object", "properties": {
        "converted_item_ids": {"type": "array", "items": {"type": "integer"},
                               "uniqueItems": True},
        "motive_assessments": {"type": "object", "additionalProperties": {
            "type": "object", "properties": {
                "outcome": {"enum": ["confirmed", "contradicted", "insufficient"]},
                "decision_note": {"type": "string"},
            },
            "required": ["outcome", "decision_note"], "additionalProperties": False,
        }},
    },
    "required": ["converted_item_ids", "motive_assessments"],
    "additionalProperties": False,
}

ALIGN_CLICK_SCHEMA = {
    "type": "object", "properties": {
        "candidate_assessments": {"type": "object", "additionalProperties": {
            "type": "object", "properties": {
                "alignment": {"enum": ["strong", "adjacent", "none"]},
                "evidence": {"type": "string"},
            },
            "required": ["alignment", "evidence"], "additionalProperties": False,
        }},
        "clicked_item_ids": {"type": "array", "items": {"type": "integer"},
                             "uniqueItems": True},
    },
    "required": ["candidate_assessments", "clicked_item_ids"],
    "additionalProperties": False,
}

RATING_CONVERSION_SCHEMA = {
    "type": "object", "properties": {
        "watch_decision": {"enum": ["watch", "not_ready"]},
        "converted_item_ids": {"type": "array", "items": {"type": "integer"},
                               "uniqueItems": True, "maxItems": 1},
        "motive_assessments": {"type": "object", "additionalProperties": {
            "type": "object", "properties": {
                "outcome": {"enum": ["confirmed", "contradicted", "insufficient"]},
                "predicted_rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "reason": {"type": "string"},
            },
            "required": ["outcome", "predicted_rating", "reason"],
            "additionalProperties": False,
        }},
        "decision_reason": {"type": "string"},
    },
    "required": ["watch_decision", "converted_item_ids", "motive_assessments",
                 "decision_reason"],
    "additionalProperties": False,
}


_ARTICLES = ("The", "A", "An", "Les", "La", "Le", "L'", "Il", "Das", "Der", "Die", "El")

DEBIASED_CLICK_SCHEMA = deepcopy(ALIGN_CLICK_SCHEMA)
_interest_schema = DEBIASED_CLICK_SCHEMA["properties"]["candidate_assessments"]["additionalProperties"]
_interest_schema["properties"].pop("alignment")
_interest_schema["properties"]["interest"] = {"type": "integer", "minimum": 1, "maximum": 5}
_interest_schema["required"] = ["interest", "evidence"]
DEBIASED_CONVERSION_SCHEMA = deepcopy(RATING_CONVERSION_SCHEMA)
_watch_schema = DEBIASED_CONVERSION_SCHEMA["properties"]["motive_assessments"]["additionalProperties"]
_watch_schema["properties"].pop("predicted_rating")
_watch_schema["properties"]["watch_likelihood"] = {"type": "integer", "minimum": 1, "maximum": 5}
_watch_schema["required"] = ["outcome", "watch_likelihood", "reason"]
_watch_schema["properties"]["outcome"]["type"] = "string"
DEBIASED_CONVERSION_SCHEMA["properties"]["watch_decision"]["type"] = "string"


def presentation_order(item_ids, model, user_id, seed=42):
    if not model:
        raise ValueError("Debiased presentation requires a backbone model")
    material = json.dumps([seed, model, int(user_id)], separators=(",", ":"))
    order = list(item_ids)
    random.Random(int.from_bytes(hashlib.sha256(material.encode()).digest(), "big")).shuffle(order)
    return order


def _title_variants(title):
    """Surface forms a model may use when quoting a MovieLens title."""
    variants = {title}
    base = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
    variants.add(base)
    for inner in re.findall(r"\(([^)]*)\)", title):
        variants.add(re.sub(r"^(?:a\.k\.a\.|aka)\s+", "", inner.strip(), flags=re.I))
    for value in list(variants):
        match = re.match(r"^(.*), (" + "|".join(re.escape(a) for a in _ARTICLES) + r")$", value)
        if match:
            joiner = "" if match.group(2).endswith("'") else " "
            variants.add(f"{match.group(2)}{joiner}{match.group(1)}")
    return sorted((value for value in variants if value), key=len, reverse=True)


def _mask_titles(text, titles):
    """Replace quoted movie titles with a placeholder so their punctuation (?, !, ...)
    and length do not count as sentence boundaries or extra words."""
    for title in titles:
        for variant in _title_variants(title):
            if re.search(r"[.!?]|\s", variant):
                text = re.sub(re.escape(variant), "TITLE", text, flags=re.IGNORECASE)
    return text


def _instruction(profile):
    if "interaction_history" in profile:
        return "Treat interaction_history as an unordered sample; do not infer recency from array position."
    return "No interaction history is supplied; do not invent one."


FULL_SLATE_CONTEXT = (
    "candidate_slate is the complete displayed exposure slate with basic metadata; "
    "it does not provide recommender scores or ranks. "
    "clicked_item_ids identifies the movies opened for inspection, and clicked_items contains "
    "detailed metadata for those movies. Select conversions only from clicked_item_ids."
)

PROMPT_PROTOCOLS = {
    "behavior-v3-debiased": (
        "click_behavior_v3_debiased.txt",
        "conversion_behavior_v3_debiased.txt",
    ),
    "behavior-motive-assessment-v1": (
        "legacy/click_behavior_motive_assessment_v1.txt",
        "legacy/conversion_behavior_motive_assessment_v1.txt",
    ),
    "behavior-motive-assessment-v2": (
        "click_behavior_motive_assessment.txt",
        "conversion_behavior_motive_assessment.txt",
    ),
    "behavior-social-traits": (
        "click_behavior_social_traits.txt",
        "conversion_behavior_social_traits.txt",
    ),
    "behavior-align-rating-social-traits": (
        "click_behavior_align_rating_social_traits.txt",
        "conversion_behavior_align_rating_social_traits.txt",
    ),
}


class TwoStageAgent:
    def __init__(self, client, retries=2,
                 prompt_version="behavior-motive-assessment-v2"):
        self.client, self.retries = client, retries
        root = Path(__file__).resolve().parents[1] / "prompts"
        if prompt_version not in PROMPT_PROTOCOLS:
            raise ValueError(f"Unknown behavior prompt version: {prompt_version}")
        click_name, conversion_name = PROMPT_PROTOCOLS[prompt_version]
        # The legacy renderer strips the template before replacing placeholders.
        # Preserve that behavior because even whitespace changes alter the API request.
        click_path = root / click_name
        conversion_path = root / conversion_name
        self.click_prompt = click_path.read_text(encoding="utf-8").strip()
        self.conversion_prompt = conversion_path.read_text(encoding="utf-8").strip()
        self.prompt_hashes = {
            "click": sha256_file(click_path),
            "conversion": sha256_file(conversion_path),
        }
        self.prompt_version = prompt_version
        self.exposes_average_rating = prompt_version not in (
            "behavior-motive-assessment-v1", "behavior-v3-debiased")
        self.uses_align_rating_protocol = (
            prompt_version == "behavior-align-rating-social-traits")

    @staticmethod
    def _canonicalize_click(value):
        raw_ids = value.get("clicked_item_ids", [])
        ids, embedded = [], {}
        for row in raw_ids:
            if isinstance(row, dict):
                item = row.get("item_id", row.get("id"))
                if item is None:
                    raise ValueError("Clicked item object lacks item_id")
                ids.append(int(item))
                motive = row.get("click_motive", row.get("motive"))
                if motive is not None:
                    embedded[str(int(item))] = str(motive)
            else:
                ids.append(int(row))
        raw_motives = value.get("click_motives", embedded)
        if isinstance(raw_motives, list):
            motives = {}
            for row in raw_motives:
                item = row.get("item_id", row.get("id"))
                motive = row.get("click_motive", row.get("motive"))
                if item is None or motive is None:
                    raise ValueError("Click motive object lacks item_id or motive")
                motives[str(int(item))] = str(motive)
        elif isinstance(raw_motives, dict):
            motives = {str(key): str(item) for key, item in raw_motives.items()}
        else:
            raise ValueError("click_motives must be an object or list")
        if not motives and embedded:
            motives = embedded
        return {"clicked_item_ids": ids, "click_motives": motives}

    @staticmethod
    def _canonicalize_conversion(value):
        raw_ids = value.get("converted_item_ids", [])
        ids = [int(row.get("item_id", row.get("id"))) if isinstance(row, dict)
               else int(row) for row in raw_ids]
        raw = value.get("motive_assessments", {})
        if isinstance(raw, list):
            assessments = {}
            for row in raw:
                item = row.get("item_id", row.get("id"))
                if item is None:
                    raise ValueError("Motive assessment object lacks item_id")
                assessments[str(int(item))] = {
                    "outcome": row.get("outcome"),
                    "decision_note": row.get("decision_note", row.get("note", "")),
                }
        elif isinstance(raw, dict):
            assessments = {str(key): row for key, row in raw.items()}
        else:
            raise ValueError("motive_assessments must be an object or list")
        return {"converted_item_ids": ids, "motive_assessments": assessments}

    @staticmethod
    def _validate_click(value, allowed, titles=()):
        Draft202012Validator(MOTIVE_CLICK_SCHEMA).validate(value)
        ids = value["clicked_item_ids"]
        motives = value["click_motives"]
        if not set(ids).issubset(allowed):
            raise ValueError("click selected an item outside the permitted set")
        if set(motives) != {str(item) for item in ids}:
            TwoStageAgent._raise_key_mismatch(
                "click_motives", motives, {str(item) for item in ids}, "clicked_item_ids")
        for item, motive in motives.items():
            TwoStageAgent._validate_short_sentence(motive, f"click_motives[{item}]", titles)

    @staticmethod
    def _validate_conversion(value, clicked, titles=()):
        Draft202012Validator(MOTIVE_CONVERSION_SCHEMA).validate(value)
        ids = value["converted_item_ids"]
        assessments = value["motive_assessments"]
        if not set(ids).issubset(set(clicked)):
            raise ValueError("conversion selected an item outside the permitted set")
        if set(assessments) != {str(item) for item in clicked}:
            TwoStageAgent._raise_key_mismatch(
                "motive_assessments", assessments, {str(item) for item in clicked},
                "all clicked_item_ids")
        for item, assessment in assessments.items():
            TwoStageAgent._validate_short_sentence(
                assessment.get("decision_note"), f"motive_assessments[{item}].decision_note",
                titles)

    @staticmethod
    def _validate_align_click(value, allowed, titles=()):
        Draft202012Validator(ALIGN_CLICK_SCHEMA).validate(value)
        ids = value["clicked_item_ids"]
        assessments = value["candidate_assessments"]
        expected = {str(item) for item in allowed}
        if set(assessments) != expected:
            TwoStageAgent._raise_key_mismatch(
                "candidate_assessments", assessments, expected, "all candidate item IDs")
        if not set(ids).issubset(allowed):
            raise ValueError("click selected an item outside the permitted set")
        for item, assessment in assessments.items():
            TwoStageAgent._validate_short_sentence(
                assessment["evidence"], f"candidate_assessments[{item}].evidence", titles)
        for item in ids:
            if assessments[str(item)]["alignment"] == "none":
                raise ValueError("an item with alignment=none cannot be clicked")

    @staticmethod
    def _validate_rating_conversion(value, clicked, titles=()):
        Draft202012Validator(RATING_CONVERSION_SCHEMA).validate(value)
        ids = value["converted_item_ids"]
        assessments = value["motive_assessments"]
        if not set(ids).issubset(set(clicked)):
            raise ValueError("conversion selected an item outside the permitted set")
        if set(assessments) != {str(item) for item in clicked}:
            TwoStageAgent._raise_key_mismatch(
                "motive_assessments", assessments, {str(item) for item in clicked},
                "all clicked_item_ids")
        decision = value["watch_decision"]
        if decision == "watch" and len(ids) != 1:
            raise ValueError("watch_decision=watch requires exactly one converted item")
        if decision == "not_ready" and ids:
            raise ValueError("watch_decision=not_ready requires an empty converted_item_ids")
        for item, assessment in assessments.items():
            TwoStageAgent._validate_short_sentence(
                assessment["reason"], f"motive_assessments[{item}].reason", titles)
        TwoStageAgent._validate_short_sentence(value["decision_reason"], "decision_reason",
                                               titles)

    @staticmethod
    def _raise_key_mismatch(field, values, expected, target):
        actual = set(values)
        sort_key = lambda value: (0, int(value)) if value.isdigit() else (1, value)
        missing = sorted(expected - actual, key=sort_key)
        extra = sorted(actual - expected, key=sort_key)
        raise ValueError(
            f"{field} keys must exactly match {target}; "
            f"missing keys={missing}; extra keys={extra}. "
            "Add every missing key and remove every extra key."
        )

    @staticmethod
    def _validate_short_sentence(value, field, titles=()):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
        masked = _mask_titles(value.strip(), titles)
        if len(masked.split()) > 20:
            raise ValueError(f"{field} must contain at most 20 words")
        boundary_text = re.sub(r"(?:\b[A-Za-z]\.){2,}",
                               lambda match: match.group(0).replace(".", ""), masked)
        boundary_text = re.sub(
            r"\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs)\.",
            lambda match: match.group(0).replace(".", ""),
            boundary_text,
            flags=re.IGNORECASE,
        )
        if "\n" in value or len(re.findall(r"[.!?](?=\s|$)", boundary_text)) > 1:
            raise ValueError(f"{field} must contain at most one sentence")

    @staticmethod
    def _retry_system(system, feedback):
        rendered = (system + "\n\nThe previous response failed validation: "
                    + str(feedback)
                    + " Return a corrected complete JSON object. Do not repeat the invalid format or wording.")
        if "at most one sentence" in str(feedback):
            rendered += (" Rewrite every motive and note as a single clause with no internal period, "
                         "question mark, or exclamation mark; use at most one such mark at the very end.")
        if "must be a nonempty string" in str(feedback):
            rendered += (" Every evidence, reason, motive, and note must be a nonempty sentence. "
                         "This includes candidates labeled none: for those, briefly state why the "
                         "supplied evidence does not show a personal fit.")
        if "at most 20 words" in str(feedback):
            rendered += (" Rewrite every motive and decision_note using no more than 15 "
                         "space-separated words. Count the words before returning the complete JSON.")
        return rendered

    def _record_validation(self, status, error=None):
        record = getattr(self.client, "record_validation", None)
        call_id = self.client.last_call.get("call_id")
        if record and call_id:
            record(call_id, status, error)

    def _call(self, stage, system, payload, validator, response_name=None, schema=None):
        feedback = None
        attempts = []
        for retry in range(self.retries + 1):
            sent = dict(payload)
            if feedback:
                sent["retry_feedback"] = feedback
            set_context = getattr(self.client, "set_context", None)
            if set_context:
                set_context(stage=stage, retry=retry)
            try:
                rendered_system = self._retry_system(system, feedback) if feedback else system
                value = self.client.respond_json(
                    rendered_system, json.dumps(sent, ensure_ascii=False), schema,
                    response_name or f"{stage}_selection")
                validator(value)
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "valid"})
                self._record_validation("valid")
                return value, attempts
            except (KeyError, TypeError, ValueError, ValidationError) as exc:
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "invalid", "error": str(exc)[:200]})
                self._record_validation("invalid", str(exc)[:500])
                if retry == self.retries:
                    raise
                feedback = str(exc)
        raise AssertionError("unreachable")

    @staticmethod
    def _validate_debiased_click(value, allowed, titles=()):
        Draft202012Validator(DEBIASED_CLICK_SCHEMA).validate(value)
        assessments = value["candidate_assessments"]
        if set(assessments) != {str(item) for item in allowed}:
            TwoStageAgent._raise_key_mismatch(
                "candidate_assessments", assessments, {str(item) for item in allowed},
                "all candidate item IDs")
        if not set(value["clicked_item_ids"]).issubset(allowed):
            raise ValueError("click selected an item outside the permitted set")
        for item, assessment in assessments.items():
            TwoStageAgent._validate_debiased_sentence(
                assessment["evidence"], f"candidate_assessments[{item}].evidence", titles)
        if any(assessments[str(item)]["interest"] < 3 for item in value["clicked_item_ids"]):
            raise ValueError("Only candidates with interest >= 3 may be clicked")

    @staticmethod
    def _validate_debiased_sentence(value, field, titles=()):
        TwoStageAgent._validate_short_sentence(value, field, titles)
        if len(value.split()) > 20:
            raise ValueError(f"{field} must contain at most 20 words")

    @staticmethod
    def _validate_debiased_conversion(value, clicked, titles=()):
        Draft202012Validator(DEBIASED_CONVERSION_SCHEMA).validate(value)
        translated = deepcopy(value)
        for assessment in translated["motive_assessments"].values():
            assessment["predicted_rating"] = assessment.pop("watch_likelihood")
        TwoStageAgent._validate_rating_conversion(translated, clicked, titles)
        for item, assessment in value["motive_assessments"].items():
            TwoStageAgent._validate_debiased_sentence(
                assessment["reason"], f"motive_assessments[{item}].reason", titles)
        TwoStageAgent._validate_debiased_sentence(value["decision_reason"], "decision_reason", titles)

    def _simulate_debiased(self, profile, candidate, catalog, model, seed):
        if '"average_rating"' in json.dumps(profile):
            raise ValueError("Debiased profile must not contain average_rating")
        if "conformity" in json.dumps(profile.get("social_traits", {})).lower():
            raise ValueError("Debiased profile must not contain Conformity")
        order = presentation_order(candidate["item_ids"], model, profile["user_id"], seed)
        titles = [catalog[item]["title"] for item in order]
        basic_fields = ("item_id", "title", "release_year", "genres")
        basic = [{key: catalog[item][key] for key in basic_fields if key in catalog[item]}
                 for item in order]
        click_system = self.click_prompt.replace("{history_instruction}", _instruction(profile))
        click, attempts = self._call("click", click_system,
            {"stage": "click", "profile": profile, "items": basic, "retry_feedback": None},
            lambda value: self._validate_debiased_click(value, set(order), titles),
            "debiased_click_selection", DEBIASED_CLICK_SCHEMA)
        clicked_set = set(click["clicked_item_ids"])
        clicked = [item for item in order if item in clicked_set]
        click["clicked_item_ids"] = clicked
        click["click_count"] = len(clicked)
        click["click_motives"] = {str(item): click["candidate_assessments"][str(item)]["evidence"]
                                  for item in clicked}
        click["shown_candidate_item_ids"] = order
        click["shown_clicked_item_ids"] = clicked
        if not clicked:
            return {**click, "watch_decision": "not_ready", "converted_item_ids": [],
                    "motive_assessments": {},
                    "decision_reason": "No candidate warranted opening its details"}, attempts
        defaults = {"overview": "unknown", "director": "unknown", "cast": [],
                    "release_date": "unknown", "language": "unknown", "country": []}
        details = [{**{key: catalog[item][key] for key in basic_fields if key in catalog[item]},
                    **{key: catalog[item].get(key, default) for key, default in defaults.items()},
                    "click_hypothesis": click["click_motives"][str(item)]} for item in clicked]
        context = (FULL_SLATE_CONTEXT + " Both displayed lists are in random order. "
                   "Use confirmed when details support the click hypothesis; contradicted only "
                   "when a revealed fact directly conflicts with it; insufficient when details "
                   "neither confirm nor directly refute it. Missing extra support or a weaker "
                   "impression is not a contradiction.")
        conversion_system = self.conversion_prompt.replace(
            "{history_instruction}", _instruction(profile)).replace(
            "{conversion_context_instruction}", context)
        conversion, more = self._call("conversion", conversion_system,
            {"stage": "conversion", "profile": profile, "candidate_slate": basic,
             "clicked_item_ids": clicked, "clicked_items": details, "retry_feedback": None},
            lambda value: self._validate_debiased_conversion(value, clicked, titles),
            "debiased_conversion_selection", DEBIASED_CONVERSION_SCHEMA)
        return {**click, **conversion}, attempts + more

    def simulate(self, profile, candidate, catalog, model=None, seed=42):
        if self.prompt_version == "behavior-v3-debiased":
            return self._simulate_debiased(
                profile, candidate, catalog, model or candidate.get("model"), seed)
        ids = candidate["item_ids"]
        titles = [catalog[item]["title"] for item in ids if "title" in catalog[item]]
        basic_fields = ("item_id", "title", "release_year", "genres")
        if self.exposes_average_rating:
            basic_fields += ("average_rating",)
        basic = [{key: catalog[item][key] for key in
                  basic_fields
                  if key in catalog[item]} for item in ids]
        click_system = self.click_prompt.replace("{history_instruction}", _instruction(profile))
        click_validator = (self._validate_align_click if self.uses_align_rating_protocol
                           else self._validate_click)
        click_response_name = ("alignment_click_selection" if self.uses_align_rating_protocol
                               else "click_selection")
        click, attempts = self._call("click", click_system,
            {"stage": "click", "profile": profile, "items": basic,
             "retry_feedback": None},
            lambda value: click_validator(value, set(ids), titles), click_response_name)
        clicked = click["clicked_item_ids"]
        if self.uses_align_rating_protocol:
            # This is a deterministic property of the selection, not an LLM judgment.
            click["click_count"] = len(clicked)
            # Preserve the common action field for downstream analysis without asking
            # the model to restate the same pre-click evidence.
            click["click_motives"] = {
                str(item): click["candidate_assessments"][str(item)]["evidence"]
                for item in clicked
            }
        if not clicked:
            empty_conversion = {"converted_item_ids": [], "motive_assessments": {}}
            if self.uses_align_rating_protocol:
                empty_conversion.update({
                    "watch_decision": "not_ready",
                    "decision_reason": "No candidate warranted opening its details",
                })
            return {**click, **empty_conversion}, attempts
        detail_fields = ("item_id", "title", "release_year", "genres")
        if self.exposes_average_rating:
            detail_fields += ("average_rating",)
        detail_fields += ("overview", "director", "cast", "release_date", "language", "country")
        detail_defaults = {"overview": "unknown", "director": "unknown", "cast": [],
                           "release_date": "unknown", "language": "unknown", "country": []}
        details = [{key: catalog[item].get(key, detail_defaults[key])
                    if key in detail_defaults else catalog[item][key]
                    for key in detail_fields}
                   for item in clicked]
        if self.uses_align_rating_protocol:
            for detail in details:
                detail["click_hypothesis"] = click["click_motives"][str(detail["item_id"])]
        conversion_system = self.conversion_prompt.replace(
            "{history_instruction}", _instruction(profile)).replace(
            "{conversion_context_instruction}", FULL_SLATE_CONTEXT)
        conversion_validator = (self._validate_rating_conversion
                                if self.uses_align_rating_protocol
                                else self._validate_conversion)
        conversion_response_name = ("rating_conversion_selection"
                                    if self.uses_align_rating_protocol
                                    else "conversion_selection")
        conversion_payload = {
            "stage": "conversion", "profile": profile, "candidate_slate": basic,
            "clicked_item_ids": clicked, "clicked_items": details,
            "click_motives": click["click_motives"], "retry_feedback": None,
        }
        if self.uses_align_rating_protocol:
            conversion_payload.pop("click_motives")
        conversion, more = self._call("conversion", conversion_system,
            conversion_payload,
            lambda value: conversion_validator(value, clicked, titles), conversion_response_name)
        return {**click, **conversion}, attempts + more
