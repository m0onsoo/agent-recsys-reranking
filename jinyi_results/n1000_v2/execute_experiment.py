import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
import select
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent / "agent-recsys-reranking"
PYTHON = REPO / ".venv/bin/python"
BUNDLE = "data/derived/ml1m_ro_n1000_seed42"
PANEL = "data/panels/users_1000_seed42.csv"
EXPECTED_STATUS = "?? agent_reranking_bench.egg-info/"
MODELS = ("MF", "LightGCN", "MultiVAE")
BASELINES = {"MF": (0.1739993, 0.2814531),
             "LightGCN": (0.2052061, 0.3441975),
             "MultiVAE": (0.2048144, 0.3300995)}
CONDITIONS = {"full": "all", "no_demographics": "history,unique_tastes,social_traits",
              "no_persona": "history,demographics",
              "no_interaction_history": "unique_tastes,social_traits,demographics"}
ARTIFACTS = ("config.yaml", "run_manifest.json", "actions.jsonl", "calls.jsonl",
             "failures.jsonl", "rankings.jsonl", "per_user_metrics.csv",
             "rating_stratified_metrics.csv", "summary.csv")
PROFILE_FILES = ("profiles.jsonl", "profile_manifests.jsonl", "run_manifest.json")
LEDGER = ROOT / "request_costs.jsonl"
STOP_FILE = ROOT / "STOP_REQUEST.json"
CONCURRENCY = 16
REQUESTS_PER_MINUTE = 300
TOKENS_PER_MINUTE = 1_000_000
MAX_RESUME_PASSES = 3
REPORT_INTERVAL = 1800


def code_version_path():
    updated = ROOT / "code_version_resume_before.json"
    return updated if updated.exists() else ROOT / "code_version_before.json"


def json_rows(path):
    if not path.exists():
        return []
    result = []
    with path.open() as source:
        for line in source:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                if line.endswith("\n"):
                    raise
    return result


def step_cost(step):
    return sum(row.get("estimated_cost_usd", 0.0) for row in json_rows(LEDGER)
               if row.get("step") == step)


def total_cost():
    return sum(row.get("estimated_cost_usd", 0.0) for row in json_rows(LEDGER))


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event(step, state, **details):
    record = {"utc": now(), "step": step, "state": state, **details}
    with (ROOT / "execution_events.jsonl").open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    with (ROOT / "timeline.md").open("a") as handle:
        handle.write(f"| {record['utc']} | {step} | {state} | {json.dumps(details, sort_keys=True)} |\n")
    print(f"{record['utc']} {step}: {state} {json.dumps(details, sort_keys=True)}", flush=True)


def git_state():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    paths = subprocess.check_output(["git", "ls-files", "agent_reranking", "tests", "configs", "prompts"], cwd=REPO, text=True).splitlines()
    return {"commit": commit, "branch": branch, "git_status": status,
            "source_sha256": {path: digest(REPO / path) for path in paths},
            "resume_test_sha256": digest(REPO / "tests/test_resume_retry.py")}


def other_jobs():
    output = subprocess.check_output(["ps", "-axo", "pid,ppid,etime,command"], text=True)
    records = [line.split(None, 3) for line in output.splitlines()[1:]]
    parents = {int(fields[0]): int(fields[1]) for fields in records if len(fields) == 4}
    ancestors = {os.getpid()}
    current = os.getpid()
    while parents.get(current, 0) and parents[current] not in ancestors:
        current = parents[current]
        ancestors.add(current)
    found = []
    for fields in records:
        if len(fields) != 4:
            continue
        process_id, parent_id, elapsed, command = fields
        if int(process_id) in ancestors or int(parent_id) == os.getpid() or str(ROOT) in command or "n1000_v2/execute_experiment.py" in command:
            continue
        if any(marker in command for marker in ("agent_reranking.cli", "agent-reranking",
                                                "execute_experiment.py", "run_experiment.py", "run_with_reasoning.py", "run_pilot")):
            found.append({"pid": int(process_id), "ppid": int(parent_id), "elapsed": elapsed})
    return found


def offline_step(step, arguments):
    event(step, "start")
    with (ROOT / f"{step}.stdout.log").open("w") as stdout, (ROOT / f"{step}.stderr.log").open("w") as stderr:
        child = subprocess.Popen(["caffeinate", "-i", "nohup", str(PYTHON), *arguments],
                                 cwd=REPO, env=os.environ.copy(), stdout=stdout, stderr=stderr)
        return_code = child.wait()
    event(step, "end", exit_code=return_code, recorded_cost_usd=0.0)
    if return_code:
        raise RuntimeError(f"{step} failed; retained stdout/stderr logs")


