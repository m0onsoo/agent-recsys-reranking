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
    def _validate_click(value, allowed):
        ids = value["clicked_item_ids"]
        motives = value["click_motives"]
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
            {"profile": profile, "candidates": basic},
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
            {"profile": profile, "candidate_slate": basic, "clicked_item_ids": clicked,
             "clicked_items": details, "click_motives": click["click_motives"]},
            lambda value: self._validate_conversion(value, clicked))
        return {**click, **conversion}, attempts + more
