import argparse
import csv
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from agent_reranking.client import api_key


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
REPO = WORKSPACE / "agent-recsys-reranking"
PANEL = ROOT.parent / "panels/users_50_from_1000_seed42.csv"
WRAPPER = ROOT.parent / "run_with_reasoning.py"
BUNDLE = "data/derived/ml1m_ro_n1000_seed42"
PANEL_HASH = "eb26776de223ef302470ce2e26350029923b266de76bde38c62ad3e871728116"
MODELS = ("MF", "LightGCN", "MultiVAE")
EXPECTED_STATUS = "?? agent_reranking_bench.egg-info/"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def event(stage, state, **details):
    with (ROOT / "execution_events.jsonl").open("a") as handle:
        handle.write(json.dumps({"stage": stage, "state": state, "utc": now(), **details}) + "\n")


def git_state():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    if status != EXPECTED_STATUS:
        raise RuntimeError("Repository status does not match the required unchanged state: " + status)
    return commit, status


def execute(stage, command, log_name, reasoning=None):
    environment = dict(os.environ)
    environment.pop("REASONING_EFFORT", None)
    if reasoning:
        environment["REASONING_EFFORT"] = reasoning
    print(f"{stage}: started {now()}", flush=True)
    event(stage, "start")
    result = subprocess.run(command, cwd=REPO, env=environment, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.replace(api_key("OPENAI_API_KEY"), "[REDACTED]")
    with (ROOT / log_name).open("a") as handle:
        handle.write(f"\n[{stage}: {now()}]\n" + output)
    event(stage, "end", exit_code=result.returncode)
    if result.returncode:
        print(output[-4000:], flush=True)
        raise RuntimeError(f"{stage} failed; see {log_name}")
    print(f"{stage}: finished {now()}", flush=True)
    return output


def panel_users():
    if digest(PANEL) != PANEL_HASH:
        raise RuntimeError("The fixed panel SHA-256 differs; do not resample")
    with PANEL.open(newline="") as handle:
        users = [int(row["user_id"]) for row in csv.DictReader(handle)]
    if len(users) != 50 or len(set(users)) != 50:
        raise RuntimeError("Expected 50 distinct panel users")
    with (REPO / "data/panels/users_1000_seed42.csv").open(newline="") as handle:
        parent = {int(row["user_id"]) for row in csv.DictReader(handle)}
    with (REPO / "data/panels/users_30_from_1000_seed42.csv").open(newline="") as handle:
        pilot = {int(row["user_id"]) for row in csv.DictReader(handle)}
    if not pilot <= set(users) <= parent:
        raise RuntimeError("The fixed 50-user panel must include the pilot and belong to the parent panel")
    return users


def prepare():
    users = panel_users()
    commit, status = git_state()
    version = commit + "\n" + status + "\n"
    version_path = ROOT / "code_version.txt"
    if version_path.exists() and version_path.read_text() != version:
        raise RuntimeError("Recorded code version changed")
    version_path.write_text(version)
    base_url = api_key("OPENAI_ENDPOINT").rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    valid = json.loads(execute("validate_bundle", [sys.executable, "-m", "agent_reranking.cli",
                       "validate-bundle", "--bundle", BUNDLE], "bundle_validation.log"))
    if valid["status"] != "valid" or valid["num_users"] != 1000:
        raise RuntimeError("Bundle validation failed")
    save_json(ROOT / "bundle_validation.json", valid)
    reference = yaml.safe_load((REPO / "configs/default.yaml").read_text())
    reference.update(llm_base_url=base_url, temperature=0.0)
    reasoning = dict(reference)
    reasoning.update(llm_model="gpt-5-mini", temperature=1.0, input_cost_per_million=0.25,
                     output_cost_per_million=2.0, reasoning_effort="low", request_timeout_seconds=300)
    for name, config in (("config_4omini.yaml", reference), ("config_gpt5mini.yaml", reasoning)):
        path = ROOT / name
        if path.exists() and yaml.safe_load(path.read_text()) != config:
            raise RuntimeError(f"Existing config changed: {name}")
        path.write_text(yaml.safe_dump(config, sort_keys=False))
    save_json(ROOT / "panel_verification.json", {"sha256": PANEL_HASH, "users": users,
              "num_users": 50, "includes_30_user_pilot": True})
    print("Prepared: unchanged repository, valid bundle, fixed 50-user panel, both configs", flush=True)
    return base_url, users


def validate_profiles(path, users):
    profiles = rows(path / "profiles.jsonl")
    manifests = rows(path / "profile_manifests.jsonl")
    if len(profiles) != 50 or len(manifests) != 50:
        raise RuntimeError("Profiles and profile manifests must each contain exactly 50 rows")
    if {int(row["user_id"]) for row in profiles} != set(users):
        raise RuntimeError("Profile users differ from the fixed panel")
    if {int(row["user_id"]) for row in manifests} != set(users):
        raise RuntimeError("Profile manifest users differ from the fixed panel")
    required = {"user_id", "raw_user_id", "interaction_history", "unique_tastes", "social_traits", "demographics"}
    if any(not required <= set(row) or len(row["interaction_history"]) != 10 for row in profiles):
        raise RuntimeError("Profile components or history size differ from requirements")
    return {name: digest(path / name) for name in ("profiles.jsonl", "profile_manifests.jsonl", "run_manifest.json")}


def get_profiles(base_url, users):
    profile_root = ROOT / "profiles"
    if (profile_root / "profiles.jsonl").exists():
        hashes = validate_profiles(profile_root, users)
        print("Reusing validated shared profiles", flush=True)
    else:
        for attempt in range(1, 4):
            target = profile_root if not profile_root.exists() else ROOT / ("profiles_attempt_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
            try:
                execute("profiles", [sys.executable, "-m", "agent_reranking.cli", "generate-profiles",
                        "--bundle", BUNDLE, "--users-file", str(PANEL), "--method", "ours", "--model", "gpt-4o-mini",
                        "--base-url", base_url, "--profile-components", "all", "--history-size", "10", "--seed", "42",
                        "--concurrency", "3", "--requests-per-minute", "60", "--tokens-per-minute", "100000",
                        "--max-cost-usd", "2", "--output-dir", str(target)], f"profiles_attempt_{attempt}_{now().replace(':', '-')}.log")
                hashes = validate_profiles(target, users)
                if target != profile_root:
                    if profile_root.exists():
                        profile_root.rename(ROOT / ("profiles_failed_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")))
                    target.rename(profile_root)
                break
            except RuntimeError:
                if not target.exists():
                    target.mkdir()
                if attempt == 3:
                    raise
        else:
            raise RuntimeError("Profile generation failed")
    hash_path = ROOT / "profile_hashes.json"
    if hash_path.exists() and json.loads(hash_path.read_text()) != hashes:
        raise RuntimeError("The shared profiles changed between executions")
    save_json(hash_path, hashes)


def run_command(tag, smoke=False):
    is_reasoning = tag != "gpt-4o-mini"
    command = [sys.executable, str(WRAPPER)] if is_reasoning else [sys.executable, "-m", "agent_reranking.cli"]
    command += ["run", "--config", str(ROOT / ("config_gpt5mini.yaml" if is_reasoning else "config_4omini.yaml")),
                "--llm-model", "gpt-5-mini" if is_reasoning else "gpt-4o-mini", "--bundle", BUNDLE,
                "--users-file", str(PANEL), "--profiles", str(ROOT / "profiles/profiles.jsonl"),
                "--prompt-version", "behavior-align-rating-social-traits", "--profile-components", "all",
                "--profile-protocol", "separated", "--concurrency", "5", "--requests-per-minute", "60",
                "--tokens-per-minute", "200000", "--max-cost-usd", "0.2" if smoke else ("4" if is_reasoning else "1"),
                "--output-root", str(ROOT / tag / "runs")]
    if smoke:
        command += ["--case-limit", "2"]
    return command


def latest_run(tag):
    directories = sorted((ROOT / tag / "runs").glob("*/config.yaml"))
    if len(directories) > 1:
        raise RuntimeError(f"Ambiguous run directories for {tag}")
    return directories[0].parent if directories else None


def verify_run(root, users):
    manifest = json.loads((root / "run_manifest.json").read_text())
    actions = rows(root / "actions.jsonl")
    expected = {(model, user) for model in MODELS for user in users}
    pairs = {(row["model"], int(row["user_id"])) for row in actions}
    if manifest["status"] != "complete" or manifest["completed_cases"] != 150 or len(actions) != 150 or pairs != expected:
        raise RuntimeError("Run is not complete with 150 unique expected cases")
    rankings = rows(root / "rankings.jsonl")
    if len(rankings) != 150 or {(row["model"], int(row["user_id"])) for row in rankings} != expected:
        raise RuntimeError("Ranking coverage differs")
    failures = rows(root / "failures.jsonl")
    if any((row["model"], int(row["user_id"])) not in pairs for row in failures):
        raise RuntimeError("A historical failure has not been recovered")
    return manifest


def run_full(tag, users):
    command = run_command(tag)
    while True:
        root = latest_run(tag)
        if root and (root / "run_manifest.json").exists():
            manifest = json.loads((root / "run_manifest.json").read_text())
            if manifest["status"] == "complete":
                return root, verify_run(root, users)
        current = command + (["--resume", str(root.resolve())] if root else [])
        execute(tag, current, tag + ".log", "low" if tag != "gpt-4o-mini" else None)


def smoke_test():
    root = latest_run("smoke")
    if root is None:
        execute("smoke", run_command("smoke", smoke=True), "smoke.log", "low")
        root = latest_run("smoke")
    if root is None:
        raise RuntimeError("Smoke run directory missing")
    failures = rows(root / "failures.jsonl")
    if failures:
        print(json.dumps(failures, indent=2).replace(api_key("OPENAI_API_KEY"), "[REDACTED]"), flush=True)
        raise RuntimeError("GPT-5-mini smoke has failures; stopping without changing model alias or parameters")
    actions = rows(root / "actions.jsonl")
    if len(actions) != 2:
        raise RuntimeError("Smoke must successfully complete exactly two cases")
    print("GPT-5-mini smoke: two successful cases, no failures", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    os.environ["AGENT_RERANKING_ENV"] = str(WORKSPACE / "gpt5.env")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    with (ROOT / "experiment.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        base_url, users = prepare()
        if args.prepare_only:
            return
        get_profiles(base_url, users)
        reference_root, reference = run_full("gpt-4o-mini", users)
        smoke_test()
        reasoning_root, reasoning = run_full("gpt-5-mini_low", users)
        validate_profiles(ROOT / "profiles", users)
        git_state()
        save_json(ROOT / "verified_runs.json", {
            "reference": {"run_dir": str(reference_root), **reference},
            "reasoning": {"run_dir": str(reasoning_root), **reasoning},
            "verified_at_utc": now(), "panel_sha256": PANEL_HASH,
            "profile_sha256": digest(ROOT / "profiles/profiles.jsonl")})
        print("Both runs verified: 150 cases each, unchanged repository", flush=True)


if __name__ == "__main__":
    main()