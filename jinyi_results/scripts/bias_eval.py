#!/usr/bin/env python3
"""Offline bias checks for the n1000 run (no API calls).
1) Re-evaluate all conditions/policies with positives = all held-out, rating>=3, rating>=4.
2) Precision of the converted item vs backbone rank-1 under each definition.
3) Position bias: conversion rate by original backbone rank.
4) Rating/popularity bias of conversions.  Writes bias_eval.json and prints a summary."""
import glob, json, math, random, statistics as st
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
B = ROOT.parent.parent / "agent-recsys-reranking/data/derived/ml1m_ro_n1000_seed42"
jl = lambda p: [json.loads(l) for l in open(p) if l.strip()]
cand = {(c["model"], c["user_id"]): c for c in jl(B / "candidates.jsonl")}
held = {d["user_id"]: d["heldout_items"] for d in jl(B / "evaluation_labels.jsonl")}
cat = {d["item_id"]: d for d in jl(B / "item_catalog.jsonl")}
pop = Counter(r["item_id"] for d in jl(B / "train_interactions.jsonl") for r in d["train_interactions"])
CONDS = ["full", "no_demographics", "no_persona", "no_interaction_history"]
MODELS = ["MF", "LightGCN", "MultiVAE"]
DEFS = {"all": 1, "ge3": 3, "ge4": 4}
def posset(u, t): return {h["item_id"] for h in held[u] if h["rating"] >= t}
def ndcg(rk, pos):
    idcg = sum(1 / math.log2(r + 2) for r in range(min(len(pos), 10)))
    return sum(1 / math.log2(r + 2) for r, i in enumerate(rk[:10]) if i in pos) / idcg
def recall(rk, pos): return sum(i in pos for i in rk[:10]) / len(pos)
def order(c, key):
    ids, sc = c["item_ids"], c["scores"]
    return [ids[j] for j in sorted(range(len(ids)), key=lambda j: (key(ids[j]), -sc[j], j))]
def pols(c, a):
    clk, conv = set(a["clicked_item_ids"]), set(a["converted_item_ids"])
    return {"backbone": c["item_ids"], "click": order(c, lambda i: 0 if i in clk else 1),
            "click+conversion": order(c, lambda i: 0 if i in conv else 1),
            "three-tier": order(c, lambda i: 0 if i in conv else (1 if i in clk else 2))}
def boot(vals, n=2000):
    rng = random.Random(42); ms = sorted(st.mean(rng.choice(vals) for _ in vals) for _ in range(n))
    return st.mean(vals), ms[int(.025 * n)], ms[int(.975 * n) - 1]
res = {"eval": {}, "precision": {}, "position": {}, "selection": {}}
for c in CONDS:
    acts = {(r["model"], r["user_id"]): r["actions"] for r in jl(glob.glob(str(ROOT / f"n1000_align_rating/{c}/runs/*/actions.jsonl"))[0])}
    for dname, t in DEFS.items():
        per = defaultdict(lambda: defaultdict(dict)); n_users = set()
        for (m, u), a in acts.items():
            pos = posset(u, t)
            if not pos: continue
            n_users.add(u)
            for p, rk in pols(cand[(m, u)], a).items():
                per[(m, u)][p] = (recall(rk, pos), ndcg(rk, pos))
        out = {"users": len(n_users)}
        for m in MODELS:
            ks = [k for k in per if k[0] == m]
            out[m] = {p: {"recall": st.mean(per[k][p][0] for k in ks), "ndcg": st.mean(per[k][p][1] for k in ks)} for p in ("backbone", "click", "click+conversion", "three-tier")}
        for p in ("click", "click+conversion", "three-tier"):
            byu = defaultdict(list)
            for (m, u), d in per.items(): byu[u].append(d[p][1] - d["backbone"][1])
            out[f"pooled_{p}"] = boot([st.mean(v) for v in byu.values()])
        res["eval"][f"{c}|{dname}"] = out
    if c == "full":
        for dname, t in DEFS.items():
            cp, t1 = [], []
            for (m, u), a in acts.items():
                pos = posset(u, t)
                for cv in a["converted_item_ids"]:
                    cp.append(cv in pos); t1.append(cand[(m, u)]["item_ids"][0] in pos)
            res["precision"][dname] = {"converted": st.mean(cp), "rank1": st.mean(t1)}
        byr = defaultdict(lambda: [0, 0, 0])
        for (m, u), a in acts.items():
            pos = posset(u, 1)
            for r, i in enumerate(cand[(m, u)]["item_ids"]):
                byr[r + 1][0] += 1; byr[r + 1][1] += i in a["converted_item_ids"]; byr[r + 1][2] += i in pos
        res["position"] = {r: {"conversion_rate": v[1] / v[0], "positive_rate": v[2] / v[0]} for r, v in sorted(byr.items())}
(HERE / "bias_eval.json").write_text(json.dumps(res, indent=1))
for k, v in res["eval"].items():
    line = f"{k:32s} users={v['users']:4d} " + " ".join(
        f"{m}: base {v[m]['backbone']['ndcg']:.4f} c+c {v[m]['click+conversion']['ndcg']:.4f} ({(v[m]['click+conversion']['ndcg']/v[m]['backbone']['ndcg']-1)*100:+.2f}%)" for m in MODELS)
    pc = v["pooled_click+conversion"]
    print(line, f"| pooled c+c {pc[0]:+.4f} [{pc[1]:+.4f},{pc[2]:+.4f}]")
print("precision", json.dumps(res["precision"]))
print("position", {r: (round(v['conversion_rate'], 3), round(v['positive_rate'], 3)) for r, v in res["position"].items()})
