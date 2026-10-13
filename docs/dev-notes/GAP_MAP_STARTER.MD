# Gap-Map (Starter Baseline): Indirect Prompt Injection against CI/CD Agentic Workflows

**Purpose:** A hand-built baseline for Claude Code to *check and extend*, not build from scratch.
Covers the 5 core works + 3 context pieces as of late July 2026. Distinguishes verified facts
from items marked **(confirm)**. Paraphrased throughout; see arXiv IDs for primary sources.

---

## ⚠️ Reality check (read first)
The core question — *"can untrusted repo content hijack an LLM agent wired into GitHub Actions?"* —
is now **answered and crowded**. Three 2026 papers plus an industry disclosure already cover it:
- **Existence + optimized attack + disclosure:** JAW / "Comment and Control."
- **Live open-source attack framework:** GitInject (released, provisions real repos).
- **Large-scale static prevalence:** AWI / TaintAWI (13,392 workflows).
- **Confirmed real-world impact:** Aikido "PromptPwnd" (Fortune 500, Google patched Gemini CLI in 4 days).

So the original differentiators ("reproducible testbed — JAW didn't release one"; "measure prevalence")
are **weaker than they were two months ago.** GitInject released a testbed; AWI did the measurement.
The open lane is narrower and more specific — see **Open-Lane Shortlist** below.

---

## Reference list (starter)

| # | Short name | Full title | Venue / ID | Group |
|---|-----------|-----------|-----------|-------|
| R1 | **JAW / Comment and Control** | Comment and Control: Hijacking Agentic Workflows via Context-Grounded Evolution | arXiv:2605.11229 (2026) | Cao (JHU) et al. |
| R2 | **GitInject** | GitInject: Real-World Prompt Injection Attacks in AI-Powered CI/CD Pipelines | arXiv:2606.09935 (2026) | Isbarov, Suleymanov, Shumailov, Kantarcioglu (VT) |
| R3 | **AWI / TaintAWI** | Demystifying and Detecting Agentic Workflow Injection Vulnerabilities in GitHub Actions | arXiv:2605.07135 (2026) | Shenao Wang, Haoyu Wang et al. |
| R4 | **Time for Actions** | Time for Actions: A Longitudinal Study of the GitHub Actions Marketplace | IEEE SecDev 2025 | Chaiwut & Nikiforakis (Stony Brook) |
| R5 | **WebInject (+line)** | WebInject: Prompt Injection Attack to Web Agents (+ WebSentinel, Tool-Selection, DataSentinel, PromptLocate) | EMNLP 2025 / arXiv:2602.03792 / NDSS 2026 / S&P 2025–26 | Gong (Duke) et al. |
| C1 | *PromptPwnd* (context) | PromptPwnd: Prompt Injection in AI-Powered GitHub Actions | Aikido Security blog (2026) | Industry |
| C2 | *CSA note* (context) | AI GitHub Actions Security research note (maps to OWASP CICD-SEC-4) | Cloud Security Alliance (2026) | Industry |
| C3 | *AI Bots Reliability* (context) | Reliability of AI Bots' Footprints in GitHub Actions CI/CD Workflows | arXiv:2604.18334 (2026) | Academic (reliability, not security) |

---

## Per-paper cards

### R1 — JAW / "Comment and Control" (arXiv:2605.11229)
- **Threat model:** attacker submits a crafted **GitHub issue comment** (context-grounded); target = LLM agent in an agentic workflow (GitHub Actions **and** n8n).
- **Method:** "Context-Grounded Evolution" — evolves payloads against the workflow context. Detection **and** exploitation framework.
- **Scale / result:** identifies **4,174 hijackable GitHub workflows + 8 n8n templates**; impacts incl. credential leakage; spans ~15 popular actions (Claude Code, Gemini CLI, Qwen CLI, Cursor CLI). Bounties from GitHub, Google, Anthropic, Snowflake.
- **Artifact released:** framework described; public release status **(confirm)**.
- **What it does NOT do:** clean per-model susceptibility *rate* comparison; under-studied vectors beyond comment context.

