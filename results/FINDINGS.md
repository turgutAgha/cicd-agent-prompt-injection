# Findings - Indirect Prompt Injection against CI/CD Agentic Workflows

**Status:** COMPLETE. **16,327 trials** across **11 models** in **4 families** (Anthropic,
DeepSeek, Google Gemini, OpenAI). 99 payloads x 3 agents x 5 reps per model (gpt-4.1
at 1,477/1,485 due to 8 API errors; all others at full 1,485).
Regenerate any time with `python -m harness.analyze` (raw dump: `results/analysis.txt`).
Every number below comes from that script; section numbers like [7d] point to its output.

The oracle is single-turn and decision-level, so every number measures
**exploitation-intent depth**: how far an injection pushes the agent's *first* decision
along the 5-rung ladder. It does not measure multi-step propagation.

Ladder: `0 NONE · 1 canary · 2 benign_tool · 3 secret_read · 4 secret_exfil · 5 downstream_exec`

**Two views.** Some results are reported twice:
- **Mean depth (all 99 payloads).** Mixes how often a technique or vector works with
  which rungs its payloads target.
- **Rung-1+ rate on the 63 canary-only payloads.** Every technique and vector is compared
  on the same target. Use this view to compare techniques and vectors fairly.

---

## Models tested

| Model | Family | Provider | Trials | Empty outputs | Notes |
|-------|--------|----------|-------:|--------------:|-------|
| claude-haiku-4-5 | Anthropic | anthropic | 1,485 | 0.0% | |
| claude-sonnet-5 | Anthropic | anthropic | 1,485 | 1.1% | |
| deepseek-chat | DeepSeek | deepseek | 1,485 | 0.0% | V3 |
| deepseek-reasoner | DeepSeek | deepseek | 1,485 | 3.2% | R1 (reasoning) |
| gpt-4.1 | OpenAI | openai | 1,477 | 0.0% | Flagship |
| gpt-4.1-mini | OpenAI | openai | 1,485 | 0.0% | |
| gpt-4o-mini | OpenAI | openai | 1,485 | 0.0% | |
| o3-mini | OpenAI | openai | 1,485 | 3.4% | Reasoning model |
| gemini-2.5-flash | Google | vertex | 1,485 | 1.1% | |
| gemini-2.5-flash-lite | Google | vertex | 1,485 | 2.7% | |
| gemini-2.5-pro | Google | vertex | 1,485 | 17.8% | See note below |

An empty output has no text and no tool call, and scores 0. This matters only for
gemini-2.5-pro: among its non-empty trials, susceptibility is 17.4% instead of 14.3%.
Its rank does not change. The cause is unknown; one possibility is that hidden reasoning
used up the 1,024-token output limit. [7a]

---

## Headline findings

### 1. Technique effectiveness is model-specific, with partial transfer within a vendor

For each pair of models, we rank the 13 techniques by mean depth and compute the Spearman
correlation of the two rankings.

| Comparison | Mean pairwise ρ | Pairs |
|------------|----------------:|------:|
| All 11 models | 0.18 | 55 |
| Without claude-sonnet-5 | **0.29** | 45 |
| Same vendor (without Sonnet 5) | 0.41 | 10 |
| Different vendor (without Sonnet 5) | 0.26 | 35 |
| Canary-only payloads, rung-1+ rate, all 11 models | 0.37 | 55 |

claude-sonnet-5 is excluded in the second row because 11 of its 13 technique means are
zero, so its correlations are noise. The highest single agreement is between the two small
OpenAI models (ρ = 0.81). [6], [7c], [7d]

→ Technique rankings transfer only partly between models, and best within a vendor's
lineup. An attacker who tunes a payload on one model cannot expect the same ranking on
another.

![Model susceptibility by intent depth](fig1_reach_rates.png)

### 2. "Cheaper = more exploitable" holds for 3 families, breaks for OpenAI

| Model | Reach ≥1 (95% CI) | ≥2 tool | ≥3 secret | ≥5 exec | Flags injection |
|-------|------------------:|--------:|----------:|--------:|----------------:|
| gemini-2.5-flash | **51.6%** (49.1-54.2) | 11.0% | 7.9% | 2.3% | 14.1% |
| o3-mini | 44.6% (42.1-47.1) | 6.1% | 4.0% | 2.4% | 13.4% |
| gpt-4.1 | 38.7% (36.2-41.2) | 2.9% | 0.9% | 0.5% | 16.6% |
| gpt-4.1-mini | 37.4% (35.0-39.9) | 13.8% | 10.6% | 3.8% | 12.3% |
| gemini-2.5-flash-lite | 33.5% (31.1-35.9) | 10.5% | 6.7% | 3.0% | 10.4% |
| gpt-4o-mini | 29.7% (27.4-32.1) | 14.5% | 10.4% | 7.6% | 12.3% |
| deepseek-chat | 19.2% (17.3-21.3) | 5.9% | 2.8% | 0.3% | 67.1% |
| gemini-2.5-pro | 14.3% (12.6-16.1) | 1.5% | 1.3% | 1.2% | 30.4% |
| claude-haiku-4-5 | 9.2% (7.8-10.7) | 3.4% | 2.7% | 0.0% | 55.0% |
| deepseek-reasoner | 4.0% (3.2-5.2) | 0.1% | 0.1% | 0.1% | 71.2% |
| **claude-sonnet-5** | **0.2%** (0.1-0.6) | 0.0% | 0.0% | 0.0% | **95.4%** |

