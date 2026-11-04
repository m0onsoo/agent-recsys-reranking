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
            next_report = time.monotonic() + 900
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
                    next_report = time.monotonic() + 900
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
                     "--seed", "42", "--concurrency", str(CONCURRENCY), "--requests-per-minute", "500",
                     "--tokens-per-minute", "3000000", "--max-cost-usd", "25", "--max-retries", "3",
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
            "--concurrency", str(CONCURRENCY), "--requests-per-minute", "500", "--tokens-per-minute", "3000000",
            "--max-cost-usd", "25", "--output-root", str(ROOT / "n1000_align_rating" / condition / "runs")]


def verify_run(condition, root, users):
    if any(not (root / name).is_file() for name in ARTIFACTS):
        raise RuntimeError(f"Missing required run artifacts: {condition}")
    manifest = json.loads((root / "run_manifest.json").read_text())
    actions = json_rows(root / "actions.jsonl")
    expected = {(model, user) for model in MODELS for user in users}
    pairs = {(row["model"], int(row["user_id"])) for row in actions}
    if manifest["status"] != "complete" or manifest["completed_cases"] != 3000 or len(actions) != 3000 or pairs != expected:
        raise RuntimeError(f"Run is not complete with 3000 unique cases: {condition}")
    failures = json_rows(root / "failures.jsonl")
    if any((row["model"], int(row["user_id"])) not in pairs for row in failures):
        raise RuntimeError(f"Unrecovered historical failure: {condition}")
    rankings = json_rows(root / "rankings.jsonl")
    if len(rankings) != 3000 or {(row["model"], int(row["user_id"])) for row in rankings} != expected:
        raise RuntimeError(f"Ranking coverage mismatch: {condition}")
    config = yaml.safe_load((root / "config.yaml").read_text())
    checks = {"llm_model": "gpt-4o-mini", "temperature": 0.0, "profile_protocol": "separated",
              "prompt_version": "behavior-align-rating-social-traits", "concurrency": CONCURRENCY,
              "requests_per_minute": 500, "tokens_per_minute": 3000000, "max_cost_usd": 25,
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
            if len(selected) != 1000 or {int(row["user_id"]) for row in selected} != set(users):
                raise RuntimeError(f"Per-user metrics coverage mismatch: {condition} {model} {stage}")
    if abs(sum(row.get("estimated_cost_usd", 0) for row in json_rows(root / "calls.jsonl")) - manifest["estimated_cost_usd"]) > 1e-9:
        raise RuntimeError(f"Manifest recorded cost mismatch: {condition}")
    transcript_summary, _ = verify_transcripts(root, actions)
    save_json(ROOT / f"{condition}_transcript_checks.json", transcript_summary)
    return manifest


def run_condition(condition, profiles, users):
    arguments = run_arguments(condition, profiles)
    attempt = len(list(ROOT.glob(f"{condition}_attempt*.stdout.log"))) + 1
    while True:
        root = latest_run(condition)
        if root and (root / "run_manifest.json").exists():
            manifest = json.loads((root / "run_manifest.json").read_text())
            if manifest["status"] == "complete":
                verified = verify_run(condition, root, users)
                event(condition, "verified", run_dir=str(root), completed_cases=3000,
                      recovered_failure_rows=verified["failure_count"], recorded_cost_usd=step_cost(condition))
                return root
        current = arguments + (["--resume", str(root.resolve())] if root else [])
        paid_step(condition, current, attempt, condition)
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
             f"Current concurrency: {CONCURRENCY}; requests/minute: 500; tokens/minute: 3000000.",
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
    lines.extend(["", "## Transcript verification", "",
                  "| Step | Exchanges | Invalid validations | HTTP/transport errors | At most one sentence errors | Extras keys | Transcript bytes | Response models |",
                  "|---|---:|---:|---:|---:|---|---:|---|"])
    for step in ("profile", *CONDITIONS):
        checks_path = ROOT / f"{step}_transcript_checks.json"
        if checks_path.exists():
            checks = json.loads(checks_path.read_text())
            lines.append(f"| {step} | {checks['exchanges']} | {checks['invalid_validations']} | {checks['http_transport_errors']} | {checks['at_most_one_sentence_errors']} | {', '.join(checks['message_extras_keys']) or 'none'} | {checks['transcript_bytes']} | {', '.join(checks['response_models'])} |")
    (ROOT / "run_info.md").write_text("\n".join(lines) + "\n")


def execute_all(base_url, users):
    if STOP_FILE.exists():
        raise RuntimeError("Safety stop is active; user approval required")
    wait_for_proxy()
    profiles = get_profiles(base_url, users)
    runs = {}
    for condition in CONDITIONS:
        runs[condition] = run_condition(condition, profiles, users)
        write_run_info(profiles, runs)
    verify_profiles(profiles, users)
    for condition, path in runs.items():
        verify_run(condition, path, users)
    save_json(ROOT / "verified_runs.json", {"profiles": str(profiles), "runs": {key: str(path) for key, path in runs.items()},
              "verified_at_utc": now(), "total_recorded_cost_usd": total_cost()})
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
    event("experiment", "complete", completed_cases=12000, total_recorded_cost_usd=total_cost())
    write_run_info(profiles, runs, after)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
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
            execute_all(base_url, users)
        finally:
            after = git_state()
            save_json(ROOT / "code_version_after.json", after)
            if not (ROOT / "verified_runs.json").exists():
                write_run_info(final_state=after)


if __name__ == "__main__":
    main()