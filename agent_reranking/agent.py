"""Current two-stage click and conversion behavior protocol."""

import json
import re
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
    "behavior-motive-assessment-v1": (
        "legacy/click_behavior_motive_assessment_v1.txt",
        "legacy/conversion_behavior_motive_assessment_v1.txt",
    ),
    "behavior-motive-assessment-v2": (
        "click_behavior_motive_assessment.txt",
        "conversion_behavior_motive_assessment.txt",
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
        self.exposes_average_rating = prompt_version == "behavior-motive-assessment-v2"

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
    def _validate_click(value, allowed):
        Draft202012Validator(MOTIVE_CLICK_SCHEMA).validate(value)
        ids = value["clicked_item_ids"]
        motives = value["click_motives"]
        if not set(ids).issubset(allowed):
            raise ValueError("click selected an item outside the permitted set")
        if set(motives) != {str(item) for item in ids}:
            TwoStageAgent._raise_key_mismatch(
                "click_motives", motives, {str(item) for item in ids}, "clicked_item_ids")
        for item, motive in motives.items():
            TwoStageAgent._validate_short_sentence(motive, f"click_motives[{item}]")

    @staticmethod
    def _validate_conversion(value, clicked):
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
                assessment.get("decision_note"), f"motive_assessments[{item}].decision_note")

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
    def _validate_short_sentence(value, field):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
        if len(value.split()) > 20:
            raise ValueError(f"{field} must contain at most 20 words")
        boundary_text = re.sub(r"(?:\b[A-Za-z]\.){2,}",
                               lambda match: match.group(0).replace(".", ""), value.strip())
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
        if "at most 20 words" in str(feedback):
            rendered += (" Rewrite every motive and decision_note using no more than 15 "
                         "space-separated words. Count the words before returning the complete JSON.")
        return rendered

    def _call(self, stage, system, payload, validator):
        feedback = None
        attempts = []
        for retry in range(self.retries + 1):
            sent = dict(payload)
            if feedback:
                sent["retry_feedback"] = feedback
            try:
                rendered_system = self._retry_system(system, feedback) if feedback else system
                value = self.client.respond_json(rendered_system, json.dumps(sent, ensure_ascii=False),
                                                 None, f"{stage}_selection")
                validator(value)
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "valid"})
                return value, attempts
            except (KeyError, TypeError, ValueError, ValidationError) as exc:
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "invalid", "error": str(exc)[:200]})
                if retry == self.retries:
                    raise
                feedback = str(exc)
        raise AssertionError("unreachable")

    def simulate(self, profile, candidate, catalog):
        ids = candidate["item_ids"]
        basic_fields = ("item_id", "title", "release_year", "genres")
        if self.exposes_average_rating:
            basic_fields += ("average_rating",)
        basic = [{key: catalog[item][key] for key in
                  basic_fields
                  if key in catalog[item]} for item in ids]
        click_system = self.click_prompt.replace("{history_instruction}", _instruction(profile))
        click, attempts = self._call("click", click_system,
            {"stage": "click", "profile": profile, "items": basic,
             "retry_feedback": None},
            lambda value: self._validate_click(value, set(ids)))
        clicked = click["clicked_item_ids"]
        if not clicked:
            return {**click, "converted_item_ids": [], "motive_assessments": {}}, attempts
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
        conversion_system = self.conversion_prompt.replace(
            "{history_instruction}", _instruction(profile)).replace(
            "{conversion_context_instruction}", FULL_SLATE_CONTEXT)
        conversion, more = self._call("conversion", conversion_system,
            {"stage": "conversion", "profile": profile, "candidate_slate": basic,
             "clicked_item_ids": clicked, "clicked_items": details,
             "click_motives": click["click_motives"], "retry_feedback": None},
            lambda value: self._validate_conversion(value, clicked))
        return {**click, **conversion}, attempts + more
