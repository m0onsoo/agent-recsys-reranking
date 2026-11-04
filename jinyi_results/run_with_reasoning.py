"""Run agent_reranking's CLI with reasoning-model request tweaks, without editing the repo.

- Adds `reasoning_effort` (from env REASONING_EFFORT) to every chat/completions body.
- Surfaces the API's HTTP error body (truncated) so failures.jsonl shows the real cause.
"""
import json
import os
import sys
from urllib.error import HTTPError

from agent_reranking import client as C
from agent_reranking.cli import main

effort = os.environ.get("REASONING_EFFORT", "").strip()
_orig_body = C.OpenAICompatibleClient.request_body


def request_body(system, user, schema, name, model, temperature):
    body = _orig_body(system, user, schema, name, model, temperature)
    if effort:
        body["reasoning_effort"] = effort
    return body


C.OpenAICompatibleClient.request_body = staticmethod(request_body)

_orig_urlopen = C.urlopen


def urlopen(request, timeout=None):
    try:
        return _orig_urlopen(request, timeout=timeout)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:250]
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from None


C.urlopen = urlopen

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