def prepare():
    from agent_reranking.client import api_key

    before = git_state()
    version_path = code_version_path()
    if version_path.exists() and json.loads(version_path.read_text()) != before:
        raise RuntimeError("Recorded repository state differs")
    save_json(version_path, before)
    offline_step("validate_bundle", ["-m", "agent_reranking.cli", "validate-bundle", "--bundle", BUNDLE])
    validation = json.loads((ROOT / "validate_bundle.stdout.log").read_text())
    bundle_manifest = json.loads((REPO / BUNDLE / "manifest.json").read_text())
    validation["panel_sha256"] = bundle_manifest["panel_sha256"]
    expected = {"status": "valid", "num_users": 1000, "candidate_size": 20,
                "num_model_user_cases": 3000, "has_social_traits": True,
                "bundle_id": "d50a678b62a6539147c0a0314ab3fb044a97177c9033fda2e1dbd604e7345ed5",
                "panel_sha256": "76cdc352836afd33e23330affa5da3408756af08fc16bafbd5879a4d09425d3b"}
    for field, value in expected.items():
        if validation.get(field) != value:
            raise RuntimeError(f"Bundle mismatch: {field}")
    if set(validation["models"]) != set(MODELS):
        raise RuntimeError("Bundle model mismatch")
    counts = {}
    for filename, expected_count in (("candidates.jsonl", 3000), ("evaluation_labels.jsonl", 1000),
                                     ("train_interactions.jsonl", 1000), ("users.csv", 1001)):
        with (REPO / BUNDLE / filename).open() as source:
            counts[filename] = sum(1 for _ in source)
        if counts[filename] != expected_count:
            raise RuntimeError(f"Bundle line count mismatch: {filename}")
    with (REPO / PANEL).open(newline="") as source:
        users = [int(row["user_id"]) for row in csv.DictReader(source)]
    with (REPO / BUNDLE / "users.csv").open(newline="") as source:
        bundle_users = [int(row["user_id"]) for row in csv.DictReader(source)]
    if len(users) != 1000 or len(set(users)) != 1000 or set(users) != set(bundle_users):
        raise RuntimeError("Fixed panel mismatch; do not resample")
    if digest(REPO / PANEL) != expected["panel_sha256"]:
        raise RuntimeError("Fixed panel SHA-256 mismatch")
    offline_step("baselines_check", ["scripts/evaluate_bundle_baselines.py", "--bundle", BUNDLE,
                                    "--top-k", "10", "--output", str(ROOT / "baselines_check.json")])
    baselines = json.loads((ROOT / "baselines_check.json").read_text())
    for model, values in BASELINES.items():
        for metric, expected_value in zip(("recall@10", "ndcg@10"), values):
            if round(baselines["models"][model][metric], 7) != expected_value:
                raise RuntimeError(f"Baseline mismatch: {model} {metric}")
    save_json(ROOT / "bundle_verification.json", {"validation": validation, "line_counts": counts,
              "fixed_panel_sha256": digest(REPO / PANEL), "users": users, "baselines_verified": True})
    endpoint = api_key("OPENAI_ENDPOINT").rstrip("/")
    base_url = endpoint if endpoint.endswith("/v1") else endpoint + "/v1"
    if not api_key("OPENAI_API_KEY") or not urlsplit(base_url).hostname:
        raise RuntimeError("Proxy credentials or host missing (values hidden)")
    default = yaml.safe_load((REPO / "configs/default.yaml").read_text())
    config = dict(default, llm_base_url=base_url, temperature=0.0, concurrency=CONCURRENCY)
    config_path = ROOT / "config_4omini.yaml"
    if config_path.exists() and yaml.safe_load(config_path.read_text()) != config:
        previous_config = yaml.safe_load(config_path.read_text())
        if dict(previous_config, concurrency=CONCURRENCY) != config or any(latest_run(name) for name in CONDITIONS):
            raise RuntimeError("Existing n1000 config differs beyond the authorized concurrency change")
        previous_path = ROOT / "config_4omini_initial.yaml"
        if previous_path.exists():
            raise RuntimeError("Refusing to overwrite the initial configuration")
        config_path.rename(previous_path)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    config_path.chmod(0o600)
    if git_state() != before:
        raise RuntimeError("Repository state changed during validation")
    save_json(ROOT / "preflight.json", {**before, "prepared_at_utc": now(),
              "base_url_host": urlsplit(base_url).hostname, "llm_model": "gpt-4o-mini",
              "other_jobs": other_jobs(), "paid_calls_started": bool(total_cost()),
              "concurrency": CONCURRENCY})
    event("preflight", "verified", line_counts=counts, other_jobs=other_jobs())
    return base_url, users


def wait_for_proxy():
    started = False
    next_report = 0.0
    while True:
        jobs = other_jobs()
        if not jobs:
            if started:
                event("wait_for_shared_proxy", "end")
            return
        if not started:
            event("wait_for_shared_proxy", "start", other_jobs=jobs)
            started = True
        if time.monotonic() >= next_report:
            event("wait_for_shared_proxy", "waiting", other_jobs=jobs)
            next_report = time.monotonic() + REPORT_INTERVAL
        select.select([], [], [], 5)


def latest_run(condition):
    paths = sorted((ROOT / "n1000_align_rating" / condition / "runs").glob("*/config.yaml"))
    if len(paths) > 1:
        raise RuntimeError(f"Ambiguous run directories: {condition}; never merge incompatible runs")
    return paths[0].parent if paths else None


