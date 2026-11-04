# Run Information

Commit SHA: 56ba845baa04f204745321be5b7a70e891e64aea
Branch: jinyi/transcripts-validator-fix
Git status before: `M README.md
 M agent_reranking/cli.py
 M agent_reranking/client.py
 M agent_reranking/profiles.py
?? agent_reranking_bench.egg-info/
?? tests/test_resume_retry.py`
Git status after: `M README.md
 M agent_reranking/cli.py
 M agent_reranking/client.py
 M agent_reranking/profiles.py
?? agent_reranking_bench.egg-info/
?? tests/test_resume_retry.py`
LLM alias: gpt-4o-mini
Base URL host only: pluto-prod-hawang-llm-proxy-2026-0-0-4000.or2.colligo.dev
Temperature: 0.0; seed: 42; protocol: separated.
Current concurrency: 16; requests/minute: 500; tokens/minute: 3000000.
Initial interrupted profile attempt used concurrency 32; user authorized 16 for all subsequent steps.
Execution first timestamp (UTC): 2026-11-04T02:52:51.719512+00:00
Latest timestamp (UTC): 2026-11-04T04:26:26.883836+00:00
Shared profiles: not yet verified

| Step | All-request recorded cost (USD) | Run calls artifact cost (USD) |
|---|---:|---:|
| profiles | 0.328341 | N/A |
| full | 5.858258 | N/A |
| no_demographics | 0.000000 | N/A |
| no_persona | 0.000000 | N/A |
| no_interaction_history | 0.000000 | N/A |

Total all-request recorded cost: $6.186599.
The request ledger includes paid responses from failed validation and unsuccessful cases,
which can be omitted from calls.jsonl by the repository runner. Costs use the unchanged
repository rates ($0.15/M input and $0.60/M output tokens), not proxy invoices.
Actual proxy billing must be checked on the provider dashboard; it has not been independently verified.
Code is ec7fac9 plus the transcript/validator commit, not the handoff commit itself.
No shards were created or merged. User-authorized checkpoint/retry changes are uncommitted and fingerprinted in code_version_resume_before.json.
Unit tests use conda datasets (user-approved); see tests_resume_retry.log. Paid steps use the unchanged project .venv.
Start/end timestamps for every attempt are recorded in timeline.md.

## Transcript verification

| Step | Exchanges | Invalid validations | HTTP/transport errors | At most one sentence errors | Extras keys | Transcript bytes | Response models |
|---|---:|---:|---:|---:|---|---:|---|
| profile | 1000 | 0 | 0 | 0 | provider_specific_fields | 6315160 | gpt-4o-mini |
