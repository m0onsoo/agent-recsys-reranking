#!/usr/bin/env python3
"""Offline analysis of the n1000 `full` condition. Makes no API calls and writes only
into this analysis_full/ folder. Usage: python3 analyze_full.py [run_dir]"""
import csv, glob, json, math, random, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # jinyi_results/n1000_v2
REPO = ROOT.parent.parent / "agent-recsys-reranking"
BUNDLE = REPO / "data/derived/ml1m_ro_n1000_seed42"
RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(sorted(glob.glob(str(ROOT / "n1000_align_rating/full/runs/*/")))[-1])
PROFILES = ROOT / "profiles/ours_all_n1000/profiles.jsonl"
MODELS = ("MF", "LightGCN", "MultiVAE")
K = 10
rng = random.Random(42)

def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
cand = {(c["model"], c["user_id"]): c for c in jl(BUNDLE / "candidates.jsonl")}
labels = {d["user_id"]: d["heldout_items"] for d in jl(BUNDLE / "evaluation_labels.jsonl")}
cat = {d["item_id"]: d for d in jl(BUNDLE / "item_catalog.jsonl")}
pop = Counter(r["item_id"] for d in jl(BUNDLE / "train_interactions.jsonl") for r in d["train_interactions"])
traits = {p["user_id"]: p.get("social_traits", {}) for p in jl(PROFILES)}
actions = {(r["model"], r["user_id"]): r["actions"] for r in jl(RUN / "actions.jsonl")}
failures = jl(RUN / "failures.jsonl")
manifest = json.loads((RUN / "run_manifest.json").read_text()) if (RUN / "run_manifest.json").exists() else {"status": "in_progress"}

def avg_rating(i):
    v = cat[i].get("average_rating")
    return float(v) if v not in (None, "") else None

def metrics(ranking, pos, ids):
    hits = [int(i in pos) for i in ranking[:K]]
    dcg = sum(h / math.log2(r + 2) for r, h in enumerate(hits))
    idcg = sum(1 / math.log2(r + 2) for r in range(min(len(pos), K)))
    return sum(hits) / len(pos), dcg / idcg

def order_by(ids, scores, key):
    idx = sorted(range(len(ids)), key=lambda j: (key(ids[j]), -scores[j], j))
    return [ids[j] for j in idx]

def policies(c, a):
    ids, sc = c["item_ids"], c["scores"]
    clk, conv = set(a["clicked_item_ids"]), set(a["converted_item_ids"])
    return {"sampled_baseline": ids,
            "click_only": order_by(ids, sc, lambda i: 0 if i in clk else 1),
            "converted_then_original": order_by(ids, sc, lambda i: 0 if i in conv else 1),
            "three_tier": order_by(ids, sc, lambda i: 0 if i in conv else (1 if i in clk else 2))}

# ---------- per-case metrics ----------
per = defaultdict(dict)   # (model,user) -> policy -> (recall, ndcg)
for key, a in actions.items():
    c = cand[key]; pos = {h["item_id"] for h in labels[key[1]]}
    for name, rk in policies(c, a).items():
        per[key][name] = metrics(rk, pos, c["item_ids"])
users_by_model = {m: sorted(u for (mm, u) in per if mm == m) for m in MODELS}

def boot(diff_by_user, n=2000):
    us = list(diff_by_user); vals = [diff_by_user[u] for u in us]
    means = sorted(st.mean(rng.choice(vals) for _ in vals) for _ in range(n))
    return st.mean(vals), means[int(0.025 * n)], means[int(0.975 * n) - 1]

out = []
P = out.append
P(f"# n1000 full condition — offline analysis\n")
P(f"Run: `{RUN.name}` · status: **{manifest.get('status')}** · completed cases: {len(actions)} / 3000 · failure rows: {len(failures)}\n")
P("Primary metrics recomputed from actions.jsonl with the repo's definitions (all held-out items are positives). "
  "CIs: user-cluster percentile bootstrap, 2,000 resamples. Cases missing because of failures are excluded per model, "
  "and the backbone is evaluated on the same cases.\n")

