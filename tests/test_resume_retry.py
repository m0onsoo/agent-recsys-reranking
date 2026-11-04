import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from agent_reranking.client import APITransportError, BudgetExceeded, MockClient, OpenAICompatibleClient, RateBudget
from agent_reranking.io import read_jsonl
from agent_reranking.profiles import _ProfileClient, generate_profiles


class ProfileResumeTests(unittest.TestCase):
    def setUp(self):
        traits = {name: {"level": 2, "value": 10} for name in ("activity", "diversity", "conformity")}
        self.bundle = SimpleNamespace(
            users=[1, 2], social_traits={1: traits, 2: traits}, trait_thresholds={},
            trait_population_scope="materialized_panel",
            histories={user: {"raw_user_id": str(user),
                "demographics": {"age": "25", "gender": "F", "occupation": "12"},
                "train_interactions": [{"item_id": user, "timestamp": 1, "rating": 4}]}
                for user in (1, 2)},
            movie=lambda item, detail=False: {"item_id": item, "title": f"Movie {item}",
                "release_year": "1999", "genres": ["Drama"]})

    def test_failed_user_does_not_discard_success_and_resume_only_retries_missing(self):
        calls = []

        def persona(method, bundle, user, client, seed, traits):
            calls.append(user)
            if user == 2 and calls.count(2) == 1:
                raise RuntimeError("temporary failure")
            return {"unique_tastes": [], "liked_patterns": [], "disliked_patterns": []}, {"calls": 1}

        with tempfile.TemporaryDirectory() as temporary, patch("agent_reranking.profiles.generate_persona", side_effect=persona):
            with self.assertRaisesRegex(RuntimeError, "1/2 saved"):
                generate_profiles(self.bundle, MockClient(), output_dir=temporary, concurrency=1)
            self.assertTrue((Path(temporary) / "checkpoints/1.json").exists())
            self.assertEqual([row["user_id"] for row in read_jsonl(Path(temporary) / "profiles.jsonl")], [1])
            generate_profiles(self.bundle, MockClient(), output_dir=temporary, concurrency=1, resume=True)
            self.assertEqual(calls, [1, 2, 2])
            self.assertEqual([row["user_id"] for row in read_jsonl(Path(temporary) / "profiles.jsonl")], [1, 2])
            with self.assertRaisesRegex(ValueError, "configuration"):
                generate_profiles(self.bundle, MockClient(), seed=43, output_dir=temporary, resume=True)
            with self.assertRaisesRegex(ValueError, "already exists"):
                generate_profiles(self.bundle, MockClient(), output_dir=temporary)

    def test_complete_resume_makes_no_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            generate_profiles(self.bundle, MockClient(), output_dir=temporary)
            with patch.object(MockClient, "respond_json", side_effect=AssertionError("Unexpected API call")):
                generate_profiles(self.bundle, MockClient(), output_dir=temporary, resume=True)

    def test_offline_recovery_never_requests_missing_users(self):
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(MockClient, "respond_json", side_effect=AssertionError("Unexpected API call")):
            result = generate_profiles(self.bundle, MockClient(), output_dir=temporary,
                resume=True, recover_only=True)
            self.assertEqual(result["completed_users"], 0)
            self.assertFalse((Path(temporary) / "profile_failures.jsonl").exists())
            manifest = json.loads((Path(temporary) / "run_manifest.json").read_text())
            self.assertEqual(manifest["status"], "partial")

    def test_truncated_transcript_tail_is_preserved_and_removed_before_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "transcripts.jsonl"
            path.write_bytes(b'{"kind":"validation"}\n{"kind":')
            generate_profiles(self.bundle, MockClient(), output_dir=temporary, resume=True, recover_only=True)
            self.assertEqual(path.read_bytes(), b'{"kind":"validation"}\n')
            self.assertEqual((Path(temporary) / "transcripts.incomplete").read_bytes(), b'{"kind":')

    def test_checkpoint_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            generate_profiles(self.bundle, MockClient(), output_dir=temporary)
            path = Path(temporary) / "checkpoints/1.json"
            saved = json.loads(path.read_text())
            saved["profile"]["raw_user_id"] = "different"
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError, "Invalid profile checkpoint"):
                generate_profiles(self.bundle, MockClient(), output_dir=temporary, resume=True)

    def test_transcript_replay_requires_matching_request_and_valid_schema(self):
        client = MockClient()
        client.model, client.temperature = "test", 0.0
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
        exchange = {"response_name": "profile", "user_prompt": "USER",
            "system_prompt_sha256": hashlib.sha256(b"SYSTEM").hexdigest(),
            "request_params": {"model": "test", "temperature": 0.0},
            "raw_response": '{"summary":"saved"}'}
        replay = _ProfileClient(client, [exchange])
        with patch.object(client, "respond_json", side_effect=AssertionError("Unexpected API call")):
            self.assertEqual(replay.respond_json("SYSTEM", "USER", schema, "profile"), {"summary": "saved"})
        with patch.object(client, "respond_json", return_value={"summary": "new"}) as request:
            self.assertEqual(replay.respond_json("SYSTEM", "CHANGED", schema, "profile"), {"summary": "new"})
            request.assert_called_once()
        exchange["raw_response"] = '{"summary":3}'
        with patch.object(client, "respond_json", return_value={"summary": "new"}) as request:
            replay.respond_json("SYSTEM", "USER", schema, "profile")
            request.assert_called_once()


