# Project: Indirect Prompt Injection against CI/CD Agentic Workflows — Research Testbed

**Context:** Security research, 2-week scope. Goal is a reproducible testbed + a technique
success-rate matrix + passive prevalence data, for a writeup. Everything runs against
repos/agents I own. No attacking third-party systems.

## Hard rules
- Only target the local testbed repo(s) in this project. Never send payloads to external repos or live services.
- Prevalence data = read-only public GitHub API metadata (adoption counts). No exploitation of others' repos.
- Keep all API keys in `.env` (gitignored). Never hardcode or log them.

## Build, in order

1. **Repo scaffold** — `testbed/`, `harness/`, `payloads/`, `results/`, `prevalence/`,
   `README.md`, `.env.example`. Python, containerized (Dockerfile + compose). Pin deps.

2. **Testbed agents** (`testbed/`) — 3–4 minimal LLM-backed CI agents, each a separate module
   with a clean interface: `code_review`, `pr_summarizer`, `issue_triage`. Each takes repo
   content as input, calls a model via API, returns text + any tool actions. Make the model
   provider swappable (config, not hardcoded).

3. **Injection oracle** — define success concretely: agent emits a planted canary token
   (`CANARY_{uuid}`) OR calls a flagged benign tool it shouldn't. One function
   `evaluate(output) -> bool`.

4. **Payload set** (`payloads/`) — one file per vector: `issue_comment`, `pr_body`,
   `code_comment`, `readme`, `commit_msg`, `filename`, `dependency_metadata`. Each holds
   several phrasing variants. Keep payloads as data, not code.

5. **Harness** (`harness/run.py`) — matrix runner: for each (agent × payload vector × variant
   × model), inject into testbed content, run agent, call oracle, log to `results/results.csv`
   (columns: timestamp, agent, vector, variant, model, success, raw_output_path). Idempotent,
   resumable, rate-limit-aware.

6. **Prevalence** (`prevalence/`) — script hitting GitHub search API to count public repos
   using each target action/workflow. Output `prevalence/adoption.csv`. Metadata only.

7. **Reporting** — script that reads `results.csv` → success-rate pivot table (agent × vector)
   as Markdown + a simple bar chart to `results/`.

## Conventions
- Type hints, docstrings, one concern per module.
- `pytest` smoke test for the oracle and harness loop.
- Start with a 1-page plan and the scaffold; wait for my go before implementing agents.

## Sequencing
Begin with steps 1–3. Hold 4–7 until the oracle is verified.