P("## 1. Effect vs backbone (same cases)\n")
P("| Model | Policy | n | Recall@10 | NDCG@10 | ΔRecall (95% CI) | ΔNDCG (95% CI) |")
P("|---|---|---:|---:|---:|---|---|")
pooled = defaultdict(lambda: defaultdict(list))
for m in MODELS:
    us = users_by_model[m]
    if not us: continue
    for pol in ("click_only", "converted_then_original", "three_tier"):
        r = [per[(m, u)][pol][0] for u in us]; n = [per[(m, u)][pol][1] for u in us]
        rb = [per[(m, u)]["sampled_baseline"][0] for u in us]; nb = [per[(m, u)]["sampled_baseline"][1] for u in us]
        dr = boot({u: per[(m, u)][pol][0] - per[(m, u)]["sampled_baseline"][0] for u in us})
        dn = boot({u: per[(m, u)][pol][1] - per[(m, u)]["sampled_baseline"][1] for u in us})
        for u in us:
            pooled[pol][u].append(per[(m, u)][pol][1] - per[(m, u)]["sampled_baseline"][1])
        P(f"| {m} | {pol} | {len(us)} | {st.mean(r):.4f} (base {st.mean(rb):.4f}) | {st.mean(n):.4f} (base {st.mean(nb):.4f}) | "
          f"{dr[0]:+.4f} [{dr[1]:+.4f}, {dr[2]:+.4f}] ({dr[0]/st.mean(rb)*100:+.1f}%) | "
          f"{dn[0]:+.4f} [{dn[1]:+.4f}, {dn[2]:+.4f}] ({dn[0]/st.mean(nb)*100:+.1f}%) |")
P("")
P("Pooled over backbones (each user's mean ΔNDCG across available backbones):\n")
for pol, d in pooled.items():
    b = boot({u: st.mean(v) for u, v in d.items()})
    P(f"- **{pol}**: ΔNDCG@10 {b[0]:+.4f} [{b[1]:+.4f}, {b[2]:+.4f}]")
P("")

# ---------- mechanism ----------
P("## 2. Why the conversion policy moves NDCG\n")
P("| Model | P(converted is positive) | P(backbone rank-1 is positive) | conv. original rank: median / share >10 | cases DCG up / down / same | P(pos) clicked / unclicked / slate |")
P("|---|---:|---:|---|---|---|")
bias = defaultdict(list)
for m in MODELS + ("all",):
    keys = [k for k in actions if m == "all" or k[0] == m]
    cp, t1, ranks, up, down, same, pc, pu, ps = [], [], [], 0, 0, 0, [], [], []
    for k in keys:
        a = actions[k]; ids = cand[k]["item_ids"]; pos = {h["item_id"] for h in labels[k[1]]}
        clk = set(a["clicked_item_ids"])
        if clk: pc.append(sum(i in pos for i in clk) / len(clk))
        un = [i for i in ids if i not in clk]
        if un: pu.append(sum(i in pos for i in un) / len(un))
        ps.append(sum(i in pos for i in ids) / len(ids))
        for cv in a["converted_item_ids"]:
            cp.append(cv in pos); t1.append(ids[0] in pos); ranks.append(ids.index(cv) + 1)
            d = per[k]["converted_then_original"][1] - per[k]["sampled_baseline"][1]
            up += d > 1e-12; down += d < -1e-12; same += abs(d) <= 1e-12
            if m == "all":
                bias["conv_rating"].append(avg_rating(cv)); bias["conv_pop"].append(pop[cv])
        if m == "all":
            for i in ids:
                bias["slate_rating"].append(avg_rating(i)); bias["slate_pop"].append(pop[i])
                if i in pos: bias["pos_rating"].append(avg_rating(i)); bias["pos_pop"].append(pop[i])
    if not ranks: continue
    P(f"| {m} | {st.mean(cp):.3f} | {st.mean(t1):.3f} | {st.median(ranks):.0f} / {sum(r > 10 for r in ranks)/len(ranks):.2f} | "
      f"{up} / {down} / {same} | {st.mean(pc):.3f} / {st.mean(pu):.3f} / {st.mean(ps):.3f} |")
mean = lambda xs: st.mean([x for x in xs if x is not None])
P("")
P(f"Selection bias: mean aggregate rating of converted items {mean(bias['conv_rating']):.2f} vs held-out positives "
  f"{mean(bias['pos_rating']):.2f} vs whole slate {mean(bias['slate_rating']):.2f}; train popularity (1,000-user panel) "
  f"{mean(bias['conv_pop']):.0f} vs {mean(bias['pos_pop']):.0f} vs {mean(bias['slate_pop']):.0f}.\n")
prec = defaultdict(list)
for k in actions:
    ids = cand[k]["item_ids"]; pos = {h["item_id"] for h in labels[k[1]]}
    for r, i in enumerate(ids): prec[r + 1].append(i in pos)
P("Backbone P(positive) by original rank: " + ", ".join(f"{r}:{st.mean(prec[r]):.2f}" for r in range(1, 21)) + "\n")

# ---------- behavior ----------
P("## 3. Behavior\n")
clicks = [len(a["clicked_item_ids"]) for a in actions.values()]
P(f"Mean clicks {st.mean(clicks):.2f} (median {st.median(clicks):.0f}); not_ready rate "
  f"{st.mean(a.get('watch_decision') == 'not_ready' for a in actions.values()):.3f}; zero-click cases {sum(c == 0 for c in clicks)}.\n")
