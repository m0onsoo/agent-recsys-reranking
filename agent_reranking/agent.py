"""Current two-stage click and conversion behavior protocol."""

import json
from pathlib import Path


def _instruction(profile):
    if "interaction_history" in profile:
        return "Treat interaction_history as an unordered sample; do not infer recency from array position."
    return "No interaction history is supplied; do not invent one."


class TwoStageAgent:
    def __init__(self, client, retries=2):
        self.client, self.retries = client, retries
        root = Path(__file__).resolve().parents[1] / "prompts"
        self.click_prompt = (root / "click_behavior_v4_motive_assessment.txt").read_text(encoding="utf-8")
        self.conversion_prompt = (root / "conversion_behavior_v4_motive_assessment.txt").read_text(encoding="utf-8")

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
        ids = value["clicked_item_ids"]
        motives = value["click_motives"]
        if any(not isinstance(item, int) for item in ids):
            raise ValueError("clicked_item_ids must contain integers")
        if len(ids) != len(set(ids)) or not set(ids) <= allowed:
            raise ValueError("Invalid clicked_item_ids")
        if set(motives) != {str(item) for item in ids}:
            raise ValueError("click_motives must exactly cover clicked items")

    @staticmethod
    def _validate_conversion(value, clicked):
        ids = value["converted_item_ids"]
        assessments = value["motive_assessments"]
        if len(ids) != len(set(ids)) or not set(ids) <= set(clicked):
            raise ValueError("Invalid converted_item_ids")
        if set(assessments) != {str(item) for item in clicked}:
            raise ValueError("motive_assessments must exactly cover clicked items")
        if any(row.get("outcome") not in {"confirmed", "contradicted", "insufficient"}
               for row in assessments.values()):
            raise ValueError("Invalid motive assessment outcome")

    def _call(self, stage, system, payload, validator):
        feedback = None
        attempts = []
        for retry in range(self.retries + 1):
            sent = dict(payload)
            if feedback:
                sent["retry_feedback"] = feedback
            try:
                value = self.client.respond_json(system, json.dumps(sent, ensure_ascii=False),
                                                 None, f"{stage}_selection")
                value = (self._canonicalize_click(value) if stage == "click" else
                         self._canonicalize_conversion(value))
                validator(value)
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "valid"})
                return value, attempts
            except (KeyError, TypeError, ValueError) as exc:
                attempts.append({"stage": stage, "retry": retry, **self.client.last_call,
                                 "status": "invalid", "error": str(exc)[:200]})
                if retry == self.retries:
                    raise
                feedback = str(exc)
        raise AssertionError("unreachable")

    def simulate(self, profile, candidate, catalog):
        ids = candidate["item_ids"]
        basic = [{key: catalog[item][key] for key in ("item_id", "title", "release_year", "genres")
                  if key in catalog[item]} for item in ids]
        click_system = self.click_prompt.replace("{history_instruction}", _instruction(profile))
        click, attempts = self._call("click", click_system,
            {"stage": "click", "profile": profile, "items": basic,
             "retry_feedback": None},
            lambda value: self._validate_click(value, set(ids)))
        clicked = click["clicked_item_ids"]
        if not clicked:
            return {**click, "converted_item_ids": [], "motive_assessments": {}}, attempts
        detail_fields = ("item_id", "title", "release_year", "genres", "overview", "director",
                         "cast", "release_date", "language", "country")
        details = [{key: catalog[item][key] for key in detail_fields if key in catalog[item]}
                   for item in clicked]
        context = ("candidate_slate is the complete displayed exposure slate with basic metadata; "
                   "clicked_item_ids identifies opened movies and clicked_items contains their details. "
                   "Select conversions only from clicked_item_ids.")
        conversion_system = self.conversion_prompt.replace(
            "{history_instruction}", _instruction(profile)).replace(
            "{conversion_context_instruction}", context)
        conversion, more = self._call("conversion", conversion_system,
            {"stage": "conversion", "profile": profile, "candidate_slate": basic,
             "clicked_item_ids": clicked, "clicked_items": details,
             "click_motives": click["click_motives"], "retry_feedback": None},
            lambda value: self._validate_conversion(value, clicked))
        return {**click, **conversion}, attempts + more
