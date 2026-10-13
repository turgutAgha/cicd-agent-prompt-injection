# Gap-Map (Verified): Indirect Prompt Injection against CI/CD Agentic Workflows

**Status:** Extended and fact-checked by Claude Code against the PDFs in `refs/`.
**Method:** Every `(confirm)` cell in the starter was checked against the extracted paper text
(one reader per paper; verbatim quotes required). Sources = `refs/*.pdf` only; no web search, no
outside knowledge. Cells are tagged **VERIFIED**, **CORRECTED**, or **UNVERIFIABLE (no source)**.

**Sources actually present in `refs/` (8 PDFs):** R1_JAW, R2_GitInject, R3_AWI_TaintAWI,
R4_TimeForActions, R5_WebInject, R5b_WebSentinel, R5c_ToolSelection, C3_AIBotsReliability.
**Not provided (cannot verify):** C1 *PromptPwnd* (Aikido blog) and C2 *CSA note* — **no PDF in
`refs/`**, so every claim resting on them is marked UNVERIFIABLE below. Per the rules, they were not
web-searched.

---

## ⚠️ Corrections to the starter baseline (read first)

These are the material changes the PDFs force. Several weaken *or* reshape the starter's framing.

1. **The starter's headline gap is overstated. GitInject (R2) DOES report per-model rates.**
   R2 Table 3 ("Model performance by injection pathway") gives explicit per-model fractions —
   `claude-sonnet-4-5` 0/4 (PR/issue body) & 2/2 (config-file), `gpt-4o-mini` 2/2 & 2/2,
   `gemini-3.1-pro-preview` 0/4 & 2/2, etc. So "no one reports clean per-model susceptibility rates
   in the CI/CD setting" is **not true as written.** What remains genuinely open is *finer-grained,
   phrasing-technique-varied* rates — R2's numbers are small-N (denominators 1–4), per **pathway**
   (two of them), and deliberately framed as "structural, not model-specific." Lane 1 survives only
   in this narrowed form (see below).

2. **"JAW didn't release a testbed" is FALSE.** R1 releases artifacts — "All artifacts are available
   at https://anonymous.4open.science/r/agentic-workflow-hijacking-BBD2" — comprising the full JAW
   implementation, a dataset of confirmed vulnerable Actions/n8n workflows, and the jailbreak
   payloads (some withheld pending disclosure). It is an anonymized 4open.science repo, not a public
   GitHub, but code + data + payloads are released.

3. **AWI/TaintAWI (R3) does NOT state an artifact release.** No "we release," no TaintAWI repo URL
   anywhere in the text (implementation is described at ~4.5 KLoC; the only GitHub URLs are
   third-party actions in the reference list). Starter's "?" resolves to **not stated in paper**, not
   "released." So the starter's "AWI did the measurement [and released]" pairing is half-right:
   AWI did the large-scale measurement; it did not (per the paper) release the tool.

4. **R4 venue "IEEE SecDev 2025" is UNVERIFIABLE from the PDF** — no venue string appears in the
   text. Treat the venue as unconfirmed; everything else in R4 checks out.

5. **WebSentinel's arXiv ID `2602.03792` is wrong / not in the source.** The R5b text prints only a
   repo URL, `https://github.com/wxl-lxw/WebSentinel`, and no self arXiv ID. Do not cite that number.

6. **R5c title/system corrected.** Printed title is "Prompt Injection Attack to Tool Selection **in
   LLM Agents**"; the attack/system is named **ToolHijacker**; `arXiv:2504.19793v3`; **NDSS 2026**
   (all verified). It is general LLM-agent tool-selection, not "web agents" specifically.

7. **Author/affiliation fixes:** R1 is JHU-centric with **co-first authors Neil Fendley & Zhengyu
   Liu** (Yinzhi Cao is last author) — "Cao et al." is last-author shorthand only. R2's **Ilia
   Shumailov is not Virginia Tech** ("AI Sequrity Company, London, UK" [sic]); the other three are VT.