al = Counter(v["alignment"] for a in actions.values() for v in a.get("candidate_assessments", {}).values())
tot = sum(al.values())
P("Alignment labels: " + ", ".join(f"{k} {v/tot:.1%}" for k, v in al.most_common()) + "\n")
oc = Counter(v["outcome"] for a in actions.values() for v in a.get("motive_assessments", {}).values())
tot = sum(oc.values())
P("Conversion-stage outcomes: " + ", ".join(f"{k} {v/tot:.1%}" for k, v in oc.most_common()) + "\n")

def trait(u, name):
    t = traits.get(u, {}).get(name, {}); return t.get("level")
P("| Trait level | Activity: mean clicks | Diversity: adjacent share of clicks | Conformity: mean |pred − avg rating| |")
P("|---|---:|---:|---:|")
for lv in (1, 2, 3):
    ac = [len(a["clicked_item_ids"]) for (m, u), a in actions.items() if trait(u, "activity") == lv]
    adj = []
    for (m, u), a in actions.items():
        if trait(u, "diversity") == lv and a["clicked_item_ids"]:
            ca = a["candidate_assessments"]
            adj.append(sum(ca[str(i)]["alignment"] == "adjacent" for i in a["clicked_item_ids"]) / len(a["clicked_item_ids"]))
    dev = []
    for (m, u), a in actions.items():
        if trait(u, "conformity") == lv:
            for i, v in a.get("motive_assessments", {}).items():
                ar = avg_rating(int(i))
                if ar is not None: dev.append(abs(v["predicted_rating"] - ar))
    f = lambda xs: f"{st.mean(xs):.3f} (n={len(xs)})" if xs else "–"
    P(f"| {lv} | {f(ac)} | {f(adj)} | {f(dev)} |")
P("\nExpected directions: clicks rise with Activity; adjacent share rises with Diversity; |pred − avg| rises with Conformity "
  "(level 1 follower → level 3 independent critic). Descriptive only; trait groups differ in histories and slates.\n")

# ---------- post-hoc policies with held-out split ----------
P("## 4. Exploratory alternative policies (split-half, not pre-registered)\n")
all_users = sorted({u for (_, u) in actions}); rng2 = random.Random(7); rng2.shuffle(all_users)
half = set(all_users[: len(all_users) // 2])
def fused(c, a, w):
    ids = c["item_ids"]; clk = set(a["clicked_item_ids"]); conv = set(a["converted_item_ids"])
    ca = a.get("candidate_assessments", {})
    def score(j):
        i = ids[j]; s = -math.log(j + 1)
        lab = ca.get(str(i), {}).get("alignment")
        s += w[0] * (i in clk) + w[1] * (i in conv) + w[2] * (lab == "strong") - w[3] * (lab == "none")
        return s
    return [ids[j] for j in sorted(range(len(ids)), key=lambda j: (-score(j), j))]
grid = [(a, b, c, d) for a in (0, .25, .5, 1) for b in (0, .25, .5, 1) for c in (0, .25, .5) for d in (0, .25, .5, 1)]
def mean_ndcg(users, w):
    vals = []
    for k, a in actions.items():
        if k[1] in users:
            pos = {h["item_id"] for h in labels[k[1]]}
            vals.append(metrics(fused(cand[k], a, w), pos, cand[k]["item_ids"])[1] - per[k]["sampled_baseline"][1])
    return st.mean(vals)
tuneA = max(grid, key=lambda w: mean_ndcg(half, w))
rest = set(all_users) - half
P(f"Score = −log(original rank) + w_click·clicked + w_conv·converted + w_strong·strong − w_none·none, grid of {len(grid)} weightings.")
P(f"Best weights on half A ({len(half)} users): {tuneA}; ΔNDCG@10 on half A {mean_ndcg(half, tuneA):+.4f}, "
  f"**on held-out half B ({len(rest)} users) {mean_ndcg(rest, tuneA):+.4f}**. "
  f"(converted_then_original on half B: {st.mean(per[k]['converted_then_original'][1]-per[k]['sampled_baseline'][1] for k in actions if k[1] in rest):+.4f})\n")
P("Use half-B numbers only as a hint; any policy carried into the paper must be fixed on a validation split, not on test labels.\n")

# ---------- failures ----------
P("## 5. Failures\n")
import re as _re
kinds = Counter(_re.sub(r"\[\d+\]", "[*]", f["error"]) for f in failures)
P(f"{len(failures)} failure rows (historical rows stay even after a case is recovered): " + "; ".join(f"{k} ×{v}" for k, v in kinds.most_common()))
P("By model: " + ", ".join(f"{m} {c}" for m, c in Counter(f["model"] for f in failures).most_common()) + "\n")
missing = [(m, u) for m in MODELS for u in sorted(labels) if (m, u) not in actions]
P(f"Cases without an action record: {len(missing)}" + (f" (e.g. {missing[:8]})" if missing else "") + "\n")

(HERE / "report_full.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
