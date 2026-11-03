"""OpenAI-compatible JSON client with rate and cost circuit breakers."""

import json
import os
import threading
import time
from collections import deque
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class BudgetExceeded(RuntimeError):
    pass


class RateBudget:
    def __init__(self, rpm=300, tpm=1_000_000, max_cost=25.0,
                 input_rate=0.15, output_rate=0.60):
        self.rpm, self.tpm, self.max_cost = rpm, tpm, max_cost
        self.input_rate, self.output_rate = input_rate, output_rate
        self.events = deque()
        self.cost = 0.0
        self.lock = threading.Lock()

    def acquire(self, estimated_tokens):
        if estimated_tokens > self.tpm:
            raise ValueError(f"One request estimate ({estimated_tokens}) exceeds TPM cap ({self.tpm})")
        while True:
            with self.lock:
                now = time.monotonic()
                while self.events and now - self.events[0][0] >= 60:
                    self.events.popleft()
                requests = len(self.events)
                tokens = sum(event[1] for event in self.events)
                if requests < self.rpm and tokens + estimated_tokens <= self.tpm:
                    self.events.append((now, estimated_tokens))
                    return
                wait = max(0.05, 60 - (now - self.events[0][0]))
            time.sleep(min(wait, 5.0))

    def charge(self, prompt_tokens, completion_tokens):
        value = (prompt_tokens * self.input_rate + completion_tokens * self.output_rate) / 1_000_000
        with self.lock:
            if self.cost + value > self.max_cost:
                raise BudgetExceeded(f"Cost limit ${self.max_cost:.2f} would be exceeded")
            self.cost += value
        return value


def api_key(name):
    value = os.environ.get(name)
    if value:
        return value
    env = os.environ.get("AGENT_RERANKING_ENV", ".env")
    if os.path.isfile(env):
        for line in open(env, encoding="utf-8"):
            key, separator, raw = line.partition("=")
            if separator and key.strip() == name:
                return raw.strip().strip("\"'")
    raise RuntimeError(f"Set {name} in the environment or .env")


class OpenAICompatibleClient:
    def __init__(self, model, base_url, key_env="OPENAI_API_KEY", temperature=0.0,
                 timeout=180, budget=None):
        self.model, self.temperature, self.timeout = model, temperature, timeout
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.key = api_key(key_env)
        self.budget = budget or RateBudget()
        self._local = threading.local()

    @property
    def last_call(self):
        return getattr(self._local, "last_call", {})

    @staticmethod
    def request_body(system, user, schema, name, model, temperature):
        """Build the legacy-compatible Chat Completions request body."""
        if name in ("conversion_selection", "rating_conversion_selection"):
            payload = json.loads(user)
            item_schema = {"type": "integer"}
            if payload.get("retry_feedback"):
                item_schema["enum"] = [item["item_id"] for item in payload["clicked_items"]]
            assessment_properties = {
                "outcome": {"type": "string",
                            "enum": ["confirmed", "contradicted", "insufficient"]},
                "decision_note": {"type": "string"}}
            assessment_required = ["outcome", "decision_note"]
            if name == "rating_conversion_selection":
                assessment_properties.update({
                    "predicted_rating": {"type": "integer", "minimum": 1, "maximum": 5},
                    "rating_reason": {"type": "string"},
                })
                assessment_required = [
                    "outcome", "predicted_rating", "rating_reason", "decision_note"]
            assessment = {"type": "object", "properties": assessment_properties,
                "required": assessment_required, "additionalProperties": False}
            properties = {str(item): assessment for item in payload["clicked_item_ids"]}
            response_properties = {
                "converted_item_ids": {"type": "array", "items": item_schema},
                "motive_assessments": {"type": "object", "properties": properties,
                    "required": list(properties), "additionalProperties": False}}
            required = ["converted_item_ids", "motive_assessments"]
            if name == "rating_conversion_selection":
                response_properties.update({
                    "watch_decision": {"type": "string", "enum": ["watch", "not_ready"]},
                    "decision_reason": {"type": "string"},
                })
                response_properties["converted_item_ids"]["maxItems"] = 1
                required = ["watch_decision", "converted_item_ids",
                            "motive_assessments", "decision_reason"]
            schema = {"type": "object", "properties": response_properties,
                "required": required,
                "additionalProperties": False}
        response_format = ({"type": "json_schema", "json_schema": {
            "name": name, "strict": True, "schema": schema}}
            if schema is not None else {"type": "json_object"})
        return {"model": model, "temperature": temperature,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "response_format": response_format}

    def respond_json(self, system, user, schema, name="structured_response"):
        estimated = max(1, (len(system) + len(user)) // 4 + 256)
        self.budget.acquire(estimated)
        body = self.request_body(system, user, schema, name, self.model, self.temperature)
        request = Request(self.url, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except HTTPError as exc:
            raise RuntimeError(f"API returned HTTP {exc.code}") from None
        usage = result.get("usage", {})
        cost = self.budget.charge(usage.get("prompt_tokens", 0),
                                  usage.get("completion_tokens", 0))
        self._local.last_call = {"usage": usage, "estimated_cost_usd": cost}
        return json.loads(result["choices"][0]["message"]["content"])


class MockClient:
    def __init__(self):
        self._local = threading.local()

    @property
    def last_call(self):
        return getattr(self._local, "last_call", {"usage": {}, "estimated_cost_usd": 0.0})

    def respond_json(self, system, user, schema, name="structured_response"):
        if name in ("click_selection", "alignment_click_selection"):
            payload = json.loads(user)
            ids = [item["item_id"] for item in payload.get("items", payload.get("candidates", []))[:2]]
            result = {"clicked_item_ids": ids,
                      "click_motives": {str(item): "The supplied genre warrants inspection"
                                        for item in ids}}
            if name == "alignment_click_selection":
                result.update({
                    "alignment_assessments": {
                        str(item["item_id"]): {
                            "alignment": ("strong" if item["item_id"] in ids else "none"),
                            "reason": "The supplied genres indicate preference alignment"}
                        for item in payload["items"]},
                })
            return result
        if name in ("conversion_selection", "rating_conversion_selection"):
            payload = json.loads(user)
            clicked = payload.get("clicked_item_ids", [])
            assessments = {
                str(item): {"outcome": "confirmed", "decision_note": "Details support viewing"}
                for item in clicked}
            result = {"converted_item_ids": clicked[:1], "motive_assessments": assessments}
            if name == "rating_conversion_selection":
                for assessment in assessments.values():
                    assessment.update({"predicted_rating": 4,
                                       "rating_reason": "The details indicate a likely positive response"})
                result.update({"watch_decision": "watch" if clicked else "not_ready",
                               "decision_reason": ("The strongest option is ready to watch"
                                                   if clicked else "No option is ready to watch")})
            return result
        properties = (schema or {}).get("properties", {})
        if "candidate_personas" in properties:
            return {"candidate_personas": [{"age": "25-34", "occupation": "other",
                                             "personality": {name: 2 for name in
                                               ("openness", "conscientiousness", "extraversion",
                                                "agreeableness", "neuroticism")},
                                             "summary": f"Candidate {index}"}
                                            for index in range(5)]}
        if "best_index" in properties:
            return {"best_index": 0, "scores": [1, 0, 0, 0, 0]}
        return {key: ([] if value.get("type") == "array" else "Observed movie preferences")
                for key, value in properties.items()}
