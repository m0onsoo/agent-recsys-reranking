import json
import os
import re
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.error import URLError


def install():
    if not os.environ.get("N1000_STEP"):
        return
    from agent_reranking import client

    ledger = Path(os.environ["N1000_LEDGER"])
    stop_file = Path(os.environ["N1000_STOP_FILE"])
    ledger.parent.mkdir(parents=True, exist_ok=True)
    mutex = threading.Lock()
    recorded = 0.0
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            recorded += json.loads(line).get("estimated_cost_usd", 0.0)
    secrets = [client.api_key("OPENAI_API_KEY"), client.api_key("OPENAI_ENDPOINT")]
    endpoint = secrets[-1].rstrip("/")
    secrets.extend([endpoint, endpoint + "/v1", endpoint + "/chat/completions"])
    secrets = sorted(set(secrets), key=len, reverse=True)

    class RedactedStream:
        def __init__(self, source):
            self.source = source

        def write(self, text):
            for secret in secrets:
                if secret:
                    text = text.replace(secret, "[REDACTED]")
            return self.source.write(re.sub(r"https?://[^\s\"'<>]+", "[URL REDACTED]", text))

        def __getattr__(self, name):
            return getattr(self.source, name)

    sys.stdout = RedactedStream(sys.stdout)
    sys.stderr = RedactedStream(sys.stderr)

    def append(record):
        record.update(utc=datetime.now(timezone.utc).isoformat(), step=os.environ["N1000_STEP"])
        with ledger.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def stop(reason, immediate=True):
        stop_file.write_text(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
                             "step": os.environ["N1000_STEP"], "reason": reason,
                             "recorded_cost_usd": recorded}, indent=2) + "\n")
        print(f"SAFETY STOP: {reason}; user approval required", file=sys.stderr, flush=True)
        if immediate:
            os._exit(86)

    original_charge = client.RateBudget.charge

    def charge(budget, prompt_tokens, completion_tokens):
        nonlocal recorded
        value = (prompt_tokens * budget.input_rate + completion_tokens * budget.output_rate) / 1_000_000
        with mutex:
            append({"kind": "charge", "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens, "estimated_cost_usd": value})
            recorded += value
            if recorded > 35.0:
                stop("total_recorded_cost_exceeded_35_usd")
        return original_charge(budget, prompt_tokens, completion_tokens)

    original_urlopen = client.urlopen

    def error_category(exception):
        message = str(exception).lower()
        code = exception.code if isinstance(exception, HTTPError) else getattr(exception, "status_code", None)
        return (f"http_{code}" if code is not None else
                "timeout" if isinstance(exception, TimeoutError) or "timed out" in message or "timeout" in message else
            "rate_limit" if "rate limit" in message or "rate-limit" in message or "rate_limit" in message else
            "transport_error" if isinstance(exception, (URLError, ConnectionError)) else
            "step_cost_budget_exceeded" if isinstance(exception, client.BudgetExceeded) else None)

    def urlopen(*arguments, **keywords):
        try:
            return original_urlopen(*arguments, **keywords)
        except Exception as exception:
            category = error_category(exception)
            with mutex:
                append({"kind": "transport_error", "error_type": type(exception).__name__,
                        "http_code": exception.code if isinstance(exception, HTTPError) else None,
                        "category": category})
            raise

    original_respond = client.OpenAICompatibleClient.respond_json

    def respond_json(instance, *arguments, **keywords):
        if stop_file.exists():
            raise RuntimeError("Safety stop is active; no new API requests are allowed")
        try:
            return original_respond(instance, *arguments, **keywords)
        except Exception as exception:
            category = error_category(exception)
            if category:
                with mutex:
                    append({"kind": "response_error", "error_type": type(exception).__name__, "category": category})
                    stop(f"retry_exhausted_or_permanent_{category}", immediate=False)
            raise

    client.RateBudget.charge = charge
    client.urlopen = urlopen
    client.OpenAICompatibleClient.respond_json = respond_json
    with mutex:
        append({"kind": "monitor_installed"})


install()