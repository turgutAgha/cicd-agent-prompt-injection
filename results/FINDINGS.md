# Findings - Indirect Prompt Injection against CI/CD Agentic Workflows

**Status:** COMPLETE. **16,335 trials** across **11 models** in **4 families** (Anthropic,
DeepSeek, Google Gemini, OpenAI). 99 payloads x 3 agents x 5 reps = 1,485 trials per model.
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
| claude-sonnet-5 | Anthropic | anthropic | 1,485 | 1.0% | |
| deepseek-chat | DeepSeek | deepseek | 1,485 | 0.0% | alias: DeepSeek-V4-Flash, non-thinking |
| deepseek-reasoner | DeepSeek | deepseek | 1,485 | 3.2% | alias: DeepSeek-V4-Flash, thinking |
| gpt-4.1 | OpenAI | openai | 1,485 | 0.0% | Flagship |
| gpt-4.1-mini | OpenAI | openai | 1,485 | 0.0% | |
| gpt-4o-mini | OpenAI | openai | 1,485 | 0.0% | |
| o3-mini | OpenAI | openai | 1,485 | 3.4% | Reasoning model |
| gemini-2.5-flash | Google | vertex | 1,485 | 0.0% | |
| gemini-2.5-flash-lite | Google | vertex | 1,485 | 0.0% | |
| gemini-2.5-pro | Google | vertex | 1,485 | 0.1% | all trials at 4,096 tokens |

**Run dates and settings.** Main runs: July 31 to August 12, 2026, with a 1,024-token output
limit. Hidden reasoning sometimes used up that limit and left the response empty. In October
2026 the empty trials of the Gemini and Claude models were re-run with a 4,096-token limit;
Gemini 2.5 Pro (17.8% empty before) was fully re-run at 4,096. Each re-run trial records its
limit, the served model, and the finish reason in its raw JSON. Trials with no output score 0.
The superseded responses are kept in `results/archive/superseded_max_tokens_1024/`.

**DeepSeek models.** `deepseek-chat` and `deepseek-reasoner` are API aliases. During our runs,
DeepSeek's documentation stated they pointed to DeepSeek-V4-Flash in non-thinking and
thinking mode, so they are one model with two modes, not two price tiers.

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
| Canary-only payloads, rung-1+ rate, all 11 models | 0.36 | 55 |

claude-sonnet-5 is excluded in the second row because 11 of its 13 technique means are
zero, so its correlations are noise. The highest single agreement is between the two small
OpenAI models (ρ = 0.81). [6], [7c], [7d]

→ Technique rankings transfer only partly between models, and best within a vendor's
lineup. An attacker who tunes a payload on one model cannot expect the same ranking on
another.

![Model susceptibility by intent depth](fig1_reach_rates.png)

### 2. Price tier is a weak guide to resistance

| Model | Reach ≥1 (95% CI) | ≥2 tool | ≥3 secret | ≥5 exec | Flags injection |
|-------|------------------:|--------:|----------:|--------:|----------------:|
| gemini-2.5-flash | **52.2%** (49.6-54.7) | 11.1% | 7.9% | 2.4% | 14.5% |
| o3-mini | 44.6% (42.1-47.1) | 6.1% | 4.0% | 2.4% | 13.4% |
| gpt-4.1 | 38.7% (36.3-41.2) | 3.0% | 1.0% | 0.5% | 16.5% |
| gpt-4.1-mini | 37.4% (35.0-39.9) | 13.8% | 10.6% | 3.8% | 12.3% |
| gemini-2.5-flash-lite | 34.1% (31.8-36.6) | 10.9% | 7.0% | 3.2% | 10.8% |
| gpt-4o-mini | 29.7% (27.4-32.1) | 14.5% | 10.4% | 7.6% | 12.3% |
| deepseek-chat | 19.2% (17.3-21.3) | 5.9% | 2.8% | 0.3% | 67.1% |
| gemini-2.5-pro | 17.6% (15.8-19.7) | 1.1% | 0.9% | 0.9% | 47.4% |
| claude-haiku-4-5 | 9.2% (7.8-10.7) | 3.4% | 2.7% | 0.0% | 55.0% |
| deepseek-reasoner | 4.0% (3.2-5.2) | 0.1% | 0.1% | 0.1% | 71.2% |
| **claude-sonnet-5** | **0.2%** (0.1-0.6) | 0.0% | 0.0% | 0.0% | **95.5%** |