8. **C1 (PromptPwnd) claims are UNVERIFIABLE here** — the "Fortune 500 / Google patched Gemini CLI in
   4 days" reality-check items have no PDF in `refs/`. Do not present them as established.

---

## Reference list (verified)

| # | Short name | Full title (as printed) | ID / venue (verified) | Group |
|---|-----------|------------------------|----------------------|-------|
| R1 | **JAW / Comment and Control** | Comment and Control: Hijacking Agentic Workflows via Context-Grounded Evolution | arXiv:2605.11229v1 (11 May 2026) | Fendley, Liu, Guan, Zhong, Cao — JHU (+ Wyze Labs) |
| R2 | **GitInject** | GitInject: Real-World Prompt Injection Attacks in AI-Powered CI/CD Pipelines | arXiv:2606.09935v1 (7 Jun 2026) | Isbarov, Suleymanov, Kantarcioglu (VT) + Shumailov (indep.) |
| R3 | **AWI / TaintAWI** | Demystifying and Detecting Agentic Workflow Injection Vulnerabilities in GitHub Actions | arXiv:2605.07135v1 (8 May 2026) | S. Wang … H. Wang et al. |
| R4 | **Time for Actions** | Time for Actions: A Longitudinal Study of the GitHub Actions Marketplace | **venue UNVERIFIED** in PDF | Chaiwut & Nikiforakis (Stony Brook) |
| R5 | **WebInject** | WebInject: Prompt Injection Attack to Web Agents | EMNLP 2025 (pp. 2010–2030) | Gong et al. (Duke) |
| R5b | **WebSentinel** | WebSentinel: Detecting and Localizing Prompt Injection Attacks for Web Agents | repo only: github.com/wxl-lxw/WebSentinel; **no arXiv ID in text** | (web-agent defense) |
| R5c | **ToolHijacker** | Prompt Injection Attack to Tool Selection in LLM Agents | arXiv:2504.19793v3; NDSS 2026 | (LLM tool-selection) |
| C3 | *AI Bots Reliability* (context) | Reliability of AI Bots Footprints in GitHub Actions CI/CD Workflows | arXiv:2604.18334v1 (20 Apr 2026); MSR '26 | LUMS (Pakistan) |
| C1 | *PromptPwnd* (context) | — | **NO PDF — unverifiable** | Aikido (industry) |
| C2 | *CSA note* (context) | — | **NO PDF — unverifiable** | CSA (industry) |

---

## Per-paper cards (verified)

### R1 — JAW / "Comment and Control" (arXiv:2605.11229) — VERIFIED
- **Threat model:** external unprivileged attacker submits crafted **GitHub issue comments** to
  manipulate the LLM agent; covers **GitHub Actions AND n8n**. ✓
- **Method:** JAW = "first detection **and** exploitation framework" via **Context-Grounded
  Evolution** (evolves inputs under contexts from hybrid program analysis). ✓
- **Scale/result:** **4,174** hijackable GitHub workflows + **8** n8n templates; credential leakage;
  spans **15** widely-used Actions incl. Claude Code, Gemini CLI, Qwen CLI, Cursor CLI; bounties from
  GitHub, Google, Anthropic, Snowflake. ✓
- **Artifact:** **RELEASED (anonymized)** — full impl + dataset + payloads at anonymous.4open.science
  (some payloads withheld pending disclosure). ← *corrects starter "(confirm)".*
- **Per-model RATES:** **NO clean % rates.** Table 3 reports the *average number of adaptive jailbreak
  iterations* to bypass defenses ("F" = failure), not success percentages. ← *corrects starter "~".*
- **Does NOT do:** per-model susceptibility *rates*; extension beyond GitHub Actions/n8n is future work.

### R2 — GitInject (arXiv:2606.09935) — VERIFIED w/ corrections
- **Threat model:** attacker controls PR/config content; target = live CI agent holding
  `GITHUB_TOKEN` write access; **GitHub (evaluated) + GitLab (confirmed port, Appendix)**. ✓
- **Method:** **LIVE** — provisions ephemeral repos, triggers **real workflow runs** (not simulated
  tool calls). ✓