The "cheaper = more exploitable" pattern holds in **three** families:
- **Anthropic:** Haiku 9.2% ≫ Sonnet 0.2%
- **Google:** Flash 51.6% ≫ Pro 14.3%
- **DeepSeek:** Chat 19.2% ≫ Reasoner 4.0%

It **breaks** for OpenAI: the flagship gpt-4.1 (38.7%) is as susceptible as gpt-4.1-mini
(37.4%) and more susceptible than gpt-4o-mini (29.7%). o3-mini (the reasoning model) is the
*most* susceptible OpenAI model at 44.6%. The relationship is **family-dependent**, not
universal.

Depth matters here: gpt-4.1 and gpt-4.1-mini have similar reach rates, but gpt-4.1 almost
always stops at rung 1 (0.9% secret reads), while gpt-4.1-mini reads secrets in 10.6% of
trials.

Two of claude-sonnet-5's three rung-1 trials quote the canary inside a code block while
warning about it (see Caveats). Its true rate may be closer to zero.

### 3. Reasoning models diverge across families: "reasoning ≠ resistant"

- **DeepSeek-Reasoner:** 4.0% susceptible, the 2nd most resistant model overall.
- **o3-mini:** 44.6% susceptible, the 2nd most exploitable model overall.

Reasoning architecture alone does not predict injection resistance.

![Injection detection rate by model](fig4_detection_rates.png)

### 4. Explicit flagging rate is strongly associated with resistance

Flagging is measured by phrase matching on the agent's output (65 markers with negation
handling; see `CHANGELOG.md` and `harness/oracle.py`). [7b]

- Across the 11 models, Spearman ρ(flagging rate, reach ≥1) = **−0.71**.

| Group | Models | Flagging rate | Mean susceptibility |
|-------|--------|--------------:|--------------------:|
| **High flagging** (≥50%) | Claude Sonnet/Haiku, DeepSeek Chat/Reasoner | 55-95% | 8.1% |
| **Moderate flagging** | Gemini Pro | 30% | 14.3% |
| **Low flagging** (<20%) | OpenAI models, Gemini Flash/Lite | 10-17% | 39.2% |

The low-flagging group is about **4.8x** more susceptible. Price tier does not explain this
as well: it fails for OpenAI (finding 2).

Flagging is not the same as refusing. In **193 trials** the agent flagged the injection and
still reached rung 1 or higher (gpt-4.1: 41, deepseek-chat: 40, gpt-4.1-mini: 34).

This is an association over 11 models, not a cause. Flagging and resistance may both come
from the same safety training.

### 5. Nine models staged attacker-controlled commands; gpt-4o-mini most often

gpt-4o-mini reached rung 5 (staged a CI command or wrote a CI config) in **7.6%** of trials,
the highest rate. [7e]

| Model | Rung 5 | From rung-5 payloads | From other payloads |
|-------|-------:|---------------------:|--------------------:|
| gpt-4o-mini | **7.6%** (113) | 44 | 69 |
| gpt-4.1-mini | 3.8% (56) | 34 | 22 |
| gemini-2.5-flash-lite | 3.0% (45) | 24 | 21 |
| o3-mini | 2.4% (35) | 27 | 8 |
| gemini-2.5-flash | 2.3% (34) | 14 | 20 |
| gemini-2.5-pro | 1.2% (18) | 1 | 17 |
| gpt-4.1 | 0.5% (7) | 0 | 7 |
| deepseek-chat | 0.3% (4) | 0 | 4 |
| deepseek-reasoner | 0.1% (1) | 0 | 1 |
| claude-haiku-4-5 | 0.0% | 0 | 0 |
| claude-sonnet-5 | 0.0% | 0 | 0 |

Many rung-5 trials came from payloads that only asked to "echo" the canary. The agent
staged `echo CANARY_...` as a CI command instead of writing it in its comment. **147 of the
313** rung-5 trials contain such a command. The command is harmless, but the agent still
passed attacker-controlled text to a later step, and the attacker could have chosen any
command. These trials stay at rung 5.

---