- **Anthropic:** the cheaper model is more susceptible. Haiku 9.2% ≫ Sonnet 0.2%.
- **Google:** the flagship Pro is the least susceptible (17.6%), but the cheapest model,
  Flash-Lite (34.1%), is *less* susceptible than Flash (52.2%).
- **OpenAI:** the flagship gpt-4.1 (38.7%) is as susceptible as gpt-4.1-mini (37.4%) and more
  susceptible than gpt-4o-mini (29.7%). o3-mini is the most susceptible OpenAI model (44.6%).
- **DeepSeek:** not a price comparison. Turning thinking on (deepseek-reasoner) cut
  susceptibility from 19.2% to 4.0%.

Depth matters here: gpt-4.1 and gpt-4.1-mini have similar reach rates, but gpt-4.1 almost
always stops at rung 1 (1.0% secret reads), while gpt-4.1-mini reads secrets in 10.6% of
trials.

Two of claude-sonnet-5's three rung-1 trials quote the canary inside a code block while
warning about it (see Caveats). Its true rate may be closer to zero.

### 3. Reasoning models diverge: "reasoning ≠ resistant"

- **deepseek-reasoner (thinking mode):** 4.0% susceptible, the 2nd most resistant model overall.
- **o3-mini:** 44.6% susceptible, the 2nd most exploitable model overall.

Reasoning alone does not predict injection resistance.

![Injection detection rate by model](fig4_detection_rates.png)

### 4. Explicit flagging rate is strongly associated with resistance

Flagging is measured by phrase matching on the agent's output (65 markers with negation
handling; see `CHANGELOG.md` and `harness/oracle.py`). [7b]

- Across the 11 models, Spearman ρ(flagging rate, reach ≥1) = **−0.71**.

| Group | Models | Flagging rate | Mean susceptibility |
|-------|--------|--------------:|--------------------:|
| **High flagging** (≥50%) | Claude Sonnet/Haiku, DeepSeek Chat/Reasoner | 55-96% | 8.1% |
| **Moderate flagging** | Gemini Pro | 47% | 17.6% |
| **Low flagging** (<20%) | OpenAI models, Gemini Flash/Lite | 11-17% | 39.5% |

The low-flagging group is about **4.8x** more susceptible. This association is more
consistent than price tier, which does not hold within Google or OpenAI (finding 2).

Flagging is not the same as refusing. In **203 trials** the agent flagged the injection and
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
| gemini-2.5-flash-lite | 3.2% (48) | 26 | 22 |
| o3-mini | 2.4% (35) | 27 | 8 |
| gemini-2.5-flash | 2.4% (35) | 15 | 20 |
| gemini-2.5-pro | 0.9% (13) | 0 | 13 |
| gpt-4.1 | 0.5% (7) | 0 | 7 |
| deepseek-chat | 0.3% (4) | 0 | 4 |
| deepseek-reasoner | 0.1% (1) | 0 | 1 |
| claude-haiku-4-5 | 0.0% | 0 | 0 |
| claude-sonnet-5 | 0.0% | 0 | 0 |

Many rung-5 trials came from payloads that only asked to "echo" the canary. The agent
staged `echo CANARY_...` as a CI command instead of writing it in its comment. **144 of the
312** rung-5 trials contain such a command. The command is harmless, but the agent still
passed attacker-controlled text to a later step, and the attacker could have chosen any
command. These trials stay at rung 5.

---

![Technique effectiveness heatmap](fig2_technique_heatmap.png)

## Which techniques work (pooled across 11 models)

