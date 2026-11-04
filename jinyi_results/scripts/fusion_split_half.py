# Run from jinyi_results/:  python3 n1000_v3/analysis_quick/fusion_split_half.py
# Split-half score fusion: score = -log(backbone rank) + w0*label + w1*clicked + w2*converted.
# label = interest-3 for v3; (strong) - (none) for the reference. Users split with seed 7.
import os, math, random, statistics as st
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "v3_vs_reference.py")).read().split("for t,name in")[0]
exec(src)
users = sorted({u for (_, u) in V3}); rng = random.Random(7); rng.shuffle(users)
A, Bh = set(users[:500]), set(users[500:])
def fused(c, a, w, v3):
    ids = c["item_ids"]; clk = set(a["clicked_item_ids"]); conv = set(a["converted_item_ids"]); ca = a["candidate_assessments"]
    def s(j):
        i = ids[j]; x = -math.log(j + 1) + w[1] * (i in clk) + w[2] * (i in conv)
        if v3: x += w[0] * (ca[str(i)]["interest"] - 3)
        else:
            lab = ca[str(i)]["alignment"]; x += w[0] * ((lab == "strong") - (lab == "none"))
        return x
    return [ids[j] for j in sorted(range(20), key=lambda j: (-s(j), j))]
grid = [(a, b, c) for a in (0, .1, .2, .35, .5) for b in (0, .15, .3, .5) for c in (0, .25, .5, 1)]
def score(S, w, acts, v3):
    return st.mean(nd(fused(cand[k], a, w, v3), ps(k[1], 1)) - nd(cand[k]["item_ids"], ps(k[1], 1)) for k, a in acts.items() if k[1] in S)
for lab, acts, v3 in (("reference", REF, False), ("v3", V3, True)):
    for tr, te, nm in ((A, Bh, "A->B"), (Bh, A, "B->A")):
        w = max(grid, key=lambda w: score(tr, w, acts, v3))
        print(lab, nm, "weights", w, "train %+.4f test %+.4f" % (score(tr, w, acts, v3), score(te, w, acts, v3)))
