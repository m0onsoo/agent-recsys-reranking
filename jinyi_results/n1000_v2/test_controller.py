"""Offline transcript-verifier regression tests; never calls the API."""
import json
import os
import io
import runpy
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import execute_experiment as controller


def main():
    process_id = os.getpid()
    fake_processes = (f"PID PPID ELAPSED COMMAND\n{process_id} 123 00:01 python controller\n"
                      f"123 1 00:01 caffeinate python n1000_v2/execute_experiment.py\n"
                      f"124 {process_id} 00:01 caffeinate python agent_reranking.cli\n"
                      "999999 123 00:01 python -m agent_reranking.cli run\n")
    with patch.object(controller.subprocess, "check_output", return_value=fake_processes):
        assert [row["pid"] for row in controller.other_jobs()] == [999999]
    for condition in controller.CONDITIONS:
        arguments = controller.run_arguments(condition, Path("synthetic_profiles"))
        assert arguments[arguments.index("--concurrency") + 1] == "16"
    with tempfile.TemporaryDirectory(prefix="command_selftest_", dir=controller.ROOT) as temporary, \
         patch.object(controller, "ROOT", Path(temporary)), \
         patch.object(controller, "paid_step", return_value=0) as paid, \
         patch.object(controller, "verify_profiles", return_value={}), patch.object(controller, "event"):
        controller.get_profiles("https://test.invalid/v1", [])
        arguments = paid.call_args.args[1]
        assert arguments[arguments.index("--concurrency") + 1] == "16"
        assert "--resume" in arguments and arguments[arguments.index("--max-retries") + 1] == "3"
    with tempfile.TemporaryDirectory(prefix="selftest_", dir=controller.ROOT) as temporary:
        root = Path(temporary)
        (root / "prompts").mkdir()
        prompt = "Synthetic system prompt"
        import hashlib
        checksum = hashlib.sha256(prompt.encode()).hexdigest()
        (root / "prompts" / f"{checksum}.txt").write_text(prompt)
        records = []
        for call_id, response_name in (("click", "alignment_click_selection"), ("convert", "rating_conversion_selection")):
            records.extend([
                {"kind": "exchange", "call_id": call_id, "model": "MF", "user_id": 1,
                 "response_name": response_name, "raw_response": "{}", "response_model": "synthetic", "message_extras": {}},
                {"kind": "validation", "call_id": call_id, "status": "valid"},
            ])
        records.append({"kind": "validation", "call_id": "old-failure", "status": "invalid", "error": "at most one sentence"})
        (root / "transcripts.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
        (root / "calls.jsonl").write_text('{"call_id":"click"}\n{"call_id":"convert"}\n')
        actions = [{"model": "MF", "user_id": 1, "actions": {"clicked_item_ids": [9]}}]
        summary, hashes = controller.verify_transcripts(root, actions)
        assert summary["exchanges"] == 2
        assert summary["invalid_validations"] == 1
        assert summary["at_most_one_sentence_errors"] == 1
        assert len(hashes) == 2
        (root / "transcripts.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records if row.get("call_id") != "convert" or row["kind"] != "validation"))
        try:
            controller.verify_transcripts(root, actions)
        except RuntimeError as exception:
            assert "validation" in str(exception)
        else:
            raise AssertionError("Missing validation was not rejected")
    from agent_reranking import client
    for succeeds in (True, False):
        with tempfile.TemporaryDirectory(prefix="monitor_selftest_", dir=controller.ROOT) as temporary:
            root = Path(temporary)
            response = io.StringIO(json.dumps({"choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}))
            errors = [HTTPError("https://test.invalid", 429, "limited", {}, io.BytesIO(b"limited")) for _ in range(2)]
            with patch.dict(os.environ, {"N1000_STEP": "selftest", "N1000_LEDGER": str(root / "costs.jsonl"),
                     "N1000_STOP_FILE": str(root / "stop.json")}), \
                 patch.object(client, "api_key", side_effect=lambda name: "test-key" if name == "OPENAI_API_KEY" else "https://test.invalid"), \
                 patch.object(client, "urlopen", side_effect=[errors[0], response] if succeeds else errors) as request, \
                 patch.object(client.RateBudget, "charge", client.RateBudget.charge), \
                 patch.object(client.OpenAICompatibleClient, "respond_json", client.OpenAICompatibleClient.respond_json), \
                 patch.object(sys, "stdout", sys.stdout), patch.object(sys, "stderr", io.StringIO()):
                runpy.run_path(str(controller.ROOT / "monitoring/sitecustomize.py"))
                instance = client.OpenAICompatibleClient("test", "https://test.invalid/v1", max_retries=1,
                    retry_base_delay=0, retry_max_delay=0)
                instance.transcript_dir = root
                try:
                    instance.respond_json("SYSTEM", "USER", None)
                except client.APITransportError:
                    assert not succeeds
                assert request.call_count == 2
                assert (root / "stop.json").exists() != succeeds
                exchanges = [row for row in controller.json_rows(root / "transcripts.jsonl") if row["kind"] == "exchange"]
                assert len(exchanges) == 2 and exchanges[0]["http_code"] == 429
                charges = [row for row in controller.json_rows(root / "costs.jsonl") if row["kind"] == "charge"]
                assert len(charges) == (1 if succeeds else 0)
    print("Controller self-test passed: process detection, transcript coverage, hashes, counts, missing-validation rejection; no API calls")


if __name__ == "__main__":
    main()