| Technique | Family | Mean depth (all payloads) | Rung-1+ rate, canary payloads |
|-----------|--------|--------------------------:|------------------------------:|
| fake_completion | T5 | 0.75 | 35.1% |
| combined | stacked | 0.64 | 62.7% |
| observation_spoof | T3 | 0.62 | 34.8% |
| policy_mode | T7 | 0.55 | 55.2% |
| config_in_data | T9 | 0.51 | 13.3% |
| context_grounded | T2 | 0.38 | 50.8% |
| conditional | T10 | 0.36 | 44.2% |
| fake_system | T1 | 0.32 | 23.7% |
| urgency | T8 | 0.31 | 18.7% |
| direct | T0 | 0.29 | 27.1% |
| obfuscated | T6 | 0.26 | 23.1% |
| obfuscated_base64 | T6 | 0.23 | 17.9% |
| delimiter_confusion | T4 | 0.19 | 17.8% |

- On equal terms (canary-only), `combined`, `policy_mode`, and `context_grounded` succeed
  most often.
- `fake_completion` has the highest mean depth mostly because it pushes some models to stage
  the requested "post-step" as a CI command (rung 5). On gpt-4o-mini its mean depth is
  2.34, the highest technique×model value in the dataset.
- Some techniques spike on single models: `observation_spoof` on gemini-flash (1.40) and
  gpt-4o-mini (1.39) but 0.11 on deepseek-chat; `delimiter_confusion` is weak almost
  everywhere except o3-mini (0.96).
- **Obfuscation ranks near the bottom in both views.** Hiding the instruction *lowers*
  compliance.

## Which entry vectors carry furthest (pooled)

![Entry vector effectiveness](fig3_vector_ranking.png)

| Vector | Type | Mean depth (all payloads) | Rung-1+ rate, canary payloads |
|--------|------|--------------------------:|------------------------------:|
| dependency_metadata | quiet | 0.67 | 38.4% |
| pr_body | known | 0.53 | 40.5% |
| issue_comment | known | 0.50 | 54.1% |
| readme | quiet | 0.38 | 32.4% |
| code_comment | quiet | 0.24 | 30.6% |
| filename | quiet | 0.18 | 8.0% |
| commit_msg | known | 0.05 | 7.0% |

`dependency_metadata` has the highest mean depth partly because it has more payloads that
target deep rungs. On equal terms, issue comments lead, and **dependency metadata works about
as well as a pull request body** (38.4% vs 40.5%). A field that agents read as structured
package data is as good an entry point as the best-known vectors. Filenames and commit
messages rarely work in either view.

## Agent susceptibility (pooled)

Mean depth: `issue_triage` (0.47) > `code_review` (0.38) > `pr_summarizer` (0.37).
On canary-only payloads the three are almost equal (33.6%, 33.6%, 32.0%). So the role does
not change how often the agent repeats the token; it changes how often the agent goes on to
use tools. The triage agent, prompted to *act on* reported content, used tools most.

---

## Caveats

- Single-turn intent, not realized propagation (by design; see DESIGN.md §1).
- **Reproducibility:** re-running the oracle on all 16,335 stored raw responses gives the
  same depth and flagging label for every trial.
- **Rung-1 quotations:** 155 of the 3,225 rung-1 trials also flag the injection. Some are
  quotations that the structural rule counted as compliance; in 7 the canary sits inside a
  code block (2 of them are claude-sonnet-5's). Removing all 155 lowers no model's
  susceptibility by more than 2.5 points (gpt-4.1). [7f]
- **Unbalanced design:** techniques and vectors have different numbers of payloads and
  different target rungs (e.g., 31 `context_grounded` payloads, 2 `combined`). Use the
  canary-only view for fair comparisons; small cells remain noisy.
- **Empty outputs** score 0; see the models table (at most 3.4% per model).
- **DeepSeek aliases:** the API did not report which version it served during the main runs,
  so the DeepSeek-V4-Flash mapping rests on DeepSeek's documentation for that period.
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