def write_progress(step, run_root=None):
    actions = json_rows(run_root / "actions.jsonl") if run_root else []
    failures = json_rows(run_root / "failures.jsonl") if run_root else []
    progress = {"utc": now(), "step": step, "completed_cases": len(actions),
                "failure_rows": len(failures), "step_recorded_cost_usd": step_cost(step),
                "total_recorded_cost_usd": total_cost(), "run_dir": str(run_root or "")}
    if step == "profiles":
        progress["completed_profiles"] = len(list((ROOT / "profiles/ours_all_n1000/checkpoints").glob("*.json")))
        progress["remaining_profiles"] = 1000 - progress["completed_profiles"]
    progress["conditions"] = {}
    for condition in CONDITIONS:
        path = latest_run(condition)
        progress["conditions"][condition] = {
            "completed_cases": len(json_rows(path / "actions.jsonl")) if path else 0,
            "failure_rows": len(json_rows(path / "failures.jsonl")) if path else 0,
            "recorded_cost_usd": step_cost(condition),
        }
    save_json(ROOT / "progress.json", progress)
    return progress


def paid_step(step, arguments, attempt, condition=None):
    if STOP_FILE.exists():
        raise RuntimeError("Safety stop is active; user approval is required before any further API calls")
    wait_for_proxy()
    if git_state() != json.loads(code_version_path().read_text()):
        raise RuntimeError("Repository sources changed before paid step")
    stdout_path = ROOT / f"{step}_attempt{attempt}.stdout.log"
    stderr_path = ROOT / f"{step}_attempt{attempt}.stderr.log"
    if stdout_path.exists() or stderr_path.exists():
        raise RuntimeError("Refusing to overwrite existing API execution logs")
    environment = dict(os.environ)
    environment.update(PYTHONPATH=str(ROOT / "monitoring"), N1000_STEP=step,
                       N1000_LEDGER=str(LEDGER), N1000_STOP_FILE=str(STOP_FILE))
    environment.pop("REASONING_EFFORT", None)
    event(step, "start", attempt=attempt)
    transcript_offsets = {}
    initial_root = latest_run(condition) if condition else None
    if initial_root is None and "--output-dir" in arguments:
        initial_root = Path(arguments[arguments.index("--output-dir") + 1])
    if initial_root and (initial_root / "transcripts.jsonl").exists():
        initial_path = initial_root / "transcripts.jsonl"
        transcript_offsets[str(initial_path)] = initial_path.stat().st_size
    def new_transport_errors(path):
        if path is None or not path.is_file():
            return ""
        messages = []
        with path.open() as source:
            source.seek(transcript_offsets.get(str(path), 0))
            while True:
                position = source.tell()
                line = source.readline()
                if not line or not line.endswith("\n"):
                    source.seek(position)
                    break
                row = json.loads(line)
                if row.get("kind") == "retry_exhausted" and row.get("retryable"):
                    messages.append("transport_retries_exhausted")
            transcript_offsets[str(path)] = source.tell()
        return "\n".join(messages)
    with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
        child = subprocess.Popen(["caffeinate", "-i", "nohup", str(PYTHON), *arguments],
                                 cwd=REPO, env=environment, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        save_json(ROOT / "active_job.json", {"step": step, "pid": child.pid,
                  "started_at_utc": now(), "attempt": attempt})
        next_report = time.monotonic()
        try:
            while child.poll() is None:
                run_root = latest_run(condition) if condition else None
                transcript_root = run_root
                if transcript_root is None:
                    for index, argument in enumerate(arguments):
                        if argument == "--output-dir":
                            transcript_root = Path(arguments[index + 1])
                transcript_errors = new_transport_errors(transcript_root / "transcripts.jsonl" if transcript_root else None)
                if transcript_errors:
                    if not STOP_FILE.exists():
                        save_json(STOP_FILE, {"utc": now(), "step": step,
                                  "reason": "transport_retries_exhausted"})
                if total_cost() > 35.0 and not STOP_FILE.exists():
                    save_json(STOP_FILE, {"utc": now(), "step": step,
                              "reason": "total_recorded_cost_exceeded_35_usd"})
                if STOP_FILE.exists():
                    os.killpg(child.pid, signal.SIGTERM)
                    child.wait()
                    break
                progress = write_progress(step, run_root)
                if time.monotonic() >= next_report:
                    event(step, "progress", **{key: value for key, value in progress.items()
                          if key not in ("utc", "step")})
                    next_report = time.monotonic() + REPORT_INTERVAL
                try:
                    child.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait()
            raise
        finally:
            save_json(ROOT / "active_job.json", {"step": step, "pid": child.pid,
                      "ended_at_utc": now(), "exit_code": child.returncode})
            event(step, "end", attempt=attempt, exit_code=child.returncode,
                  recorded_cost_usd=step_cost(step), total_recorded_cost_usd=total_cost())
    if STOP_FILE.exists():
        raise RuntimeError("Safety stop: retained all logs and artifacts; ask the user before continuing")
    installed = [row for row in json_rows(LEDGER)
                 if row.get("step") == step and row.get("kind") == "monitor_installed"]
    if not installed:
        raise RuntimeError("Runtime monitor did not initialize; stopping")
    return child.returncode


def transcript_artifacts(path):
    transcript = path / "transcripts.jsonl"
    prompts = sorted((path / "prompts").glob("*.txt"))
    if not transcript.is_file() or not prompts:
        raise RuntimeError(f"Missing transcripts or saved prompts: {path.name}")
    for prompt in prompts:
        if digest(prompt) != prompt.stem:
            raise RuntimeError("Saved prompt SHA-256 mismatch")
    return [transcript, *prompts]


def verify_transcripts(path, actions=None):
    artifacts = transcript_artifacts(path)
    exchanges, validations = {}, {}
    records = json_rows(path / "transcripts.jsonl")
    for row in records:
        if row.get("kind") == "exchange":
            exchanges.setdefault(row["call_id"], []).append(row)
        elif row.get("kind") == "validation":
            validations.setdefault(row["call_id"], []).append(row)
    for call in json_rows(path / "calls.jsonl"):
        call_id = call["call_id"]
        if len(exchanges.get(call_id, [])) != 1 or not exchanges[call_id][0].get("raw_response"):
            raise RuntimeError("Recorded call lacks exactly one non-empty exchange")
        if len(validations.get(call_id, [])) != 1:
            raise RuntimeError("Recorded call lacks exactly one validation")
    coverage = {}
    for values in exchanges.values():
        for row in values:
            if row.get("raw_response") and not row.get("error"):
                key = (row.get("model"), int(row["user_id"]))
                coverage.setdefault(key, set()).add(row["response_name"])
    if actions is not None:
        for action in actions:
            names = coverage.get((action["model"], int(action["user_id"])), set())
            if "alignment_click_selection" not in names:
                raise RuntimeError("Completed case lacks click exchange")
            if action["actions"]["clicked_item_ids"] and "rating_conversion_selection" not in names:
                raise RuntimeError("Completed clicked case lacks conversion exchange")
    summary = {
        "exchanges": sum(len(values) for values in exchanges.values()),
        "invalid_validations": sum(row.get("status") != "valid" for row in records if row.get("kind") == "validation"),
        "http_transport_errors": sum(bool(row.get("error")) for row in records if row.get("kind") == "exchange"),
        "at_most_one_sentence_errors": sum("at most one sentence" in str(row.get("error", "")).lower() for row in records if row.get("kind") == "validation"),
        "message_extras_keys": sorted({key for row in records for key in row.get("message_extras", {})}),
        "response_models": sorted({row["response_model"] for row in records if row.get("response_model")}),
        "transcript_bytes": (path / "transcripts.jsonl").stat().st_size,
    }
    return summary, {str(file): digest(file) for file in artifacts}


def verify_profiles(path, users):
    profiles = json_rows(path / "profiles.jsonl")
    manifests = json_rows(path / "profile_manifests.jsonl")
    for name, rows in (("profiles.jsonl", profiles), ("profile_manifests.jsonl", manifests)):
        if len(rows) != 1000 or {int(row["user_id"]) for row in rows} != set(users):
            raise RuntimeError(f"Expected exactly 1000 fixed-panel records: {name}")
        with (path / name).open() as source:
            if sum(1 for _ in source) != 1000:
                raise RuntimeError(f"Expected exactly 1000 physical lines: {name}")
    required = {"user_id", "raw_user_id", "interaction_history", "unique_tastes", "social_traits", "demographics"}
    if any(not required <= row.keys() or len(row["interaction_history"]) != 10 for row in profiles):
        raise RuntimeError("Profile fields or 10-movie history mismatch")
    manifest = json.loads((path / "run_manifest.json").read_text())
    if manifest["num_users"] != 1000 or manifest["seed"] != 42 or manifest["concurrency"] != CONCURRENCY:
        raise RuntimeError("Profile manifest settings mismatch")
    expected_components = {"history", "unique_tastes", "social_traits", "demographics"}
    if set(manifest["components"]) != expected_components or manifest["method"] != "ours":
        raise RuntimeError("Profile method or components mismatch")
    summary, transcript_hashes = verify_transcripts(path)
    exchange_users = {int(row["user_id"]) for row in json_rows(path / "transcripts.jsonl")
                      if row.get("kind") == "exchange" and row.get("raw_response")}
    if exchange_users != set(users):
        raise RuntimeError("Profile exchanges do not cover all 1000 users")
    save_json(ROOT / "profile_transcript_checks.json", summary)
    return {**{str(path / name): digest(path / name) for name in PROFILE_FILES}, **transcript_hashes}


def get_profiles(base_url, users):
    selection = ROOT / "verified_profiles.json"
    if selection.exists():
        stored = json.loads(selection.read_text())
        path = Path(stored["directory"])
        if verify_profiles(path, users) != stored["sha256"]:
            raise RuntimeError("Verified profiles changed")
        return path
    attempt = len(list(ROOT.glob("profiles_attempt*.stdout.log"))) + 1
    while True:
        path = ROOT / "profiles" / "ours_all_n1000"
        path.mkdir(parents=True, exist_ok=True)
        arguments = ["-m", "agent_reranking.cli", "generate-profiles", "--bundle", BUNDLE,
                     "--users-file", PANEL, "--method", "ours", "--model", "gpt-4o-mini",
                     "--base-url", base_url, "--profile-components", "all", "--history-size", "10",
                     "--seed", "42", "--concurrency", str(CONCURRENCY), "--requests-per-minute", str(REQUESTS_PER_MINUTE),
                     "--tokens-per-minute", str(TOKENS_PER_MINUTE), "--max-cost-usd", "25", "--max-retries", "3",
                     "--output-dir", str(path), "--resume"]
        return_code = paid_step("profiles", arguments, attempt)
        if return_code == 0:
            hashes = verify_profiles(path, users)
            save_json(selection, {"directory": str(path), "sha256": hashes, "verified_at_utc": now(),
                      "recorded_cost_usd": step_cost("profiles")})
            event("profiles", "verified", num_profiles=1000, directory=str(path), sha256=hashes)
            return path
        event("profiles", "partial_checkpoint_retained", attempt=attempt, directory=str(path))
        raise RuntimeError("Profile attempt failed; checkpoints retained for explicit resume")


def run_arguments(condition, profiles):
    return ["-m", "agent_reranking.cli", "run", "--config", str(ROOT / "config_4omini.yaml"),
            "--bundle", BUNDLE, "--users-file", PANEL, "--profiles", str(profiles / "profiles.jsonl"),
            "--llm-model", "gpt-4o-mini", "--prompt-version", "behavior-align-rating-social-traits",
            "--profile-components", CONDITIONS[condition], "--profile-protocol", "separated",
            "--concurrency", str(CONCURRENCY), "--requests-per-minute", str(REQUESTS_PER_MINUTE), "--tokens-per-minute", str(TOKENS_PER_MINUTE),
            "--max-cost-usd", "25", "--output-root", str(ROOT / "n1000_align_rating" / condition / "runs")]


def missing_cases(root, users):
    expected = {(model, user) for model in MODELS for user in users}
    completed = {(row["model"], int(row["user_id"])) for row in json_rows(root / "actions.jsonl")}
    errors = {(row["model"], int(row["user_id"])): row.get("error", "")
              for row in json_rows(root / "failures.jsonl")}
    return [{"model": model, "user_id": user,
             "last_error": errors.get((model, user), "No completed action was recorded")}
            for model, user in sorted(expected - completed)]


def verify_run(condition, root, users):
    if any(not (root / name).is_file() for name in ARTIFACTS):
        raise RuntimeError(f"Missing required run artifacts: {condition}")
    manifest = json.loads((root / "run_manifest.json").read_text())
    actions = json_rows(root / "actions.jsonl")
    expected = {(model, user) for model in MODELS for user in users}
    pairs = {(row["model"], int(row["user_id"])) for row in actions}
    missing = missing_cases(root, users)
    documented_path = ROOT / f"unrecovered_cases_{condition}.json"
    documented = json.loads(documented_path.read_text()) if documented_path.exists() else []
    expected_status = "partial" if missing else "complete"
    if (manifest["status"] != expected_status or manifest["completed_cases"] != len(pairs)
            or len(actions) != len(pairs) or not pairs <= expected or missing != documented):
        raise RuntimeError(f"Run coverage or documented missing cases mismatch: {condition}")
    failures = json_rows(root / "failures.jsonl")
    documented_pairs = {(row["model"], int(row["user_id"])) for row in documented}
    if any((row["model"], int(row["user_id"])) not in pairs | documented_pairs for row in failures):
        raise RuntimeError(f"Unrecovered historical failure: {condition}")
    rankings = json_rows(root / "rankings.jsonl")
    if len(rankings) != len(pairs) or {(row["model"], int(row["user_id"])) for row in rankings} != pairs:
        raise RuntimeError(f"Ranking coverage mismatch: {condition}")
    config = yaml.safe_load((root / "config.yaml").read_text())
    checks = {"llm_model": "gpt-4o-mini", "temperature": 0.0, "profile_protocol": "separated",
              "prompt_version": "behavior-align-rating-social-traits", "concurrency": CONCURRENCY,
              "requests_per_minute": REQUESTS_PER_MINUTE, "tokens_per_minute": TOKENS_PER_MINUTE, "max_cost_usd": 25,
              "num_users": 1000, "seed": 42, "history_size": 10, "candidate_size": 20,
              "top_k": 10, "num_shards": 1, "shard_index": 0}
    for field, value in checks.items():
        if config[field] != value:
            raise RuntimeError(f"Run setting mismatch: {condition} {field}")
    base_config = yaml.safe_load((ROOT / "config_4omini.yaml").read_text())
    if config["llm_base_url"] != base_config["llm_base_url"] or set(config["models"]) != set(MODELS):
        raise RuntimeError(f"Proxy or backbone setting mismatch: {condition}")
    components = {"history", "unique_tastes", "social_traits", "demographics"} if CONDITIONS[condition] == "all" else set(CONDITIONS[condition].split(","))
    if set(config["profile_components"]) != components or set(config["selected_user_ids"]) != set(users):
        raise RuntimeError(f"Run components or user panel mismatch: {condition}")
    metric_rows = list(csv.DictReader((root / "per_user_metrics.csv").open(newline="")))
    stages = {"sampled_baseline", "click_only", "converted_then_original", "three_tier"}
    for model in MODELS:
        for stage in stages:
            selected = [row for row in metric_rows if row["model"] == model and row["stage"] == stage]
            completed_users = {user for case_model, user in pairs if case_model == model}
            if len(selected) != len(completed_users) or {int(row["user_id"]) for row in selected} != completed_users:
                raise RuntimeError(f"Per-user metrics coverage mismatch: {condition} {model} {stage}")
    if abs(sum(row.get("estimated_cost_usd", 0) for row in json_rows(root / "calls.jsonl")) - manifest["estimated_cost_usd"]) > 1e-9:
        raise RuntimeError(f"Manifest recorded cost mismatch: {condition}")
    transcript_summary, _ = verify_transcripts(root, actions)
    save_json(ROOT / f"{condition}_transcript_checks.json", transcript_summary)
    return manifest


def migrate_rate_limits(condition, root):
    path = root / "config.yaml"
    stored = yaml.safe_load(path.read_text())
    updated = dict(stored, concurrency=CONCURRENCY, requests_per_minute=REQUESTS_PER_MINUTE,
                   tokens_per_minute=TOKENS_PER_MINUTE)
    if stored != updated:
        archive = root / "config_pre_retryfix.yaml"
        if archive.exists():
            raise RuntimeError("Refusing to overwrite original rate configuration")
        archive.write_bytes(path.read_bytes())
        archive.chmod(0o600)
        path.write_text(yaml.safe_dump(updated, sort_keys=True))
        path.chmod(0o600)
        event(condition, "rate_limits_migrated", concurrency=CONCURRENCY,
              requests_per_minute=REQUESTS_PER_MINUTE, tokens_per_minute=TOKENS_PER_MINUTE,
              original_configuration=archive.name)


def run_condition(condition, profiles, users):
    arguments = run_arguments(condition, profiles)
    attempt = len(list(ROOT.glob(f"{condition}_attempt*.stdout.log"))) + 1
    initial_root = latest_run(condition)
    original_missing = missing_cases(initial_root, users) if initial_root else []
    transcript_start = 0
    previous_validation_errors = set()
    if condition == "full" and initial_root:
        transcript_path = initial_root / "transcripts.jsonl"
        transcript_start = transcript_path.stat().st_size
        previous_validation_errors = {re.sub(r"\[\d+\]", "[item]", row.get("error", ""))
            for row in json_rows(transcript_path) if row.get("kind") == "validation" and row.get("status") == "invalid"}
    if initial_root:
        migrate_rate_limits(condition, initial_root)
    successful_passes = sum(row.get("step") == condition and row.get("state") == "end"
                            and row.get("exit_code") == 0 for row in json_rows(ROOT / "execution_events.jsonl"))
    if initial_root and successful_passes == 0:
        successful_passes = 1
    starting_failures = len(json_rows(initial_root / "failures.jsonl")) if initial_root else 0
    while True:
        root = latest_run(condition)
        if root and (root / "run_manifest.json").exists():
            manifest = json.loads((root / "run_manifest.json").read_text())
            missing = missing_cases(root, users)
            documented_path = ROOT / f"unrecovered_cases_{condition}.json"
            if not missing or successful_passes >= 1 + MAX_RESUME_PASSES:
                save_json(documented_path, missing)
                if missing:
                                        event(condition, "resume_limit_reached", missing_cases=missing,
                                                    max_resume_passes=MAX_RESUME_PASSES)
                verified = verify_run(condition, root, users)
                event(condition, "verified", run_dir=str(root), completed_cases=verified["completed_cases"],
                                            missing_cases=len(missing),
                      recovered_failure_rows=verified["failure_count"], recorded_cost_usd=step_cost(condition))
                if condition == "full" and original_missing:
                    pending = {(row["model"], row["user_id"]) for row in missing}
                    recovered = sum((row["model"], row["user_id"]) not in pending for row in original_missing)
                    report = {"original_failed_cases": len(original_missing), "recovered": recovered,
                              "still_missing": len(missing), "new_failure_rows":
                              len(json_rows(root / "failures.jsonl")) - starting_failures}
                    with (root / "transcripts.jsonl").open() as source:
                        source.seek(transcript_start)
                        appended = [json.loads(line) for line in source if line.strip()]
                    invalid = [row for row in appended if row.get("kind") == "validation" and row.get("status") == "invalid"]
                    errors = sorted({re.sub(r"\[\d+\]", "[item]", row.get("error", "")) for row in invalid})
                    report.update(new_invalid_validations=len(invalid), validation_error_types=errors,
                                  novel_validation_error_types=sorted(set(errors) - previous_validation_errors))
                    save_json(ROOT / "full_recovery_report.json", report)
                    event("full_recovery", "reported", **report)
                return root
        current = arguments + (["--resume", str(root.resolve())] if root else [])
        return_code = paid_step(condition, current, attempt, condition)
        if return_code:
            raise RuntimeError(f"Unexpected runner exit for {condition}: {return_code}; artifacts retained")
        successful_passes += 1
        attempt += 1


def write_run_info(profile_root=None, runs=None, final_state=None):
    runs = runs or {}
    before = json.loads(code_version_path().read_text())
    events = json_rows(ROOT / "execution_events.jsonl")
    preflight = json.loads((ROOT / "preflight.json").read_text()) if (ROOT / "preflight.json").exists() else {}
    lines = ["# Run Information", "", f"Commit SHA: {before['commit']}",
             f"Branch: {before['branch']}",
             f"Git status before: `{before['git_status']}`",
             f"Git status after: `{(final_state or {}).get('git_status', 'execution in progress')}`",
             "LLM alias: gpt-4o-mini", f"Base URL host only: {preflight.get('base_url_host', 'not recorded')}",
             "Temperature: 0.0; seed: 42; protocol: separated.",
             f"Current concurrency: {CONCURRENCY}; requests/minute: {REQUESTS_PER_MINUTE}; tokens/minute: {TOKENS_PER_MINUTE}.",
             "Initial interrupted profile attempt used concurrency 32; user authorized 16 for all subsequent steps.",
             f"Execution first timestamp (UTC): {events[0]['utc'] if events else now()}",
             f"Latest timestamp (UTC): {events[-1]['utc'] if events else now()}",
             f"Shared profiles: {profile_root or 'not yet verified'}", "",
             "| Step | All-request recorded cost (USD) | Run calls artifact cost (USD) |", "|---|---:|---:|"]
    for step in ("profiles", *CONDITIONS):
        artifact_cost = "N/A"
        if step in runs:
            artifact_cost = f"{json.loads((runs[step] / 'run_manifest.json').read_text())['estimated_cost_usd']:.6f}"
        lines.append(f"| {step} | {step_cost(step):.6f} | {artifact_cost} |")
    lines.extend(["", f"Total all-request recorded cost: ${total_cost():.6f}.",
                  "The request ledger includes paid responses from failed validation and unsuccessful cases,",
                  "which can be omitted from calls.jsonl by the repository runner. Costs use the unchanged",
                  "repository rates ($0.15/M input and $0.60/M output tokens), not proxy invoices.",
                  "Actual proxy billing must be checked on the provider dashboard; it has not been independently verified.",
                  "Code is ec7fac9 plus the transcript/validator commit, not the handoff commit itself.",
                  "No shards were created or merged. User-authorized checkpoint/retry changes are uncommitted and fingerprinted in code_version_resume_before.json.",
                  "Unit tests use conda datasets (user-approved); see tests_resume_retry.log. Paid steps use the unchanged project .venv.",
                  "Start/end timestamps for every attempt are recorded in timeline.md."])
    lines.extend(["", "## Documented Missing Cases", "",
                  "At most three completed resume passes after the first pass; interrupted passes do not consume the allowance."])
    for condition in CONDITIONS:
        path = ROOT / f"unrecovered_cases_{condition}.json"
        if path.exists():
            missing = json.loads(path.read_text())
            lines.append(f"- {condition}: {len(missing)} missing cases; see {path.name}.")
            lines.extend(f"  - {row['model']} user {row['user_id']}: {row['last_error']}" for row in missing)
    lines.extend(["", "## Transcript verification", "",
                  "| Step | Exchanges | Invalid validations | HTTP/transport errors | At most one sentence errors | Extras keys | Transcript bytes | Response models |",
                  "|---|---:|---:|---:|---:|---|---:|---|"])
    for step in ("profile", *CONDITIONS):
        checks_path = ROOT / f"{step}_transcript_checks.json"
        if checks_path.exists():
            checks = json.loads(checks_path.read_text())
            lines.append(f"| {step} | {checks['exchanges']} | {checks['invalid_validations']} | {checks['http_transport_errors']} | {checks['at_most_one_sentence_errors']} | {', '.join(checks['message_extras_keys']) or 'none'} | {checks['transcript_bytes']} | {', '.join(checks['response_models'])} |")
    (ROOT / "run_info.md").write_text("\n".join(lines) + "\n")


def finalize_source_commit():
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip() != "jinyi/transcripts-validator-fix":
        raise RuntimeError("Refusing to commit on an unexpected branch")
    files = ["agent_reranking/agent.py", "agent_reranking/client.py", "agent_reranking/profiles.py",
             "agent_reranking/cli.py", "README.md", "tests/test_resume_retry.py"]
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=REPO, text=True).splitlines()
    if set(staged) - set(files):
        raise RuntimeError("Unrelated staged files exist; source commit postponed")
    subprocess.run(["git", "add", "--", *files], cwd=REPO, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode:
        subprocess.run(["git", "-c", "user.name=Jinyi Ye", "-c", "user.email=jinyiy@usc.edu", "commit",
                        "-m", "Add profile resume and API retries; fix empty-evidence retry prompts"], cwd=REPO, check=True)
    committed = git_state()
    save_json(ROOT / "code_version_post_commit.json", committed)
    event("source_commit", "complete", commit=committed["commit"], pushed=False)
    recovery = json.loads((ROOT / "full_recovery_report.json").read_text())
    counts = {condition: len(json.loads((ROOT / f"unrecovered_cases_{condition}.json").read_text()))
              for condition in CONDITIONS}
    readme = ROOT.parent / "README.md"
    text = readme.read_text()
    heading = "## Notes / things to be aware of"
    before, marker, remainder = text.partition(heading)
    if not marker:
        raise RuntimeError("Result README Notes heading is missing")
    notes, separator, after_notes = remainder.partition("\n## ")
    notes = re.sub(r"\n- \*\*21 cases are missing\*\*.*?(?=\n- \*\*|\Z)", "", notes, flags=re.S)
    notes = re.sub(r"\n- \*\*Code differs from the handoff commit\.\*\*.*?(?=\n- \*\*|\Z)", "", notes, flags=re.S)
    current_notes = (
        f"\n\n- **最终恢复结果：**原 full 的 21 个失败案例恢复 {recovery['recovered']} 个；"
        f"新增失败记录 {recovery['new_failure_rows']} 条。\n"
        "- **重试提示修复：**仅在验证错误含 must be a nonempty string 时补充非空 evidence 指令，首次请求不变。\n"
        f"- **最终缺失案例：**{'; '.join(f'{condition}={count}' for condition, count in counts.items())}。"
        "每个条件最多三次完成的恢复轮次；缺失清单见 n1000_v2/unrecovered_cases_*.json。\n"
        f"- **源码提交：**{committed['commit']}，分支 jinyi/transcripts-validator-fix；只在本地提交，未 push。\n"
        "- **指标版本：**本页上方 full 表格保留了首次 2,979 案例分析快照；最终四条件指标见 n1000_v2/summary_table.md 与 analysis.md。\n")
    from agent_reranking.io import atomic_text
    atomic_text(readme, before + marker + current_notes + notes + separator + after_notes)
    with (ROOT / "run_info.md").open("a") as handle:
        handle.write(f"\nSource changes committed after verification: {committed['commit']} (local only; not pushed).\n")
    save_json(ROOT / "finalization.json", {"source_commit": committed["commit"], "pushed": False,
              "full_recovery": recovery, "missing_cases": counts, "completed_at_utc": now()})


def write_final_checksums(profiles, runs):
    hashes = verify_profiles(profiles, json.loads((ROOT / "bundle_verification.json").read_text())["users"])
    for path in runs.values():
        hashes.update({str(path / name): digest(path / name) for name in ARTIFACTS})
        hashes.update({str(file): digest(file) for file in transcript_artifacts(path)})
    report_files = ["run_info.md", "summary_table.md", "analysis.md", "bootstrap_results.json",
                    "full_recovery_report.json", "verified_runs.json", "finalization.json",
                    "code_version_after.json", "code_version_post_commit.json"]
    report_files.extend(f"unrecovered_cases_{condition}.json" for condition in CONDITIONS)
    for name in report_files:
        hashes[str(ROOT / name)] = digest(ROOT / name)
    hashes[str(ROOT.parent / "README.md")] = digest(ROOT.parent / "README.md")
    (ROOT / "SHA256SUMS.txt").write_text("".join(
        f"{checksum}  {os.path.relpath(path, ROOT)}\n" for path, checksum in sorted(hashes.items())))


def execute_all(base_url, users, through_full=False):
    if STOP_FILE.exists():
        raise RuntimeError("Safety stop is active; user approval required")
    wait_for_proxy()
    profiles = get_profiles(base_url, users)
    runs = {}
    for condition in CONDITIONS:
        runs[condition] = run_condition(condition, profiles, users)
        write_run_info(profiles, runs)
        if through_full:
            return
    verify_profiles(profiles, users)
    for condition, path in runs.items():
        verify_run(condition, path, users)
    save_json(ROOT / "verified_runs.json", {"profiles": str(profiles), "runs": {key: str(path) for key, path in runs.items()},
              "verified_at_utc": now(), "total_recorded_cost_usd": total_cost(),
              "missing_cases": {condition: json.loads((ROOT / f"unrecovered_cases_{condition}.json").read_text())
                                for condition in CONDITIONS}})
    event("analysis", "start")
    from build_reports import build_reports
    build_reports(ROOT, profiles, runs, users)
    event("analysis", "end", recorded_cost_usd=0.0)
    hashes = verify_profiles(profiles, users)
    for path in runs.values():
        hashes.update({str(path / name): digest(path / name) for name in ARTIFACTS})
        hashes.update({str(file): digest(file) for file in transcript_artifacts(path)})
    (ROOT / "SHA256SUMS.txt").write_text("".join(f"{checksum}  {Path(path).relative_to(ROOT)}\n" for path, checksum in sorted(hashes.items())))
    after = git_state()
    save_json(ROOT / "code_version_after.json", after)
    if after != json.loads(code_version_path().read_text()):
        raise RuntimeError("Repository commit or status changed")
        completed_count = sum(len(json_rows(path / "actions.jsonl")) for path in runs.values())
        event("experiment", "complete", completed_cases=completed_count,
            missing_cases=12000 - completed_count, total_recorded_cost_usd=total_cost())
    write_run_info(profiles, runs, after)
    finalize_source_commit()
    write_final_checksums(profiles, runs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--through-full", action="store_true",
                        help="Recover and verify full first, then exit without finalizing the other conditions")
    parser.add_argument("--record-code-update", action="store_true",
                        help="Offline only: fingerprint the user-authorized checkpoint/retry changes")
    args = parser.parse_args()
    os.environ["AGENT_RERANKING_ENV"] = str(ROOT.parent.parent / "gpt5.env")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if not (ROOT / "timeline.md").exists():
        (ROOT / "timeline.md").write_text("# Execution Timeline (UTC)\n\n| Timestamp | Step | State | Details |\n|---|---|---|---|\n")
    with (ROOT / "experiment.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.record_code_update:
            if not args.prepare_only or not STOP_FILE.exists() or other_jobs():
                raise RuntimeError("Code update recording requires paused, offline-only execution with no competing jobs")
            snapshot = ROOT / "code_version_resume_before.json"
            current = git_state()
            if snapshot.exists() and json.loads(snapshot.read_text()) != current:
                raise RuntimeError("Approved source snapshot already exists and differs")
            save_json(snapshot, current)
            event("authorized_resume_changes", "recorded", concurrency=CONCURRENCY,
                  snapshot=snapshot.name, note="Checkpoint recovery and bounded retries; original snapshot retained")
        base_url, users = prepare()
        if args.prepare_only:
            return
        try:
            execute_all(base_url, users, through_full=args.through_full)
        finally:
            after = git_state()
            if not (ROOT / "code_version_post_commit.json").exists():
                save_json(ROOT / "code_version_after.json", after)
            if not (ROOT / "verified_runs.json").exists():
                write_run_info(final_state=after)


if __name__ == "__main__":
    main()