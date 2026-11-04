"""OpenAI-compatible JSON client with rate and cost circuit breakers."""

import hashlib
import json
import os
import random
import re
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from collections import deque
from urllib.error import HTTPError
from urllib.error import URLError
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen


class BudgetExceeded(RuntimeError):
    pass


class APITransportError(RuntimeError):
    def __init__(self, message, status_code, retry_after=0.0):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


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
                if self.cost >= self.max_cost:
                    raise BudgetExceeded(f"Cost limit ${self.max_cost:.2f} reached")
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
            self.cost += value
            if self.cost > self.max_cost:
                raise BudgetExceeded(f"Cost limit ${self.max_cost:.2f} would be exceeded")
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
                 timeout=180, budget=None, max_retries=3, retry_base_delay=1.0,
                 retry_max_delay=60.0, stop_on_transport_error=False):
        if max_retries < 0 or retry_base_delay < 0 or retry_max_delay < retry_base_delay:
            raise ValueError("Invalid API retry limits")
        self.max_retries = max_retries
        self.retry_base_delay, self.retry_max_delay = retry_base_delay, retry_max_delay
        self._retry_lock = threading.Lock()
        self._retry_until = 0.0
        self.stop_on_transport_error = stop_on_transport_error
        self._transport_stopped = threading.Event()
        self.model, self.temperature, self.timeout = model, temperature, timeout
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.key = api_key(key_env)
        self.budget = budget or RateBudget()
        self._local = threading.local()
        # Transcript logging: when transcript_dir is set, every API exchange (including
        # failed validations and HTTP errors) is appended to transcript_dir/transcripts.jsonl
        # and each distinct system prompt is stored once under transcript_dir/prompts/.
        self.transcript_dir = None
        self._transcript_lock = threading.Lock()
        self._saved_prompts = set()

    @property
    def last_call(self):
        return getattr(self._local, "last_call", {})

    def set_context(self, reset=False, **values):
        context = {} if reset else dict(getattr(self._local, "context", {}))
        context.update(values)
        self._local.context = context

    def _write_transcript(self, row, system=None):
        if self.transcript_dir is None:
            return
        root = Path(self.transcript_dir)
        root.mkdir(parents=True, exist_ok=True)
        record = {"utc": datetime.now(timezone.utc).isoformat(),
                  **getattr(self._local, "context", {})}
        with self._transcript_lock:
            if system is not None:
                digest = hashlib.sha256(system.encode("utf-8")).hexdigest()
                record["system_prompt_sha256"] = digest
                if digest not in self._saved_prompts:
                    prompts = root / "prompts"
                    prompts.mkdir(parents=True, exist_ok=True)
                    target = prompts / f"{digest}.txt"
                    if not target.exists():
                        target.write_text(system, encoding="utf-8")
                    self._saved_prompts.add(digest)
            record.update(row)
            with (root / "transcripts.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def record_validation(self, call_id, status, error=None):
        """Append the validation verdict for a previously logged exchange."""
        row = {"kind": "validation", "call_id": call_id, "status": status}
        if error:
            row["error"] = error
        self._write_transcript(row)

    @staticmethod
    def request_body(system, user, schema, name, model, temperature):
        """Build the legacy-compatible Chat Completions request body."""
        if name in ("debiased_click_selection", "debiased_conversion_selection"):
            from copy import deepcopy
            schema = deepcopy(schema)
            payload = json.loads(user)
            is_click = name == "debiased_click_selection"
            ids = ([item["item_id"] for item in payload["items"]] if is_click
                   else payload["clicked_item_ids"])
            field = "candidate_assessments" if is_click else "motive_assessments"
            collection = schema["properties"][field]
            assessment = collection["additionalProperties"]
            collection.update(properties={str(item): assessment for item in ids},
                              required=[str(item) for item in ids], additionalProperties=False)
            selected = schema["properties"]["clicked_item_ids" if is_click else "converted_item_ids"]
            selected["items"]["enum"] = ids
            selected.pop("uniqueItems", None)
        if name == "alignment_click_selection":
            payload = json.loads(user)
            ids = [str(item["item_id"]) for item in payload["items"]]
            assessment = {"type": "object", "properties": {
                "alignment": {"type": "string", "enum": ["strong", "adjacent", "none"]},
                "evidence": {"type": "string"}},
                "required": ["alignment", "evidence"], "additionalProperties": False}
            schema = {"type": "object", "properties": {
                "candidate_assessments": {"type": "object",
                    "properties": {item: assessment for item in ids},
                    "required": ids, "additionalProperties": False},
                "clicked_item_ids": {"type": "array", "items": {
                    "type": "integer", "enum": [int(item) for item in ids]}}},
                "required": ["candidate_assessments", "clicked_item_ids"],
                "additionalProperties": False}
        elif name in ("conversion_selection", "rating_conversion_selection"):
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
                    "reason": {"type": "string"},
                })
                assessment_properties.pop("decision_note")
                assessment_required = ["outcome", "predicted_rating", "reason"]
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

    def _safe_error(self, value):
        value = str(value).replace(self.key, "[REDACTED]")
        return re.sub(r"https?://[^\s\"'<>]+", "[URL REDACTED]", value)

    @staticmethod
    def _retry_after(headers):
        value = headers.get("Retry-After", "") if headers else ""
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
            except (ValueError, TypeError, OverflowError):
                return 0.0

    def respond_json(self, system, user, schema, name="structured_response"):
        self._local.last_call = {}
        if self._transport_stopped.is_set():
            raise RuntimeError("Transport safety stop is active; user approval required")
        for attempt in range(self.max_retries + 1):
            self.set_context(transport_retry=attempt)
            while True:
                with self._retry_lock:
                    delay = self._retry_until - time.monotonic()
                if delay <= 0:
                    break
                time.sleep(delay)
            try:
                return self._respond_once(system, user, schema, name)
            except (APITransportError, URLError, TimeoutError, ConnectionError,
                    socket.timeout, json.JSONDecodeError) as exception:
                if self.stop_on_transport_error and not isinstance(exception, json.JSONDecodeError):
                    self._transport_stopped.set()
                    self._write_transcript({"kind": "safety_stop",
                        "call_id": self.last_call.get("call_id"),
                        "reason": "HTTP or transport error; user approval required"})
                    raise
                retryable = not isinstance(exception, APITransportError) or exception.status_code in (
                    408, 429, 500, 502, 503, 504)
                call_id = self.last_call.get("call_id")
                if isinstance(exception, json.JSONDecodeError) and call_id:
                    self.record_validation(call_id, "invalid", "Invalid JSON response")
                if not retryable or attempt == self.max_retries:
                    self._write_transcript({"kind": "retry_exhausted", "call_id": call_id,
                        "attempts": attempt + 1, "error_type": type(exception).__name__,
                        "retryable": retryable})
                    raise
                backoff = min(self.retry_max_delay, self.retry_base_delay * 2 ** attempt)
                delay = max(getattr(exception, "retry_after", 0.0),
                            min(self.retry_max_delay, backoff + random.uniform(0, backoff * .25)))
                with self._retry_lock:
                    self._retry_until = max(self._retry_until, time.monotonic() + delay)
                self._write_transcript({"kind": "retry", "call_id": call_id,
                    "delay_seconds": delay, "error_type": type(exception).__name__})

    def _respond_once(self, system, user, schema, name):
        estimated = max(1, (len(system) + len(user)) // 4 + 256)
        self.budget.acquire(estimated)
        if self._transport_stopped.is_set():
            raise RuntimeError("Transport safety stop is active; user approval required")
        body = self.request_body(system, user, schema, name, self.model, self.temperature)
        call_id = uuid.uuid4().hex
        request_params = {key: value for key, value in body.items()
                          if key not in ("messages", "response_format")}
        exchange = {"kind": "exchange", "call_id": call_id, "response_name": name,
                    "request_params": request_params, "user_prompt": user}
        request = Request(self.url, data=json.dumps(body).encode(), headers={
            "Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.load(response)
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", "replace")[:300]
            except Exception:
                detail = ""
            self._local.last_call = {"usage": {}, "estimated_cost_usd": 0.0, "call_id": call_id}
            detail = self._safe_error(detail)
            self._write_transcript({**exchange, "error": f"HTTP {exc.code}: {detail}",
                                    "http_code": exc.code,
                                    "latency_seconds": round(time.monotonic() - started, 3)},
                                   system)
            raise APITransportError(f"API returned HTTP {exc.code}: {detail}", exc.code,
                                    self._retry_after(exc.headers)) from None
        except Exception as exc:
            self._local.last_call = {"usage": {}, "estimated_cost_usd": 0.0, "call_id": call_id}
            self._write_transcript({**exchange, "error": f"{type(exc).__name__}: {self._safe_error(exc)[:300]}",
                                    "latency_seconds": round(time.monotonic() - started, 3)},
                                   system)
            if isinstance(exc, URLError):
                raise URLError(self._safe_error(exc.reason)) from None
            raise
        usage = result.get("usage", {})
        choice = (result.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content")
        # Keep any non-content message fields the provider returns (e.g. reasoning_content,
        # reasoning summaries, refusal) so reasoning traces are retained when available.
        extras = {key: value for key, value in message.items()
                  if key not in ("role", "content") and value not in (None, "", [], {})}
        self._local.last_call = {"usage": usage, "estimated_cost_usd": 0.0, "call_id": call_id}
        self._write_transcript({
            **exchange, "response_id": result.get("id"), "response_model": result.get("model"),
            "system_fingerprint": result.get("system_fingerprint"),
            "finish_reason": choice.get("finish_reason"), "usage": usage,
            "raw_response": content, "message_extras": extras,
            "latency_seconds": round(time.monotonic() - started, 3)}, system)
        cost = self.budget.charge(usage.get("prompt_tokens", 0),
                                  usage.get("completion_tokens", 0))
        self._local.last_call = {"usage": usage, "estimated_cost_usd": cost, "call_id": call_id}
        if not isinstance(content, str):
            raise json.JSONDecodeError("Missing JSON response content", "", 0)
        return json.loads(content)


class MockClient:
    def __init__(self):
        self._local = threading.local()
        self.transcript_dir = None

    def set_context(self, reset=False, **values):
        return None

    def record_validation(self, call_id, status, error=None):
        return None

    @property
    def last_call(self):
        return getattr(self._local, "last_call", {"usage": {}, "estimated_cost_usd": 0.0})

    def respond_json(self, system, user, schema, name="structured_response"):
        if name == "debiased_click_selection":
            payload = json.loads(user)
            ids = [item["item_id"] for item in payload["items"][:2]]
            return {"candidate_assessments": {str(item["item_id"]): {
                "interest": 4 if item["item_id"] in ids else 2,
                "evidence": "The supplied history suggests this degree of personal fit"}
                for item in payload["items"]}, "clicked_item_ids": ids}
        if name == "debiased_conversion_selection":
            ids = json.loads(user)["clicked_item_ids"]
            return {"watch_decision": "watch" if ids else "not_ready",
                "converted_item_ids": ids[:1], "motive_assessments": {str(item): {
                    "outcome": "confirmed", "watch_likelihood": 4,
                    "reason": "The details fit the supplied history"} for item in ids},
                "decision_reason": "The personal evidence supports this viewing choice"}
        if name in ("click_selection", "alignment_click_selection"):
            payload = json.loads(user)
            ids = [item["item_id"] for item in payload.get("items", payload.get("candidates", []))[:2]]
            result = {"clicked_item_ids": ids,
                      "click_motives": {str(item): "The supplied genre warrants inspection"
                                        for item in ids}}
            if name == "alignment_click_selection":
                result = {
                    "candidate_assessments": {
                        str(item["item_id"]): {
                            "alignment": ("strong" if item["item_id"] in ids else "none"),
                            "evidence": "The supplied genres indicate preference alignment"}
                        for item in payload["items"]},
                    "clicked_item_ids": ids,
                }
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
                    assessment.pop("decision_note")
                    assessment.update({"predicted_rating": 4,
                                       "reason": "The details indicate a likely positive response"})
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