- **Scale/result:** 4 providers (Claude, OpenAI Codex, Gemini, Cline); **11 named attacks / 4 classes**
  (config-file injection, credential exfiltration, judgment manipulation, availability); every provider
  vulnerable in default config. ✓
- **Structural claim:** worst bugs are **structural** (credential/config handling), **not
  model-specific** (§6.1). ✓
- **Artifact:** public — **github.com/ceferisbarov/GitInject**; ships workflow defs + StateEvaluator
  (security) + LLMEvaluator (utility). The word **"dataset" is not used** — it's a framework. ✓ (minor
  correction to starter wording)
- **Per-model rates:** **REPORTED** (Table 3 / Table 5, per model × pathway, small-N). ← *corrects
  starter "✗".*
- **Mitigations:** minimum-cost workflow-level countermeasure per attack class. ✓
- **Does NOT do:** exhaustive vector coverage or prevalence; some scenarios modeled but "not
  empirically tested."

### R3 — AWI / TaintAWI (arXiv:2605.07135) — ALL NUMBERS VERIFIED
- **Threat model:** untrusted event context (issue bodies, PR descriptions, comments) → agent
  prompts / agent-consumed inputs. ✓
- **Concepts:** Agentic Workflow Injection; **P2A** (Prompt-to-Agent) and **P2S** (Prompt-to-Script). ✓
- **Method:** **static taint analysis** (TaintAWI); characterized **1,033** AI-assisted actions. ✓
- **Numbers (all verbatim-verified):** 13,392 workflows · 10,792 repos · 519 potential · **496
  confirmed** · **95.6% precision** · **343 zero-days** · **187 disclosed** · **24 accepted/fixed**
  (26 maintainer responses). ✓
- **Artifact:** **NOT STATED** in paper (no release claim / no tool URL). ← *corrects starter "(confirm)".*
- **Static only:** never executes models → **no empirical model-susceptibility data**; no runtime
  defense evaluation. ✓
- **Does NOT do:** dynamic/model-in-the-loop testing; non-LLM GHA bugs are explicitly out of scope.

### R4 — Time for Actions — VERIFIED (venue excepted)
- **Scope:** longitudinal measurement of the **GitHub Actions Marketplace** (supply-chain hygiene);
  **no AI / prompt-injection content at all** (verified absent). ✓
- **Scale:** **23,757** Actions; weekly crawl **Dec 18 2024 – Apr 9 2025**. ✓
- **Findings:** poor SHA-pinning; ~4.3% verified creators (95%+ non-verified); typosquatting +
  dangling remote references. ✓
- **Use to you:** clean **passive-prevalence methodology** template (weekly registry crawl, hygiene
  metrics at population scale). **Venue "SecDev 2025" unconfirmed in PDF.**

### R5 line — WebInject / WebSentinel / ToolHijacker — VERIFIED (web/general-agent domain)
- **WebInject (EMNLP 2025):** MLLM **web agents**; pixel/HTML injection; **reports per-agent ASR**
  (Table 1: UI-TARS 0.975, Phi-4 0.963, Llama-3.2 0.972, Qwen-2.5 0.970, Gemma-3 0.972). ✓
- **WebSentinel:** **defense** — detects & localizes PI for web agents (repo only; no arXiv ID in
  text). ✓
- **ToolHijacker (NDSS 2026, arXiv:2504.19793v3):** PI to **tool selection** in general LLM agents;
  tests **8 LLMs × 4 retrievers**, formal ASR/AHR metrics; MetaTool/ToolBench. ✓
- **Use to you:** the closest thing to a rigorous **ASR-benchmarking template** (vary technique ×
  model, measure ASR) — **domain is web/general-agent, not CI/CD**; port the method, not the results.

### C3 — AI Bots Reliability (arXiv:2604.18334, MSR '26) — context only
- **Reliability, not security** (verified): CI workflow success rate of 5 bots (Claude, Devin, Cursor,
  Copilot, Codex) over **61,837 runs / 2,355 repos**; Claude lowest (64.86%), Codex highest (94.44%).
  **No prompt-injection/attack content.** Use only as evidence that these agents actively run in CI.

