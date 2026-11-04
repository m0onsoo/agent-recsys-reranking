import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

STAGES = ("sampled_baseline", "click_only", "converted_then_original", "three_tier")
METRICS = ("recall@10", "ndcg@10")
MODELS = ("MF", "LightGCN", "MultiVAE")


def rows(path):
    with path.open() as source:
        return [json.loads(line) for line in source if line.strip()]


def csv_rows(path):
    with path.open(newline="") as source:
        return list(csv.DictReader(source))


def percentile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_changes(columns, num_users, resamples=2000):
    if any(len(values) != num_users for values in columns.values()):
        raise ValueError("Bootstrap requires one paired metric delta per user")
    generator = random.Random(42)
    draws = {name: [] for name in columns}
    for _ in range(resamples):
        counts = Counter(generator.choices(range(num_users), k=num_users))
        for name, values in columns.items():
            draws[name].append(sum(values[index] * count for index, count in counts.items()) / num_users)
    return {name: {"change": sum(columns[name]) / num_users,
                   "ci_lower": percentile(values, 0.025), "ci_upper": percentile(values, 0.975)}
            for name, values in draws.items()}


def pearson(pairs):
    if len(pairs) < 2:
        return None
    mean_first = sum(pair[0] for pair in pairs) / len(pairs)
    mean_second = sum(pair[1] for pair in pairs) / len(pairs)
    covariance = sum((first - mean_first) * (second - mean_second) for first, second in pairs)
    denominator = math.sqrt(sum((first - mean_first) ** 2 for first, _ in pairs) *
                            sum((second - mean_second) ** 2 for _, second in pairs))
    return covariance / denominator if denominator else None


