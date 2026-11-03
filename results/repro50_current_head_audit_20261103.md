# Current-HEAD repro50 deterministic audit (2026-11-03)

Audited commit: `c1b0c4c`

Command:

```bash
python scripts/audit_repro50.py
```

## Bundle

- Bundle ID: `14f4b04b58702ff5a9c47dd7883a91a10f72f2d428912b4ac4c844563afa6763`
- Users: 50
- Models: MF, LightGCN, MultiVAE
- Model-user cases: 150
- Candidate size: 20
- Structural and file-hash validation: passed

## Legacy replay

The fresh original-code runs for full, w/o demographics, w/o interaction history,
and w/o persona were replayed through the current bundle, reranking policies, and
metric implementation. Each condition contains 150 cases.

| Check | Full | W/o demographics | W/o history | W/o persona |
|---|---:|---:|---:|---:|
| Candidate ID/order mismatches | 0 | 0 | 0 | 0 |
| Baseline ranking mismatches | 0 | 0 | 0 | 0 |
| Click-only ranking mismatches | 0 | 0 | 0 | 0 |
| Converted-first ranking mismatches | 0 | 0 | 0 | 0 |
| Profile payload key mismatches | 0 | 0 | 0 | 0 |

- Maximum candidate-score absolute delta: `3.814697265625e-06`
- Maximum metric absolute delta: `4.996050850802902e-09`
- The score delta does not change any candidate or reranked order.

## Prompt identity

- Click prompt current/legacy SHA-256:
  `7af5392a64f8f7577bcf2f7e1262580f8f3d5039cbd3809c497d236308275b50`
- Conversion prompt current/legacy SHA-256:
  `c5d9ccd1b029ab7cda342be3b853d8a1ad151b9386cca623caa9c4dcd38e5e1e`

The deterministic pipeline therefore reproduces the original inputs, actions when
replayed, rankings, and metrics. A new live GPT-4o-mini run is still required to
measure serving-time behavioral variation. Submit it with:

```bash
sbatch scripts/reproduce_50user_ablations.sbatch
```