---

## Coverage matrix — injection vector × paper (regenerated, verified)
`✓ = primary/clearly studied · ~ = partial/mentioned or as sink only · ✗ = not covered`
(Only the CI/CD papers R1–R3 carry vectors; R4/R5/C3 are ✗ by domain and omitted.)

| Injection vector | R1 JAW | R2 GitInject | R3 AWI | Change vs starter |
|---|---|---|---|---|
| issue_comment | ✓ | ✓ | ✓ | — |
| pr_body / description | ✓ | ✓ | ✓ | R1 ~→✓ |
| config_file (agent config) | ✗ | ✓ | ~ (sink only) | R1 ~→✗; R3 clarified as P2S **sink**, not source |
| commit_msg | ~ | ✗ | ✓ | R1 ?→~; R2 ~→✗; **R3 ?→✓ (head_commit.message is a taint source)** |
| code_comment | ✗ | ~ (via CLAUDE.md, not the comment) | ✗ | R1 ?→✗; R2 ?→~; R3 ~→✗ |
| readme / repo docs | ✗ | ~ (repo-instruction .md; README not tested) | ✗ | R1 ?→✗; R2 ?→~; R3 ~→✗ |
| filename | ~ (listed in R1 Table 5, no result) | ✗ | ✗ | **R1 ✗?→~**; R2/R3 ✗ |
| dependency_metadata | ✗ | ✗ | ✗ | confirmed ✗ everywhere |
| webpage (pixel/HTML) | ✗ | ✗ | ✗ | covered only by R5 (web domain) |

**Open vectors (empirically, with rates):** `dependency_metadata` (✗ across all three — fully open),
`filename` (only *named* in R1, never tested), `code_comment` and `readme` (only *incidental* in R2 via
config files, never isolated as carriers). **`commit_msg` is now a known source (R3)** — drop it from
any "novel vector" pitch; it's open only for *empirical rates*, not novelty.

---

## Axis matrix — paper × dimension (regenerated, verified)

| Dimension | R1 JAW | R2 GitInject | R3 AWI | R4 Actions | R5 line |
|---|---|---|---|---|---|
| Domain | GH Actions + n8n | GH + GitLab CI | GH Actions | GH Marketplace | Web / tool-use agents |
| Execution model | Live (evolutionary) | **Live (real runs)** | **Static taint** | Weekly crawl | Datasets / live agents |
| Breadth | 15 actions | 4 providers | 1,033 actions (chars.) | 23,757 actions | 5–8 models |
| **Per-model susceptibility RATE** | ✗ (iteration counts, not %) | **~ (per model × pathway, small-N)** | ✗ (static) | ✗ | ✓ (formal ASR, web/tool domain) |
| Phrasing-technique axis (vary wording, measure rate) | ~ (evolves payloads, not a rate grid) | ✗ | ✗ | ✗ | ✓ (technique-vs-baseline ASR) |
| Reproducible artifact released | **✓ (anonymized 4open.science)** | **✓ (public GitHub)** | **✗ (not stated)** | not stated | ~ (WebSentinel repo) |
| Runtime prompt-level defense eval | ✗ | ~ (workflow-level mitigations, not prompt-level) | ✗ (static guards only) | ✗ | ✓ (WebSentinel, web domain) |
| Large-scale prevalence | ✓ (4,174) | ✗ | **✓ (13,392)** | ✓ (23,757) | ✗ |

---

## Open-Lane Shortlist (re-ranked after verification)

1. **Phrasing-technique × model × vector SUCCESS-RATE matrix for CI agents.** *(OPEN — but narrower
   than the starter claimed.)*
   R2 already reports coarse per-model per-pathway fractions and frames them as "structural"; R3 is
   static; R1 reports iteration counts, not rates. **The un-taken slice:** hold agent + vector fixed
   and vary **phrasing technique** (spotlighting-evasion, role-play, fake-completion, obfuscation,
   context-grounding, …) across models, reporting **ASR-style rates with real denominators** — i.e.
   port ToolHijacker/WebInject's ASR rigor to CI review/triage/summarizer agents. Contribution = the
   *technique-level* empirical curve none of R1–R3 provide. **Pitch as complementary to R2, not as
   "first per-model rates."**