def build_reports(root, profile_root, runs, users):
    from agent_reranking.bundle import DataBundle

    users = sorted(users)
    profiles = {int(row["user_id"]): row for row in rows(profile_root / "profiles.jsonl")}
    bundle = DataBundle(root.parent.parent / "agent-recsys-reranking/data/derived/ml1m_ro_n1000_seed42")
    baseline_check = json.loads((root / "baselines_check.json").read_text())["models"]
    missing_by_condition = {condition: json.loads((root / f"unrecovered_cases_{condition}.json").read_text())
                            for condition in runs}
    coverage = ["| Condition | Expected | Completed | Missing |", "|---|---:|---:|---:|"]
    for condition, missing in missing_by_condition.items():
        coverage.append(f"| {condition} | 3000 | {3000 - len(missing)} | {len(missing)} |")
    table = ["# 1,000 用户实验汇总", "",
             "四个条件均已完成有界恢复与验收；最终缺失案例有单独清单，不以零分填补。",
             *coverage, "",
             "Changes are absolute differences against the same model's sampled backbone baseline.",
             "Failures 是历史失败记录数，可能包含已恢复的案例；最终缺失数见上表。",
             "Recorded cost is model-specific calls.jsonl cost, repeated across stages (do not sum stage rows).",
             "See run_info.md for the more complete all-request ledger and profile costs.", "",
             "| Condition | Model | Stage | Cases | Failures | Recorded cost | Recall@10 | NDCG@10 | Recall change | NDCG change |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    analysis = ["# 描述性分析", "",
                "以下为描述性结果；分析在四条件有界恢复和验收结束后进行。",
                *coverage, "",
                "The panel is fixed and conditioned on at least one held-out positive in every backbone's Top-20.",
                "Relevance is every held-out interaction, regardless of rating; findings do not generalize to all MovieLens users.",
                "Costs are estimates, not verified proxy bills. Check actual billing on the dashboard.", "",
                "## Paired User-Clustered Bootstrap", "",
                "95% percentile intervals; 2,000 resamples of completed user clusters, seed 42.",
                "Each sampled user contributes both baseline and reranked metrics; changes are absolute, not relative.",
                "Same cluster draws are reused within each condition/model across stages and metrics; no multiplicity adjustment.",
                "若存在缺失，各条件/模型的完成用户集合可能不同，跨条件比较不再完全配对；缺失用户不填补。",
                "The sampled_baseline delta and interval are identically zero.", "",
                "| Condition | Model | Stage | Metric | Change | 95% CI lower | 95% CI upper |",
                "|---|---|---|---|---:|---:|---:|"]
    confidence_rows = []
    activity_counts = defaultdict(Counter)
    activity_denominators = Counter()
    outcomes = defaultdict(Counter)
    watch_counts = defaultdict(Counter)
    diversity = defaultdict(lambda: {"clicked": 0, "adjacent": 0, "fractions": []})
    conformity = defaultdict(list)
    metric_cache = {}
    case_counts = {}
    for condition, run_root in runs.items():
        metrics = csv_rows(run_root / "per_user_metrics.csv")
        metric_cache[condition] = metrics
        summary = {(row["model"], row["stage"]): row for row in csv_rows(run_root / "summary.csv")}
        failed_counts = Counter(row["model"] for row in rows(run_root / "failures.jsonl"))
        model_costs = defaultdict(float)
        for call in rows(run_root / "calls.jsonl"):
            model_costs[call["model"]] += call.get("estimated_cost_usd", 0.0)
        for model in MODELS:
            lookup = {(row["stage"], int(row["user_id"])): row for row in metrics if row["model"] == model}
            completed_users = [user for user in users if ("sampled_baseline", user) in lookup]
            case_counts[(condition, model)] = len(completed_users)
            if not completed_users:
                for stage in STAGES:
                    table.append(f"| {condition} | {model} | {stage} | 0 | {failed_counts[model]} | ${model_costs[model]:.6f} | N/A | N/A | N/A | N/A |")
                continue
            columns = {}
            for stage in STAGES:
                aggregate = summary[(model, stage)]
                averages = {metric: sum(float(lookup[(stage, user)][metric]) for user in completed_users) / len(completed_users)
                            for metric in METRICS}
                baseline_averages = {metric: sum(float(lookup[("sampled_baseline", user)][metric]) for user in completed_users) / len(completed_users)
                                     for metric in METRICS}
                for metric in METRICS:
                    if len(completed_users) == 1000 and abs(baseline_averages[metric] - baseline_check[model][metric]) > 1e-10:
                        raise ValueError(f"Sampled backbone baseline mismatch: {condition} {model} {metric}")
                    if abs(averages[metric] - float(aggregate[metric])) > 1e-10:
                        raise ValueError("Summary and per-user metrics mismatch")
                    columns[(stage, metric)] = [float(lookup[(stage, user)][metric]) -
                                               float(lookup[("sampled_baseline", user)][metric]) for user in completed_users]
                table.append(f"| {condition} | {model} | {stage} | {len(completed_users)} | {failed_counts[model]} | "
                             f"${model_costs[model]:.6f} | {averages['recall@10']:.7f} | {averages['ndcg@10']:.7f} | "
                             f"{averages['recall@10'] - baseline_averages['recall@10']:+.7f} | "
                             f"{averages['ndcg@10'] - baseline_averages['ndcg@10']:+.7f} |")
            confidence = bootstrap_changes(columns, len(completed_users), resamples=2000)
            for (stage, metric), result in confidence.items():
                confidence_rows.append({"condition": condition, "model": model, "stage": stage,
                                        "metric": metric, **result, "users": len(completed_users), "resamples": 2000})
                analysis.append(f"| {condition} | {model} | {stage} | {metric} | {result['change']:+.7f} | "
                                f"{result['ci_lower']:+.7f} | {result['ci_upper']:+.7f} |")
        for row in rows(run_root / "actions.jsonl"):
            model, user = row["model"], int(row["user_id"])
            action = row["actions"]
            traits = profiles[user]["social_traits"]
            clicked = action["clicked_item_ids"]
            activity_key = (condition, model, int(traits["activity"]["level"]))
            activity_counts[activity_key][len(clicked)] += 1
            activity_denominators[activity_key] += 1
            key = (condition, model)
            watch = action["watch_decision"]
            if watch not in ("watch", "not_ready"):
                raise ValueError("Unexpected watch decision")
            watch_counts[key][watch] += 1
            assessments = action["motive_assessments"]
            if set(assessments) != {str(item) for item in clicked}:
                raise ValueError("Clicked items and outcome assessments differ")
            adjacent = sum(action["candidate_assessments"][str(item)]["alignment"] == "adjacent" for item in clicked)
            diversity_key = (condition, model, int(traits["diversity"]["level"]))
            diversity[diversity_key]["clicked"] += len(clicked)
            diversity[diversity_key]["adjacent"] += adjacent
            if clicked:
                diversity[diversity_key]["fractions"].append(adjacent / len(clicked))
            for item, assessment in assessments.items():
                outcome = assessment["outcome"]
                if outcome not in ("confirmed", "contradicted", "insufficient"):
                    raise ValueError("Unexpected outcome")
                outcomes[key][outcome] += 1
                average = bundle.catalog[int(item)].get("average_rating")
                if average is not None:
                    conformity[(condition, model, int(traits["conformity"]["level"]))].append(
                        (float(assessment["predicted_rating"]), float(average)))
    (root / "summary_table.md").write_text("\n".join(table) + "\n")
    analysis.extend(["", "## Click Counts by Activity", "",
                     "Grouping uses each user's stored Activity level, including in conditions where persona was withheld.",
                     "Each case contributes one click count (0-20); percentages use cases within the Activity group.", "",
                     "| Condition | Model | Activity | Click count | Cases | Group cases | Percent |",
                     "|---|---|---:|---:|---:|---:|---:|"])
    for key in sorted(activity_counts):
        condition, model, level = key
        denominator = activity_denominators[key]
        for click_count in range(21):
            count = activity_counts[key][click_count]
            analysis.append(f"| {condition} | {model} | {level} | {click_count} | {count} | {denominator} | {100 * count / denominator:.2f}% |")
    analysis.extend(["", "## Outcomes and Watch Rates", "",
                     "Outcomes are per clicked-item assessment; watch rates are per model-user case.",
                     "Zero-click cases are deterministically not_ready and have no item-level outcomes.", "",
                     "| Condition | Model | Confirmed | Contradicted | Insufficient | Assessed items | Watch | Not ready | Watch rate |",
                     "|---|---|---:|---:|---:|---:|---:|---:|---:|"])
    for key in sorted(watch_counts):
        counts = outcomes[key]
        total = sum(counts.values())
        watch = watch_counts[key]
        denominator = case_counts[key]
        if sum(watch.values()) != denominator:
            raise ValueError("Watch count denominator mismatch")
        percentages = [f"{counts[name]} ({100 * counts[name] / total:.2f}%)" if total else "0 (N/A)"
                       for name in ("confirmed", "contradicted", "insufficient")]
        analysis.append(f"| {key[0]} | {key[1]} | {' | '.join(percentages)} | {total} | {watch['watch']} | "
                        f"{watch['not_ready']} | {100 * watch['watch'] / denominator:.2f}% |")
    analysis.extend(["", "## Adjacent Clicks by Diversity", "",
                     "Pooled fraction weights clicked items; mean case fraction excludes zero-click cases.", "",
                     "| Condition | Model | Diversity | Clicked items | Adjacent items | Pooled adjacent fraction | Mean case fraction |",
                     "|---|---|---:|---:|---:|---:|---:|"])
    for key, values in sorted(diversity.items()):
        pooled = f"{values['adjacent'] / values['clicked']:.6f}" if values["clicked"] else "N/A"
        mean_case = f"{sum(values['fractions']) / len(values['fractions']):.6f}" if values["fractions"] else "N/A"
        analysis.append(f"| {key[0]} | {key[1]} | {key[2]} | {values['clicked']} | {values['adjacent']} | {pooled} | {mean_case} |")
    analysis.extend(["", "## Predicted and Aggregate Ratings by Conformity", "",
                     "Aggregate ratings use checkpoint-training interactions only. Pearson correlation is descriptive",
                     "over pooled clicked-item assessments; repeated users/items are not independent observations.", "",
                     "| Condition | Model | Conformity | Items with aggregate rating | Mean predicted | Mean aggregate | Mean absolute difference | Pearson r |",
                     "|---|---|---:|---:|---:|---:|---:|---:|"])
    for key, pairs in sorted(conformity.items()):
        count = len(pairs)
        coefficient = pearson(pairs)
        correlation = "N/A" if coefficient is None else f"{coefficient:.6f}"
        analysis.append(f"| {key[0]} | {key[1]} | {key[2]} | {count} | {sum(first for first, _ in pairs) / count:.6f} | "
                        f"{sum(second for _, second in pairs) / count:.6f} | "
                        f"{sum(abs(first - second) for first, second in pairs) / count:.6f} | {correlation} |")
    for document in (table, analysis):
        document.extend(["", "## 最终缺失案例", ""])
        for condition, missing in missing_by_condition.items():
            document.append(f"- {condition}: {len(missing)} 个；清单 unrecovered_cases_{condition}.json。")
            document.extend(f"  - {row['model']} user {row['user_id']}: {row['last_error']}" for row in missing)
    (root / "summary_table.md").write_text("\n".join(table) + "\n")
    (root / "analysis.md").write_text("\n".join(analysis) + "\n")
    (root / "bootstrap_results.json").write_text(json.dumps(confidence_rows, indent=2, sort_keys=True) + "\n")