### R2 — GitInject (arXiv:2606.09935)
- **Threat model:** attacker controls PR / config content; target = live CI agent with elevated repo permissions. GitHub **and** GitLab.
- **Method:** **live** framework — provisions ephemeral repos and triggers **real workflow runs** (not simulated tool calls), so credential/permission behavior is production-accurate.
- **Scale / result:** 4 AI providers; **11 named attacks across 4 classes** (config-file injection, credential exfiltration, judgment manipulation, availability). All providers vulnerable in default config. Key claim: the worst bugs are **structural** (how CI handles credentials/config), **not model-specific**.
- **Artifact released:** **YES** — open-source (github.com/ceferisbarov/GitInject). Ships workflow defs, dataset, utility+security tests.
- **Mitigations:** identifies **minimum-cost workflow-level countermeasure** per attack class.
- **What it does NOT do:** per-model susceptibility rates (explicitly de-emphasizes model as the variable); large-scale prevalence; "quiet" content vectors.

### R3 — AWI / TaintAWI (arXiv:2605.07135)
- **Threat model:** untrusted **event context** (issue bodies, PR descriptions, comments) flows into agent prompts / agent-consumed inputs.
- **Concepts:** "Agentic Workflow Injection (AWI)"; two patterns — **Prompt-to-Agent (P2A)** and **Prompt-to-Script (P2S)**.
- **Method:** **static taint analysis** (TaintAWI); characterized 1,033 AI-assisted actions to build taint specs.
- **Scale / result:** 13,392 workflows / 10,792 repos → 519 potential, **496 confirmed** exploitable, **95.6% precision**, **343 previously-unknown zero-days**; disclosed 187, 24 accepted **(confirm counts)**.
- **Artifact released:** TaintAWI tool — release status **(confirm)**.
- **What it does NOT do:** it's **static** — never runs the models, so **no empirical model-susceptibility data**; no runtime defense eval.

### R4 — Time for Actions (SecDev 2025)
- **Scope:** longitudinal measurement of the **GitHub Actions Marketplace** (supply-chain hygiene), **not** AI/injection.
- **Scale / result:** collected **23,757 Actions** (weekly crawl Dec 2024–Apr 2025); poor adoption of SHA pinning / creator verification.
- **Use to you:** template + citation for the **passive prevalence** methodology; supply-chain framing.

### R5 — WebInject and Gong's PI line
- **Domain:** **web agents**, not CI/CD. WebInject = pixel/HTML injection into MLLM web agents.
- **Line:** WebSentinel (detect/localize, arXiv:2602.03792), Prompt Injection to Tool Selection (NDSS 2026), Formalizing & Benchmarking PI (USENIX Sec 2024), DataSentinel (S&P 2025), PromptLocate (S&P 2026).
- **Use to you:** the **benchmarking + attack/defense-eval methodology** to borrow — this is the closest thing to a rigorous *success-rate* template, just in the wrong domain (port it to CI/CD).

---

## Coverage matrix — injection vector × paper
`✓ = covered/primary · ~ = partial/secondary · ✗ = out of scope · ? = confirm`

| Injection vector | R1 JAW | R2 GitInject | R3 AWI | R4 Actions | R5 WebInject |
|---|---|---|---|---|---|
| issue_comment | ✓ | ~ | ✓ | ✗ | ✗ |
| pr_body / description | ~ | ✓ | ✓ | ✗ | ✗ |
| config_file (agent config) | ~ | ✓ | ~ | ✗ | ✗ |
| commit_msg | ? | ~ | ~ | ✗ | ✗ |
| code_comment | ? | ? | ~ | ✗ | ✗ |
| readme / repo docs | ? | ? | ~ | ✗ | ✗ |
| filename | ✗? | ✗? | ✗? | ✗ | ✗ |
| dependency_metadata | ✗? | ✗? | ✗? | ✗ | ✗ |
| webpage (pixel/HTML) | ✗ | ✗ | ✗ | ✗ | ✓ |

**Empty-ish rows = candidate open vectors:** `filename`, `dependency_metadata`, and (largely) `code_comment` / `readme` are under-studied as carriers in the CI/CD setting.

---

## Axis matrix — paper × dimension

