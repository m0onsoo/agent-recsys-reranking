# Run from jinyi_results/:  python3 n1000_v3/analysis_quick/v3_vs_reference.py
# Compares v3 full run with the reference n1000_v2 full run (offline, no API calls).
import glob,json,math,random,statistics as st,collections
B='../agent-recsys-reranking/data/derived/ml1m_ro_n1000_seed42/'
jl=lambda p:[json.loads(l) for l in open(p) if l.strip()]
cand={(c['model'],c['user_id']):c for c in jl(B+'candidates.jsonl')}
held={d['user_id']:d['heldout_items'] for d in jl(B+'evaluation_labels.jsonl')}
cat={d['item_id']:d for d in jl(B+'item_catalog.jsonl')}
pop=collections.Counter(r['item_id'] for d in jl(B+'train_interactions.jsonl') for r in d['train_interactions'])
ar=lambda i: float(cat[i]['average_rating']) if cat[i].get('average_rating') not in (None,'') else None
REF={(r['model'],r['user_id']):r['actions'] for r in jl(glob.glob('n1000_v2/n1000_align_rating/full/runs/*/actions.jsonl')[0])}
V3={(r['model'],r['user_id']):r['actions'] for r in jl(glob.glob('n1000_v3/full/runs/*/actions.jsonl')[0])}
M=['MF','LightGCN','MultiVAE']
def ps(u,t): return {h['item_id'] for h in held[u] if h['rating']>=t}
def nd(rk,pos):
    idcg=sum(1/math.log2(r+2) for r in range(min(len(pos),10)))
    return sum(1/math.log2(r+2) for r,i in enumerate(rk[:10]) if i in pos)/idcg
def order(c,key):
    ids,sc=c['item_ids'],c['scores']; return [ids[j] for j in sorted(range(20),key=lambda j:(key(ids[j]),-sc[j],j))]
def pols(c,a,v3=False):
    clk,conv=set(a['clicked_item_ids']),set(a['converted_item_ids'])
    d={'backbone':c['item_ids'],'click':order(c,lambda i:0 if i in clk else 1),
       'click+conv':order(c,lambda i:0 if i in conv else 1),
       'three-tier':order(c,lambda i:0 if i in conv else (1 if i in clk else 2))}
    return d
def boot(v):
    rng=random.Random(42); ms=sorted(st.mean(rng.choice(v) for _ in v) for _ in range(2000)); return st.mean(v),ms[50],ms[1949]
for t,name in ((1,'all'),(3,'>=3'),(4,'>=4')):
    print(f'=== positives {name}')
    for lab,A in (('ref',REF),('v3',V3)):
        row=[]
        for p in ('click','click+conv','three-tier'):
            per=collections.defaultdict(list); pm={}
            for m in M:
                vals=[]
                for (mm,u),a in A.items():
                    if mm!=m: continue
                    pos=ps(u,t)
                    if not pos: continue
                    P=pols(cand[(m,u)],a); b=nd(P['backbone'],pos); x=nd(P[p],pos)
                    vals.append((b,x)); per[u].append(x-b)
                pm[m]=(st.mean(x for _,x in vals)/st.mean(b for b,_ in vals)-1)*100
            bt=boot([st.mean(v) for v in per.values()])
            row.append(f"{p}: MF {pm['MF']:+.2f}% LG {pm['LightGCN']:+.2f}% MV {pm['MultiVAE']:+.2f}% pooled {bt[0]:+.4f} [{bt[1]:+.4f},{bt[2]:+.4f}]")
        print(' ',lab,' | '.join(row))
    # paired v3-ref for click+conv
    per=collections.defaultdict(list)
    for k in V3:
        if k not in REF: continue
        pos=ps(k[1],t)
        if not pos: continue
        per[k[1]].append(nd(pols(cand[k],V3[k])['click+conv'],pos)-nd(pols(cand[k],REF[k])['click+conv'],pos))
    print('  paired v3-ref click+conv', '%+.4f [%+.4f,%+.4f]'%boot([st.mean(v) for v in per.values()]))
# diagnostics
for lab,A in (('ref',REF),('v3',V3)):
    cp=t1=0;n=0;rt=[];pp=[];top=0;clicks=[];nr=0
    for (m,u),a in A.items():
        ids=cand[(m,u)]['item_ids']; pos=ps(u,1); clicks.append(len(a['clicked_item_ids'])); nr+=a.get('watch_decision')=='not_ready'
        for c in a['converted_item_ids']:
            n+=1; cp+=c in pos; t1+=ids[0] in pos; rt.append(ar(c)); pp.append(pop[c]); top+= ar(c)==max(ar(x) or 0 for x in ids)
    print(lab,f'conv precision {cp/n:.3f} vs rank1 {t1/n:.3f} | conv rating {st.mean(x for x in rt if x):.2f} pop {st.mean(pp):.0f} top-rated {top/n:.1%} | clicks {st.mean(clicks):.2f} not_ready {nr/len(A):.1%}')
# position of conversions (backbone rank) in v3
r=collections.Counter()
for (m,u),a in V3.items():
    for c in a['converted_item_ids']: r[cand[(m,u)]['item_ids'].index(c)+1]+=1
tot=sum(r.values()); print('v3 conv by backbone rank (1..20):',' '.join(f'{k}:{r[k]/tot:.2f}' for k in range(1,21)))
