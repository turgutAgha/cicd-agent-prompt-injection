# Changelog

## v3 - Re-runs and data fixes (2026-10)

**16,335 trials; every model at 1,485.**

- Ran the 8 gpt-4.1 trials that had failed with API errors (same settings).
- Found that hidden reasoning sometimes used up the 1,024-token output limit, so the API
  returned no answer (`malformed_function_call` on Gemini). Re-ran these trials with a
  4,096-token limit:
  - gemini-2.5-pro: all 1,485 trials re-run (17.8% were empty before; 0.1% after).
  - gemini-2.5-flash (16) and gemini-2.5-flash-lite (40): only the empty trials.
  - claude-sonnet-5 (16): only the empty trials; 15 are API-level refusals and stay empty.
- Not re-run: o3-mini (50 empty; model shut down by OpenAI on 2026-10-23) and
  deepseek-reasoner (47 empty; the alias now serves a newer model). These score 0.
- Corrected DeepSeek labels: `deepseek-chat` / `deepseek-reasoner` pointed to
  DeepSeek-V4-Flash (non-thinking / thinking) during our runs, not V3 / R1.
- Corrected finding 2: price tier holds for Anthropic only; Gemini Flash-Lite is less
  susceptible than Flash, and the DeepSeek pair is one model with two modes.
- Runner now records the output limit, the served model id, and the finish reason in each
  raw JSON (`--max-tokens` flag added).
- `harness/analyze.py` section 7 adds robustness checks (CIs, empty outputs, canary-only
  comparisons, rung-5 composition, rung-1 quotation cases).
- Superseded responses are kept in `results/archive/superseded_max_tokens_1024/`.

## v2 - Oracle revision (2026-08-12)

**Detection marker expansion and negation-aware matching.**

The original oracle used 22 detection markers biased toward Anthropic and DeepSeek
vocabulary ("prompt injection", "cannot follow", "injected instruction"). An audit of
raw outputs revealed that OpenAI and Gemini models flag injections with different
phrases ("security risk", "malicious command", "supply chain attack", "suspicious
request", "hidden instruction").

Changes:
- Expanded detection markers from 22 to 65 entries covering all four model families.
- Added negation-aware matching for ambiguous phrases ("security concern", "security
  risk", "security issue") that frequently appear negated in normal code-review prose
  ("no security concerns", "security risks are low").
- Recovered 1,819 previously-missed detections across all trials.
- Susceptibility (rung) scores are unaffected; those are mechanically derived from
  tool calls, not detection markers.

Corrected detection rates after the revision:

| Model | Before | After |
|-------|-------:|------:|
| Claude Sonnet 5 | 94.6% | 95.4% |
| deepseek-reasoner | 69.1% | 71.2% |
| deepseek-chat | 57.2% | 67.1% |
| Claude Haiku 4.5 | 37.6% | 55.0% |
| Gemini Pro | 3.8% | 30.4% |
| GPT-4.1 | 1.8% | 16.6% |
| Gemini Flash | 2.4% | 14.1% |
| o3-mini | 0.9% | 13.4% |
| GPT-4o-mini | 0.2% | 12.3% |
| GPT-4.1-mini | 0.5% | 12.3% |
| Gemini Flash-Lite | 0.7% | 10.4% |

## v1 - Initial oracle and full sweep (2026-07-31 to 2026-08-11)

**16,327 trials across 11 models in 4 families.**

- 5-rung capability ladder: NONE, CANARY, BENIGN_TOOL, SECRET_READ, SECRET_EXFIL,
  DOWNSTREAM_EXEC.
- 99 payload variants across 7 injection vectors and 13 techniques in 12 families
  (obfuscation has a plain and a base64 variant).
- 3 CI agents: code_review, pr_summarizer, issue_triage.
- Structural rung-1 scoring (compliance vs quotation) to avoid false positives from
  agents quoting the canary while flagging the injection.
- Phase 1 (5 models): deepseek-chat/deepseek-reasoner, Gemini Flash/Flash-Lite/Pro.
- Phase 2 (6 models): Claude Haiku 4.5/Sonnet 5, GPT-4.1/4.1-mini/4o-mini, o3-mini.