2. **"Quiet vector" study.** *(OPEN — strongest remaining lane.)*
   `dependency_metadata` is ✗ across all three CI papers; `filename` is only named (R1), never tested;
   `code_comment`/`readme` appear only incidentally in R2. Systematically test these as carriers into
   review/triage agents. **Drop `commit_msg`** from the novelty framing — R3 already models it as a
   taint source. Pairs cleanly with Lane 1 as the vector axis.

3. **Runtime prompt-level defense evaluation in CI.** *(OPEN.)*
   R3 is static; R2's mitigations are workflow-level (tool restriction, author-association filters),
   not prompt-level; WebSentinel-style guard/spotlighting is web-domain only. Measure how much
   prompt-level defenses shrink success *rate* for CI agents specifically — a defense column on Lanes
   1–2.

4. **Post-patch reproduction / short longitudinal.** *(OPEN but weakly motivated here.)*
   Re-test whether R1/R2 attack classes still fire after vendor patches. **Caveat:** the starter's
   motivating "vendors patch in 4 days" comes from C1 (PromptPwnd), which has **no PDF in `refs/`** and
   is unverified. R1 does show bounties + withheld payloads (patches implied) — usable motivation.
   Lowest novelty ceiling.

### CLOSED — do not pitch as novel
- ❌ "GitHub Actions AI agents can be prompt-injected at all" → R1, R2, R3.
- ❌ "Large-scale static prevalence of injectable workflows" → R3 (13,392).
- ❌ "An open live-repo attack framework" → R2 (public). **Also note R1 released artifacts** — so
  "no reproducible testbed exists" is closed twice over.
- ❌ "Marketplace supply-chain hygiene (SHA pinning)" → R4.
- ⚠️ **Partially closed:** "no per-model rates in CI/CD" → R2 reports coarse ones. Only the
  *technique-varied, finer-grained* version (Lane 1) is open.

---

## Revised project framing (recommended)

Combine **Lane 2 (quiet vectors) + Lane 1 (technique×model rates)**, optionally **+ Lane 3 (defense)**:

> *A controlled susceptibility study measuring how indirect-injection success **rate** varies across
> **phrasing technique × model × injection vector** for CI/CD review/triage/summarizer agents — with
> emphasis on under-studied "quiet" carriers (**dependency metadata, filenames, code comments,
> READMEs**) that R1–R3 do not isolate — providing the **technique-level** empirical curve that
> GitInject (coarse, per-pathway, structural framing) and AWI (static) do not report, and optionally
> quantifying how much runtime prompt-level defenses shrink that rate.*

Position explicitly as **complementary to R2/R3**, borrowing **ToolHijacker/WebInject** ASR rigor
(R5 line). Keep the grid tight (e.g., 3 agents × 2–3 models × the 4 quiet vectors + 2 known-vector
controls × N phrasings) to finish in the 2-week window. **Honesty guardrail for the writeup:** cite
R2 Table 3 and state plainly that per-model rates already exist at coarse granularity — your novelty
is the technique axis and the quiet vectors, not "first rates."

---

## Provenance & limits
- Verified strictly from `refs/*.pdf` via extracted text; quotes were spot-checked against the source
  (R2 Table 3 per-model rates; R1 4open.science release; R3 no-release; R5b no arXiv ID).
- **No new 2026 papers added** (ARGUS, COSSETER, WASP, EIA, AgentDojo, etc.): none have a PDF in
  `refs/`, and the rules forbid web-searching or inventing them. If you drop their PDFs in `refs/`,
  re-run this pass and they can be folded in.
- **"Not covered" vs "unknown":** matrix ✗ = affirmatively out of scope in the text; C1/C2 items are
  **unknown (no source)**, kept separate and never treated as covered.