class ClientRetryTests(unittest.TestCase):
    def client(self, **options):
        with patch("agent_reranking.client.api_key", return_value="test-secret"):
            return OpenAICompatibleClient("test", "https://test.invalid/v1",
                retry_base_delay=0, retry_max_delay=0, **options)

    def response(self, content='{"ok":true}'):
        return io.StringIO(json.dumps({"model": "test", "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}))

    def test_http429_is_logged_and_retried_with_identical_request(self):
        client = self.client(max_retries=1)
        error = HTTPError(client.url, 429, "limited", {}, io.BytesIO(b"test-secret https://test.invalid/private"))
        with tempfile.TemporaryDirectory() as temporary, patch("agent_reranking.client.urlopen", side_effect=[error, self.response()]) as request:
            client.transcript_dir = temporary
            self.assertEqual(client.respond_json("SYSTEM", "USER", None), {"ok": True})
            self.assertEqual(request.call_count, 2)
            self.assertEqual(request.call_args_list[0].args[0].data, request.call_args_list[1].args[0].data)
            rows = read_jsonl(Path(temporary) / "transcripts.jsonl")
            self.assertEqual([row["transport_retry"] for row in rows if row["kind"] == "exchange"], [0, 1])
            text = (Path(temporary) / "transcripts.jsonl").read_text()
            self.assertNotIn("test-secret", text)
            self.assertNotIn("https://test.invalid", text)

    def test_transient_errors_retry_but_authentication_does_not(self):
        for error in (URLError("connection reset"), TimeoutError("timeout"),
                      HTTPError("https://test.invalid", 503, "unavailable", {}, io.BytesIO(b""))):
            with self.subTest(error=type(error).__name__), patch("agent_reranking.client.urlopen", side_effect=[error, self.response()]) as request:
                self.assertEqual(self.client(max_retries=1).respond_json("SYSTEM", "USER", None), {"ok": True})
                self.assertEqual(request.call_count, 2)
        with patch("agent_reranking.client.urlopen", side_effect=HTTPError("https://test.invalid", 401, "auth", {}, io.BytesIO(b""))) as request:
            with self.assertRaises(APITransportError):
                self.client().respond_json("SYSTEM", "USER", None)
            request.assert_called_once()

    def test_retry_exhaustion_is_bounded(self):
        with patch("agent_reranking.client.urlopen", side_effect=TimeoutError("timeout")) as request:
            with self.assertRaises(TimeoutError):
                self.client(max_retries=2).respond_json("SYSTEM", "USER", None)
            self.assertEqual(request.call_count, 3)

    def test_invalid_json_is_charged_before_retry(self):
        client = self.client(max_retries=1)
        with patch("agent_reranking.client.urlopen", side_effect=[self.response("invalid"), self.response()]):
            self.assertEqual(client.respond_json("SYSTEM", "USER", None), {"ok": True})
        self.assertAlmostEqual(client.budget.cost, 2 * (10 * .15 + 5 * .60) / 1_000_000)

    def test_budget_stop_counts_response_and_does_not_retry(self):
        client = self.client(budget=RateBudget(max_cost=.000001))
        with patch("agent_reranking.client.urlopen", return_value=self.response()) as request:
            with self.assertRaises(BudgetExceeded):
                client.respond_json("SYSTEM", "USER", None)
            self.assertGreater(client.budget.cost, client.budget.max_cost)
            with self.assertRaises(BudgetExceeded):
                client.respond_json("SYSTEM", "USER", None)
            request.assert_called_once()

    def test_retry_after_seconds_and_date(self):
        self.assertEqual(OpenAICompatibleClient._retry_after({"Retry-After": "12"}), 12)
        with patch("agent_reranking.client.time.time", return_value=0):
            self.assertEqual(OpenAICompatibleClient._retry_after({"Retry-After": "Thu, 01 Jan 1970 00:01:00 GMT"}), 60)
        self.assertEqual(OpenAICompatibleClient._retry_after({"Retry-After": "invalid"}), 0)