| Dimension | R1 JAW | R2 GitInject | R3 AWI | R4 Actions | R5 WebInject |
|---|---|---|---|---|---|
| Domain | GH Actions + n8n | GH + GitLab CI | GH Actions | GH Marketplace | Web agents |
| Live execution vs static/sim | Live | **Live (real runs)** | **Static taint** | Crawl | Datasets/sim |
| # providers/agents | ~15 actions | 4 providers | 1,033 actions (chars.) | 23,757 actions | MLLM web agents |
| **Per-model susceptibility RATE** | ~ | ✗ (structural) | ✗ (static) | ✗ | ✓ (web domain) |
| Reproducible artifact released | ? | **✓** | ? | ? | ~ |
| Mitigation proposed | ~ | **✓** | detection | rec. | ✓ (sep. papers) |
| Large-scale prevalence | ✓ (4,174) | ✗ | **✓ (13,392)** | ✓ (23,757) | ✗ |

---

## Open-Lane Shortlist (ranked for a 2-week solo testbed study)

1. **Controlled technique × model × vector SUCCESS-RATE matrix.** *(OPEN — best fit.)*
   No one reports clean per-model susceptibility rates in the CI/CD agent setting: GitInject calls
   vulns "structural, not model-specific" and reports binary/default-config outcomes; AWI is static
   and never runs models; Gong has the rate methodology but in the web-agent domain. **Your contribution:**
   port Gong-style benchmarking to CI agents — hold vector/agent fixed, vary phrasing technique and
   model, report success *rates*. This is the empirical data all four CI/CD works lack.

2. **"Quiet vector" emphasis.** *(OPEN / under-studied.)*
   Prior work centers issue comments, PR bodies, config files. Systematically test **dependency_metadata
   (package names/descriptions/changelogs), filenames, and code comments** as injection carriers into
   review/triage agents. Pairs naturally with Lane 1 as the "vector" axis.

3. **Runtime defense evaluation in the CI setting.** *(OPEN.)*
   AWI detects statically; nobody has measured how much **prompt-level defenses** (spotlighting,
   delimiting, data/instruction separation, guard models à la WebSentinel/WebAgentGuard) reduce
   success *rate* for CI agents specifically. Adds a defense column to your matrix.

4. **Post-patch reproduction / short longitudinal.** *(OPEN, modest, very 2-wk-friendly.)*
   Vendors patch fast (Google fixed Gemini CLI in 4 days per Aikido). Re-test whether documented
   JAW/GitInject/PromptPwnd attack classes still fire after patches. Lower novelty ceiling but low risk.

### CLOSED — do not pitch these as novel
- ❌ "GitHub Actions AI agents can be prompt-injected at all" → R1, R2, R3, C1.
- ❌ "Large-scale static prevalence of injectable workflows" → R3 (13,392).
- ❌ "An open live-repo attack framework" → R2 released one.
- ❌ "Marketplace supply-chain hygiene (SHA pinning)" → R4.

---

## Revised project framing (recommended)
Combine **Lane 1 + Lane 2** (optionally **+ Lane 3**):

> *A controlled susceptibility study measuring how indirect-injection success **rate** varies across
> phrasing technique × model × injection vector for CI/CD review/triage/summarizer agents — including
> under-studied "quiet" vectors (dependency metadata, filenames, code comments) — providing the
> empirical model-level data that GitInject (structural/binary) and AWI (static detection) do not
> report, and optionally quantifying how much runtime prompt-level defenses shrink that rate.*

Position explicitly as **complementary** to R2/R3, borrowing R5's benchmarking rigor. Keep it to a
tight grid (e.g., 3 agents × 2 models × 6 vectors × N phrasings) so it finishes in the window.

---

## Instructions for Claude Code (extend this baseline)
1. Ingest `refs/` (PDFs of R1–R5 + C1–C3) — **do not web-search or invent citations**; work only from provided sources.
2. **Verify every `(confirm)` cell** against the PDFs; correct any cell I got wrong and cite the exact paper/section.
3. Add any **2026 works I missed** *only if I place their PDF in `refs/`* (e.g., WASP, EIA, AgentDojo, SecureWebArena, BrowseSafe — web-agent side; ARGUS, COSSETER — CI taint/least-privilege side).
4. Regenerate the **coverage matrix** and **axis matrix** from the verified cards.
5. Output `refs/gap_map.md` with an updated **Open-Lane Shortlist**, and flag any lane above that a
   newly-added paper has since **closed**.
6. Distinguish "not covered" from "unknown/couldn't tell." No speculation about unpublished work.
