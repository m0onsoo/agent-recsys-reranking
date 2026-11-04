import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

from agent_reranking.bundle import DataBundle
from agent_reranking.io import stable_hash
from agent_reranking.runner import _profile_payload

from run_experiment import ROOT, REPO, MODELS, EXPECTED_STATUS, PANEL_HASH, latest_run, panel_users, rows, save_json, validate_profiles, verify_run


STAGES = ("converted_then_original", "click_only", "three_tier")
RESAMPLES = 2000
BOOTSTRAP_SEED = 42


def mean(values):
    return statistics.fmean(values) if values else None


def quantile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap(differences):
    generator = random.Random(BOOTSTRAP_SEED)
    estimates = [statistics.fmean(generator.choices(differences, k=len(differences)))
                 for _ in range(RESAMPLES)]
    return mean(differences), quantile(estimates, 0.025), quantile(estimates, 0.975)


def write_csv(name, data):
    if not data:
        raise RuntimeError("Refusing to write an empty analysis table")
    with (ROOT / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def read_metrics(root):
    with (root / "per_user_metrics.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))
    metrics = {(row["model"], int(row["user_id"]), row["stage"]):
               {name: float(row[name]) for name in ("recall@10", "ndcg@10")} for row in records}
    if len(records) != len(metrics):
        raise RuntimeError("Duplicate per-user metrics")
    return metrics


def comparison(reference, reasoning, users):
    output = []
    for stage in STAGES:
        for model in MODELS:
            result = {"stage": stage, "backbone": model}
            for metric in ("recall@10", "ndcg@10"):
                baseline = mean([reference[(model, user, "sampled_baseline")][metric] for user in users])
                reference_value = mean([reference[(model, user, stage)][metric] for user in users])
                reasoning_value = mean([reasoning[(model, user, stage)][metric] for user in users])
                result.update({metric + "_backbone": baseline,
                               metric + "_4omini": reference_value,
                               metric + "_4omini_delta": reference_value - baseline,
                               metric + "_4omini_relative_change": (reference_value - baseline) / baseline if baseline else None,
                               metric + "_gpt5mini": reasoning_value,
                               metric + "_gpt5mini_delta": reasoning_value - baseline,
                               metric + "_gpt5mini_relative_change": (reasoning_value - baseline) / baseline if baseline else None,
                               metric + "_gpt5mini_minus_4omini": reasoning_value - reference_value})
            output.append(result)
    return output


def paired_ci(reference, reasoning, users):
    output = []
    for model in (*MODELS, "pooled"):
        included = MODELS if model == "pooled" else (model,)
        differences = [mean([reasoning[(backbone, user, "converted_then_original")]["ndcg@10"]
                           - reference[(backbone, user, "converted_then_original")]["ndcg@10"]
                           for backbone in included]) for user in users]
        estimate, lower, upper = bootstrap(differences)
        output.append({"backbone": model, "stage": "converted_then_original", "metric": "ndcg@10",
                       "gpt5mini_minus_4omini": estimate, "ci95_lower": lower, "ci95_upper": upper,
                       "num_user_clusters": len(users), "num_backbone_cases": len(users) * len(included),
                       "bootstrap_resamples": RESAMPLES, "bootstrap_seed": BOOTSTRAP_SEED,
                       "method": "paired user-cluster percentile bootstrap"})
    return output


def behavior_stats(actions, bundle, label):
    output = []
    for model in MODELS:
        selected = [row for row in actions.values() if row["model"] == model]
        clicks = [len(row["actions"]["clicked_item_ids"]) for row in selected]
        alignments = Counter()
        outcomes = Counter()
        rating_differences = []
        missing_ratings = 0
        not_ready = 0
        for row in selected:
            action = row["actions"]
            slate = bundle.candidates[(model, int(row["user_id"]))]["item_ids"]
            if set(action["candidate_assessments"]) != {str(item) for item in slate}:
                raise RuntimeError("Candidate assessments do not cover the exact slate")
            alignments.update(assessment["alignment"] for assessment in action["candidate_assessments"].values())
            not_ready += action["watch_decision"] == "not_ready"
            if set(action["motive_assessments"]) != {str(item) for item in action["clicked_item_ids"]}:
                raise RuntimeError("Conversion assessments do not cover every clicked item")
            for item in action["clicked_item_ids"]:
                assessment = action["motive_assessments"][str(item)]
                outcomes[assessment["outcome"]] += 1
                average = bundle.catalog[int(item)].get("average_rating")
                if average is None:
                    missing_ratings += 1
                else:
                    rating_differences.append(abs(assessment["predicted_rating"] - average))
        total_assessments = sum(alignments.values())
        total_clicked = sum(clicks)
        if total_assessments != len(selected) * 20 or sum(outcomes.values()) != total_clicked:
            raise RuntimeError("Behavior denominators differ from expected coverage")
        result = {"llm": label, "backbone": model, "num_cases": len(selected), "mean_clicks": mean(clicks),
                  "click_count_distribution": json.dumps(dict(sorted(Counter(clicks).items())), sort_keys=True),
                  "num_candidate_assessments": total_assessments,
                  "strong_share": alignments["strong"] / total_assessments,
                  "adjacent_share": alignments["adjacent"] / total_assessments,
                  "none_share": alignments["none"] / total_assessments,
                  "not_ready_cases": not_ready, "not_ready_share": not_ready / len(selected),
                  "num_clicked_item_assessments": total_clicked}
        for outcome in ("confirmed", "contradicted", "insufficient"):
            result[outcome + "_count"] = outcomes[outcome]
            result[outcome + "_share"] = outcomes[outcome] / total_clicked if total_clicked else None
        result.update(mean_abs_predicted_minus_average_rating=mean(rating_differences),
                      rating_comparison_items=len(rating_differences), missing_average_rating_items=missing_ratings)
        output.append(result)
    return output


def agreement(reference, reasoning):
    output = []
    for model in (*MODELS, "pooled"):
        keys = [key for key in reference if key[0] == model or model == "pooled"]
        click_matches = 0
        conversion_matches = 0
        both_matches = 0
        both_no_conversion = 0
        for key in keys:
            first, second = reference[key]["actions"], reasoning[key]["actions"]
            click_equal = set(first["clicked_item_ids"]) == set(second["clicked_item_ids"])
            conversion_equal = set(first["converted_item_ids"]) == set(second["converted_item_ids"])
            click_matches += click_equal
            conversion_matches += conversion_equal
            both_matches += click_equal and conversion_equal
            both_no_conversion += not first["converted_item_ids"] and not second["converted_item_ids"]
        output.append({"backbone": model, "num_pairs": len(keys),
                       "exact_click_set_matches": click_matches, "exact_click_set_agreement": click_matches / len(keys),
                       "exact_conversion_matches": conversion_matches, "exact_conversion_agreement": conversion_matches / len(keys),
                       "both_agree_count": both_matches, "both_agree_share": both_matches / len(keys),
                       "both_no_conversion_cases": both_no_conversion})
    return output


def run_cost(root, label, events, stage):
    manifest = json.loads((root / "run_manifest.json").read_text())
    calls = rows(root / "calls.jsonl")
    cost = sum(call.get("estimated_cost_usd", 0) for call in calls)
    if not math.isclose(cost, manifest["estimated_cost_usd"], abs_tol=1e-9):
        raise RuntimeError("Recorded costs do not match the manifest")
    tokens = [call["usage"]["completion_tokens"] for call in calls if "completion_tokens" in call.get("usage", {})]
    prompt_tokens = [call["usage"]["prompt_tokens"] for call in calls if "prompt_tokens" in call.get("usage", {})]
    starts = [record["utc"] for record in events if record["stage"] == stage and record["state"] == "start"]
    ends = [record["utc"] for record in events if record["stage"] == stage and record["state"] == "end"]
    start, end = min(starts) if starts else None, max(ends) if ends else None
    duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() if start and end else None
    per_stage = {}
    for name in ("click", "conversion"):
        selected = [call["usage"]["completion_tokens"] for call in calls
                    if call.get("stage") == name and "completion_tokens" in call.get("usage", {})]
        per_stage[name] = {"recorded_calls": len(selected), "mean_completion_tokens": mean(selected)}
    return {"llm": label, "completed_cases": manifest["completed_cases"], "status": manifest["status"],
            "recorded_cost_usd": cost, "recorded_cost_per_case_usd": cost / manifest["completed_cases"],
            "recorded_calls": len(calls), "calls_with_completion_usage": len(tokens),
            "mean_completion_tokens_per_call": mean(tokens), "total_completion_tokens": sum(tokens),
            "total_prompt_tokens": sum(prompt_tokens),
            "total_reported_reasoning_tokens": sum(call.get("usage", {}).get("completion_tokens_details", {}).get("reasoning_tokens", 0) for call in calls),
            "historical_failure_rows": manifest["failure_count"],
            "start_utc": start, "end_utc": end, "wall_seconds_including_resumes": duration,
            "completion_tokens_by_stage": json.dumps(per_stage, sort_keys=True)}


def display(value, places=5):
    return "NA" if value is None else f"{value:.{places}f}"


def percent(value):
    return "NA" if value is None else f"{100 * value:.1f}%"


def report(comparisons, intervals, behaviors, agreements, costs, provenance):
    lines = ["# 50 用户配对 LLM 重排序实验", "", "## 完整性与设置", "",
             "固定 seed-42 的 50 用户面板，两组各 150/150 个唯一案例，所有历史失败均已恢复。",
             "共享同一份 gpt-4o-mini 生成的全输入画像、候选 Top-20 和 handoff 提示词；协议为 separated。",
             "行为运行 concurrency=5、RPM=60、TPM=200000。4o-mini temperature=0；GPT-5-mini temperature=1、reasoning_effort=low。",
             "", f"代码 SHA：`{provenance['commit']}`。面板 SHA-256：`{provenance['panel_sha256']}`。",
             f"共享 profiles SHA-256：`{provenance['profile_sha256']}`。", "",
             "## 同一 50 用户的骨干基线", "", "| 骨干 | Recall@10 | NDCG@10 |", "|---|---:|---:|"]
    if not provenance["repository_final_gate_passed"]:
        lines[2:2] = ["**验收警告：两组产物完整，但最终仓库状态检查未通过；运行期间检测到外部源码改动。未恢复或覆盖这些改动，本报告是带来源限制的统计结果，不代表全部硬性要求已满足。**", ""]
    for row in comparisons[:3]:
        lines.append(f"| {row['backbone']} | {display(row['recall@10_backbone'])} | {display(row['ndcg@10_backbone'])} |")
    for metric in ("recall@10", "ndcg@10"):
        lines += ["", f"## {metric} 配对比较", "",
                  "括号内为相对同骨干基线的绝对变化和相对百分比；最后一列为 GPT-5-mini 减 4o-mini 的绝对差。",
                  "", "| 策略 | 骨干 | 4o-mini（Δ基线；相对变化） | GPT-5-mini（Δ基线；相对变化） | GPT-5-mini − 4o-mini |",
                  "|---|---|---:|---:|---:|"]
        for row in comparisons:
            first = f"{row[metric + '_4omini']:.5f} ({row[metric + '_4omini_delta']:+.5f}; {row[metric + '_4omini_relative_change']:+.2%})"
            second = f"{row[metric + '_gpt5mini']:.5f} ({row[metric + '_gpt5mini_delta']:+.5f}; {row[metric + '_gpt5mini_relative_change']:+.2%})"
            lines.append(f"| {row['stage']} | {row['backbone']} | {first} | {second} | {row[metric + '_gpt5mini_minus_4omini']:+.5f} |")
    lines += ["", "## 用户聚类配对 Bootstrap", "",
              "主策略 converted_then_original 的 NDCG@10 差值。seed=42，2,000 次 percentile bootstrap；每次有放回抽 50 个用户，保留用户的配对模型结果。",
              "pooled 先对每个用户的三个骨干差值等权平均，再抽用户；不是把 150 个案例独立抽样。", "",
              "| 骨干 | GPT-5-mini − 4o-mini | 95% CI |", "|---|---:|---:|"]
    for row in intervals:
        lines.append(f"| {row['backbone']} | {row['gpt5mini_minus_4omini']:+.5f} | [{row['ci95_lower']:+.5f}, {row['ci95_upper']:+.5f}] |")
    if all(row["ci95_lower"] <= 0 <= row["ci95_upper"] for row in intervals):
        lines += ["", "所有主策略区间都包含 0；这批用户上没有明确证据说明 GPT-5-mini 的 NDCG 优于 4o-mini，也不能把不显著解释为两者等效。"]
    lines += ["", "## 行为统计", "",
              "标签比例的分母为各骨干 50×20=1,000 个候选；outcome 和评分偏差按点击项目加权。缺失平均评分的项目排除，并在 CSV 中记录数量。", "",
              "| LLM | 骨干 | 平均点击 | strong / adjacent / none | not_ready | confirmed / contradicted / insufficient | 平均评分绝对偏差 |",
              "|---|---|---:|---|---:|---|---:|"]
    for row in behaviors:
        alignment = " / ".join(percent(row[name + "_share"]) for name in ("strong", "adjacent", "none"))
        outcome = " / ".join(percent(row[name + "_share"]) for name in ("confirmed", "contradicted", "insufficient"))
        lines.append(f"| {row['llm']} | {row['backbone']} | {row['mean_clicks']:.2f} | {alignment} | {percent(row['not_ready_share'])} | {outcome} | {display(row['mean_abs_predicted_minus_average_rating'], 3)} |")
    lines += ["", "### 点击数量分布", "", "格式为 点击数:案例数；每行合计 50。", ""]
    for row in behaviors:
        distribution = json.loads(row["click_count_distribution"])
        distribution = sorted(distribution.items(), key=lambda item: int(item[0]))
        lines.append(f"- {row['llm']} / {row['backbone']}: " + ", ".join(f"{count}:{frequency}" for count, frequency in distribution))
    lines += ["", "### 两 LLM 的精确一致率", "",
              "点击比较集合，不比较数组顺序；conversion 比较最终电影集合，双方均为空也计为一致。", "",
              "| 骨干 | 精确点击集合一致 | conversion 一致 | 两项同时一致 | 双方均不转化案例 |", "|---|---:|---:|---:|---:|"]
    for row in agreements:
        lines.append(f"| {row['backbone']} | {percent(row['exact_click_set_agreement'])} | {percent(row['exact_conversion_agreement'])} | {percent(row['both_agree_share'])} | {row['both_no_conversion_cases']} |")
    lines += ["", "## 费用与时间", "",
              "费用是 calls.jsonl 的 token-rate 估算，不是代理账单。completion_tokens 包含接口计入的推理 tokens；失败案例若整例失败，其调用可能未写入，实际成本可能更高。", "",
              "| LLM | 案例 | 记录费用 USD | 每案例 USD | 记录调用 | 平均 completion tokens / call | 历史失败行 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for row in costs:
        lines.append(f"| {row['llm']} | {row['completed_cases']} | {row['recorded_cost_usd']:.6f} | {row['recorded_cost_per_case_usd']:.6f} | {row['recorded_calls']} | {display(row['mean_completion_tokens_per_call'], 1)} | {row['historical_failure_rows']} |")
    lines += ["", "UTC 起止时间（包括续跑）：", ""]
    for row in costs:
        lines.append(f"- {row['llm']}: {row['start_utc']} → {row['end_utc']}; {display(row['wall_seconds_including_resumes'], 1)} 秒。")
    lines += ["", "共享画像生成未持久化 token usage 或成本总额，不能从产物核算；已保存起止事件和全部生成日志，实际费用需要代理账单。Smoke 为独立的两案例开销，不并入正式组。", "",
              "## 限制与解读", "",
              "- n=50，结果和区间仅用于探索，不能替代 1,000 用户实验或真实用户验证。",
              "- GPT-5-mini temperature=1、4o-mini temperature=0；模型、解码参数与推理模式的差异无法拆开归因。",
              "- 使用实时 API alias，无版本锁定；温度 0 也不保证重复调用完全一致。代理返回的实际模型标识未被原代码持久化。",
              "- 面板要求三个骨干 Top-20 都命中至少一个测试交互；正例是所有测试交互，不按评分阈值筛选。结论不能推广到未筛选用户。",
              "- 画像由 4o-mini 生成并共享；这控制了输入差异，但没有评估 GPT-5-mini 自行生成画像的效果。",
              "- Bootstrap 是用户聚类的配对 percentile 区间；未做多重比较校正，不能把单个区间当作普遍优越的证据。",
              "- 平均评分绝对偏差是模型预测与群体均值的差异，不是对用户真实评分的预测误差。", ""]
    if not provenance["repository_final_gate_passed"]:
        lines += ["## 源码状态异常", "",
                  "初始 code_version.txt 只有未跟踪 egg-info，最终状态出现以下修改；这些修改未由本执行入口写入。",
                  "", "```text", provenance["git_status"], "```", "",
                  "当前源码修改时间晚于决策子进程启动，两组 calls.jsonl 均无新增 call_id 日志字段或 transcript 文件，与旧代码在启动时已载入相符。",
                  "但执行时未记录逐文件源代码哈希，因此无法仅凭事后 mtime 证明全部运行代码一致，不能宣称完整通过源代码不变的验收。", ""]
    (ROOT / "report_zh.md").write_text("\n".join(lines))


def analyze():
    users = panel_users()
    verified_path = ROOT / "verified_runs.json"
    if verified_path.exists():
        verified = json.loads(verified_path.read_text())
    else:
        reference_root = latest_run("gpt-4o-mini")
        reasoning_root = latest_run("gpt-5-mini_low")
        verified = {"reference": {"run_dir": str(reference_root), **verify_run(reference_root, users)},
                    "reasoning": {"run_dir": str(reasoning_root), **verify_run(reasoning_root, users)},
                    "panel_sha256": PANEL_HASH}
    reference_root = Path(verified["reference"]["run_dir"])
    reasoning_root = Path(verified["reasoning"]["run_dir"])
    verify_run(reference_root, users)
    verify_run(reasoning_root, users)
    profile_hashes = validate_profiles(ROOT / "profiles", users)
    if profile_hashes != json.loads((ROOT / "profile_hashes.json").read_text()):
        raise RuntimeError("Shared profiles changed")
    bundle = DataBundle(REPO / "data/derived/ml1m_ro_n1000_seed42")
    profiles = {int(row["user_id"]): row for row in rows(ROOT / "profiles/profiles.jsonl")}
    reference_actions = {(row["model"], int(row["user_id"])): row for row in rows(reference_root / "actions.jsonl")}
    reasoning_actions = {(row["model"], int(row["user_id"])): row for row in rows(reasoning_root / "actions.jsonl")}
    reference_config = yaml.safe_load((reference_root / "config.yaml").read_text())
    reasoning_config = yaml.safe_load((reasoning_root / "config.yaml").read_text())
    allowed = {"llm_model", "temperature", "input_cost_per_million", "output_cost_per_million",
               "reasoning_effort", "request_timeout_seconds", "max_cost_usd", "output_root"}
    differences = {key for key in set(reference_config) | set(reasoning_config)
                   if reference_config.get(key) != reasoning_config.get(key)}
    if not differences <= allowed:
        raise RuntimeError("Unexpected cross-run config differences: " + str(differences - allowed))
    for key, reference in reference_actions.items():
        reasoning = reasoning_actions[key]
        user = key[1]
        expected_profile = stable_hash(_profile_payload(profiles[user], reference_config["profile_components"], reference_config["profile_protocol"]))
        expected_candidate = stable_hash(bundle.candidates[key])
        for row in (reference, reasoning):
            if row["profile_hash"] != expected_profile or row["candidate_hash"] != expected_candidate:
                raise RuntimeError("Profile or slate hash mismatch")
    if verified["reference"]["behavior_prompt_sha256"] != verified["reasoning"]["behavior_prompt_sha256"]:
        raise RuntimeError("Behavior prompt hashes differ")
    reference_metrics = read_metrics(reference_root)
    reasoning_metrics = read_metrics(reasoning_root)
    if set(reference_metrics) != set(reasoning_metrics) or len(reference_metrics) != 600:
        raise RuntimeError("Metric coverage must be 150 cases times four stages")
    for model in MODELS:
        for user in users:
            if reference_metrics[(model, user, "sampled_baseline")] != reasoning_metrics[(model, user, "sampled_baseline")]:
                raise RuntimeError("Backbone baselines differ")
    comparisons = comparison(reference_metrics, reasoning_metrics, users)
    intervals = paired_ci(reference_metrics, reasoning_metrics, users)
    behaviors = behavior_stats(reference_actions, bundle, "gpt-4o-mini") + behavior_stats(reasoning_actions, bundle, "gpt-5-mini_low")
    agreements = agreement(reference_actions, reasoning_actions)
    events = rows(ROOT / "execution_events.jsonl")
    costs = [run_cost(reference_root, "gpt-4o-mini", events, "gpt-4o-mini"),
             run_cost(reasoning_root, "gpt-5-mini_low", events, "gpt-5-mini_low"),
             run_cost(next((ROOT / "smoke/runs").glob("*/run_manifest.json")).parent, "gpt-5-mini_smoke", events, "smoke")]
    write_csv("comparison.csv", comparisons)
    write_csv("bootstrap_ci.csv", intervals)
    write_csv("behavior.csv", behaviors)
    write_csv("agreement.csv", agreements)
    write_csv("costs.csv", costs)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip()
    calls_by_run = {label: rows(root / "calls.jsonl") for label, root in (("reference", reference_root), ("reasoning", reasoning_root))}
    source_mtimes = {name: (REPO / "agent_reranking" / name).stat().st_mtime for name in ("agent.py", "client.py", "runner.py")}
    save_json(ROOT / "repository_final_state.json", {"commit": commit, "status": status,
              "required_status": EXPECTED_STATUS, "passed": status == EXPECTED_STATUS,
              "source_mtimes_unix": source_mtimes,
              "calls_with_new_call_id": {label: sum("call_id" in call for call in records) for label, records in calls_by_run.items()},
              "transcript_files_present": {label: (root / "transcripts.jsonl").exists() for label, root in (("reference", reference_root), ("reasoning", reasoning_root))}})
    provenance = {"commit": commit, "git_status": status, "panel_sha256": verified["panel_sha256"],
                  "repository_final_gate_passed": status == EXPECTED_STATUS,
                  "profile_sha256": profile_hashes["profiles.jsonl"],
                  "cross_run_config_differences": sorted(differences), "profile_and_slate_hashes_match_all_150_pairs": True,
                  "behavior_prompt_hashes_match": True, "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_resamples": RESAMPLES,
                  "wrapper_sha256": hashlib.sha256((ROOT.parent / "run_with_reasoning.py").read_bytes()).hexdigest()}
    save_json(ROOT / "analysis_verification.json", provenance)
    save_json(verified_path, {**verified, "repository_final_gate_passed": status == EXPECTED_STATUS,
              "profile_sha256": profile_hashes["profiles.jsonl"]})
    report(comparisons, intervals, behaviors, agreements, costs, provenance)
    artifacts = {}
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name not in ("artifact_hashes.json", "experiment.lock"):
            artifacts[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    save_json(ROOT / "artifact_hashes.json", artifacts)
    print("Verified run artifacts, paired inputs, baseline identity, behavior denominators, costs and bootstrap; wrote report_zh.md")
    print("Final repository-state gate passed:", status == EXPECTED_STATUS)
    print(json.dumps({"main_policy": comparisons[:3], "bootstrap": intervals, "costs": costs[:2]}, indent=2))


def self_test():
    estimate, lower, upper = bootstrap([0.1] * 50)
    assert all(math.isclose(value, 0.1) for value in (estimate, lower, upper))
    estimate, lower, upper = bootstrap([0.0] * 50)
    assert (estimate, lower, upper) == (0.0, 0.0, 0.0)
    pilot = ROOT.parent / "full/runs/20261103_170740_f6183fb320"
    if pilot.exists():
        actions = {(row["model"], int(row["user_id"])): row for row in rows(pilot / "actions.jsonl")}
        assert all(row["exact_click_set_agreement"] == row["exact_conversion_agreement"] == 1 for row in agreement(actions, actions))
        bundle = DataBundle(REPO / "data/derived/ml1m_ro_n1000_seed42")
        stats = behavior_stats(actions, bundle, "self_test_only")
        assert all(row["num_candidate_assessments"] == 600 for row in stats)
        metrics = read_metrics(pilot)
        users = sorted({key[1] for key in actions})
        assert all(row["ndcg@10_gpt5mini_minus_4omini"] == row["recall@10_gpt5mini_minus_4omini"] == 0 for row in comparison(metrics, metrics, users))
        assert all(row["ci95_lower"] == row["ci95_upper"] == 0 for row in paired_ci(metrics, metrics, users))
    print("Self-tests passed: bootstrap, identical-run agreement, metric differences and actual action schema; no experiment results written")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test() if args.self_test else analyze()