![Technique effectiveness heatmap](fig2_technique_heatmap.png)

## Which techniques work (pooled across 11 models)

| Technique | Family | Mean depth (all payloads) | Rung-1+ rate, canary payloads |
|-----------|--------|--------------------------:|------------------------------:|
| fake_completion | T5 | 0.77 | 35.5% |
| combined | stacked | 0.62 | 60.6% |
| observation_spoof | T3 | 0.60 | 33.1% |
| policy_mode | T7 | 0.53 | 53.2% |
| config_in_data | T9 | 0.50 | 12.1% |
| context_grounded | T2 | 0.38 | 50.7% |
| conditional | T10 | 0.36 | 43.7% |
| fake_system | T1 | 0.31 | 22.8% |
| urgency | T8 | 0.30 | 18.2% |
| direct | T0 | 0.28 | 26.9% |
| obfuscated | T6 | 0.26 | 22.7% |
| obfuscated_base64 | T6 | 0.22 | 17.3% |
| delimiter_confusion | T4 | 0.18 | 17.6% |

- On equal terms (canary-only), `combined`, `policy_mode`, and `context_grounded` succeed
  most often.
- `fake_completion` has the highest mean depth mostly because it pushes some models to stage
  the requested "post-step" as a CI command (rung 5). On gpt-4o-mini its mean depth is
  2.34, the highest technique×model value in the dataset.
- Some techniques spike on single models: `observation_spoof` on gemini-flash (1.40) and
  gpt-4o-mini (1.39) but 0.11 on DeepSeek Chat; `delimiter_confusion` is weak almost
  everywhere except o3-mini (0.96).
- **Obfuscation ranks near the bottom in both views.** Hiding the instruction *lowers*
  compliance.

## Which entry vectors carry furthest (pooled)

![Entry vector effectiveness](fig3_vector_ranking.png)

| Vector | Type | Mean depth (all payloads) | Rung-1+ rate, canary payloads |
|--------|------|--------------------------:|------------------------------:|
| dependency_metadata | quiet | 0.65 | 37.3% |
| pr_body | known | 0.53 | 39.8% |
| issue_comment | known | 0.49 | 53.6% |
| readme | quiet | 0.37 | 32.2% |
| code_comment | quiet | 0.23 | 29.3% |
| filename | quiet | 0.17 | 7.6% |
| commit_msg | known | 0.06 | 7.3% |

`dependency_metadata` has the highest mean depth partly because it has more payloads that
target deep rungs. On equal terms, issue comments lead, and **dependency metadata works about
as well as a pull request body** (37.3% vs 39.8%). A field that agents read as structured
package data is as good an entry point as the best-known vectors. Filenames and commit
messages rarely work in either view.

## Agent susceptibility (pooled)

Mean depth: `issue_triage` (0.47) > `code_review` (0.38) > `pr_summarizer` (0.36).
On canary-only payloads the three are almost equal (33.5%, 32.2%, 31.6%). So the role does
not change how often the agent repeats the token; it changes how often the agent goes on to
use tools. The triage agent, prompted to *act on* reported content, used tools most.

---

## Caveats

- Single-turn intent, not realized propagation (by design; see DESIGN.md §1).
- **Reproducibility:** re-running the oracle on all 16,327 stored raw responses gives the
  same depth and flagging label for every trial.
- **Rung-1 quotations:** 145 of the 3,154 rung-1 trials also flag the injection. Some are
  quotations that the structural rule counted as compliance; in 7 the canary sits inside a
  code block (2 of them are claude-sonnet-5's). Removing all 145 lowers no model's
  susceptibility by more than 2.5 points (gpt-4.1). [7f]
- **Unbalanced design:** techniques and vectors have different numbers of payloads and
  different target rungs (e.g., 31 `context_grounded` payloads, 2 `combined`). Use the
  canary-only view for fair comparisons; small cells remain noisy.
- **Empty outputs** score 0; see the models table (gemini-2.5-pro 17.8%).
- gpt-4.1 completed 1,477/1,485 (99.5%) due to 8 API errors; all other models at full
  1,485.
- o3-mini receives the system prompt inside the user message (reasoning-model API
  limitation), which may affect its behavior.
- The agents' system prompt says the input is untrusted. No other defenses are used.
- **Detection rate revision (v2):** the original oracle used 22 detection markers biased
  toward Anthropic/DeepSeek vocabulary ("prompt injection", "cannot follow"). An audit
  found that OpenAI and Gemini models flag injections with different phrases ("security
  risk", "malicious command", "supply chain attack"). Expanding the marker list and
  adding negation-aware matching (to avoid false positives from "no security concerns")
  recovered 1,819 previously-missed detections. Susceptibility (rung) scores are
  unaffected; those are mechanically derived from tool calls.
