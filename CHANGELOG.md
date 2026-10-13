# Changelog

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
| DeepSeek R1 | 69.1% | 71.2% |
| DeepSeek V3 | 57.2% | 67.1% |
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
- 99 payload variants across 7 injection vectors and 12 technique families.
- 3 CI agents: code_review, pr_summarizer, issue_triage.
- Structural rung-1 scoring (compliance vs quotation) to avoid false positives from
  agents quoting the canary while flagging the injection.
- Phase 1 (5 models): DeepSeek V3/R1, Gemini Flash/Flash-Lite/Pro.
- Phase 2 (6 models): Claude Haiku 4.5/Sonnet 5, GPT-4.1/4.1-mini/4o-mini, o3-mini.
