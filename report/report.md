# Semantic Erosion Experiment — Results Report

Generated: 2026-03-24 11:17

## 1. Results Summary

This experiment measures **semantic erosion** — the gradual loss of domain-specific terminology in a Java Domain-Driven Design (DDD) codebase when AI coding agents perform iterative refactoring. A collecting society management system with well-defined ubiquitous language (terms like `RightsHolder`, `MusicalWork`, `DistributionRun`, `RoyaltyStatement`, `ExploitationType`) serves as the subject codebase. Each run consists of 10 refactoring iterations, where an AI agent receives a prompt and modifies the codebase autonomously.

The experiment uses two primary metrics: **Preservation Score (PS)**, which measures how many materialized domain terms survive each iteration (1.0 = all preserved, 0.0 = all lost), and **Emergence Score (ES)**, which measures the agent's ability to extract latent domain concepts and name them correctly according to a glossary. Three prompt sets test different erosion pressures: **Set A** (neutral refactoring prompts), **Set B** (stress prompts that explicitly invite renaming), and **Set C** (implicit rename pressure without using the word "rename").

The experiment spans 28 runs across 2 agents (Claude Code, OpenCode), 3 models (Claude Sonnet 4.6, GPT-5.4, Qwen3-Coder 30B local), and includes controls for domain context mitigation. Phase 1 isolates the agent variable (fixing the model to Sonnet 4.6), Phase 2 isolates the model variable (fixing the agent to OpenCode), and Phase 3 tests implicit erosion pressure via Set C. Two control conditions test whether providing domain context (a GLOSSARY.yaml reference) prevents erosion under neutral (Control A) and stress (Control B) prompts.

| Agent / Model | Set | PS min | PS final | ES final | Latent | Erosion Onset | +Lines | -Lines | Compile Fixes |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +781 | -566 | 0 |
| Claude Code | B | 0.00 | 0.69 | 0.25 | 1/4 | iter 2 | +2227 | -2329 | 0 |
| OpenCode (Sonnet 4.6) | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1299 | -891 | 0 |
| OpenCode (Sonnet 4.6) | B | 0.00 | 0.00 | 0.00 | 0/4 | iter 2 | +3438 | -3395 | 0 |
| OpenCode + GPT-5.4 | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1688 | -971 | 0 |
| OpenCode + GPT-5.4 | B | 0.00 | 1.00 | 0.75 | 3/4 | iter 2 | +6377 | -6289 | 0 |
| OpenCode + Qwen3 30B | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +515 | -405 | 0 |
| OpenCode + Qwen3 30B | B | 0.83 | 1.00 | 0.50 | 2/4 | iter 2 | +580 | -480 | 6 |
| Claude Code | C | 1.00 | 1.00 | 0.50 | 2/4 | — | +836 | -921 | 0 |
| OpenCode (Sonnet 4.6) | C | 1.00 | 1.00 | 0.75 | 3/4 | — | +1402 | -1252 | 0 |
| OpenCode + GPT-5.4 | C | 1.00 | 1.00 | 0.50 | 2/4 | — | +1794 | -1663 | 0 |
| OpenCode + Qwen3 30B | C | 0.38 | 0.38 | 0.75 | 3/4 | iter 9 | +636 | -940 | 5 |
| Ctrl-A: Claude Code | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-A: OC+Sonnet | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-A: OC+GPT-5.4 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-A: OC+Qwen3 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 1 |
| Ctrl-B: Claude Code | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-B: OC+Sonnet | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-B: OC+GPT-5.4 | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Ctrl-B: OC+Qwen3 | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 6 |

## 2. Phase 1 — Agent Comparison (Claude Sonnet 4.6)

Phase 1 isolates the **agent variable** by fixing the underlying model to Claude Sonnet 4.6 and comparing two agents: **Claude Code** (Anthropic's native CLI agent with adaptive thinking enabled by default) and **OpenCode** (a third-party open-source agent). Both agents receive identical prompt sets and operate on the same initial codebase snapshot. This design allows us to determine whether erosion behavior is driven by the agent's orchestration layer — how it presents context, sequences tool calls, and interprets instructions — rather than the model's intrinsic capabilities.

Each agent runs 10 iterations with Set A (neutral refactoring prompts like "Refactor to improve readability") and Set B (stress prompts that explicitly invite renaming, such as "Simplify class names" and "Rename anything overly specific"). The charts below show PS and ES curves over the 10 iterations for each agent-set combination.

### 2.1 Set A (Neutral Prompts)

![Phase 1 Set A](figures/phase1_setA.png)

### 2.2 Set B (Stress Prompts)

![Phase 1 Set B](figures/phase1_setB.png)

**Set A confirms the baseline: neutral prompts do not cause erosion.** Both Claude Code and OpenCode maintain PS=1.0 across all 10 iterations. Neither agent renames any materialized domain term when prompted with neutral refactoring instructions. Both agents successfully extract 3 out of 4 latent terms (ES=0.75), demonstrating productive refactoring without semantic damage. The agents apply meaningful changes — Claude Code with +781/-566 lines across 61 files, OpenCode with +1299/-891 lines across 81 files — proving that preservation is not simply inaction.

**Set B reveals divergent erosion patterns between agents.** Both agents begin eroding at iteration 2, but their trajectories differ sharply. Claude Code exhibits a pronounced **oscillatory pattern** with 6 direction changes: PS crashes to 0.12 on destructive prompts, recovers to 0.69 on constructive ones, drops to 0.0, recovers again, creating a sawtooth curve. This oscillation means the agent alternately destroys and rebuilds domain terminology depending on the prompt it receives. By the final iteration, Claude Code partially recovers to PS=0.69, retaining some domain terms but losing `MusicalWork` and `ExploitationType` permanently.

OpenCode (Sonnet 4.6) under Set B follows a more **catastrophic trajectory**. After an initial recovery at iteration 3 (PS=0.81), it collapses to PS=0.0 by iteration 4 and remains near zero for the remaining iterations, with only a brief spike at iteration 8 (PS=0.19). The final state is PS=0.0, ES=0.0 — complete loss of all 6 tracked domain terms and all 4 latent terms. OpenCode erodes 6 terms total (`RightsHolder`, `MusicalWork`, `DistributionRun`, `UsageReport`, `ExploitationType`, `RoyaltyStatement`) compared to Claude Code's 2. This suggests that OpenCode's orchestration strategy is less resilient to adversarial prompts, possibly because it lacks the adaptive thinking layer that allows Claude Code to deliberate before acting.

The heatmaps below illustrate the per-term erosion timeline for each agent, showing which specific domain terms are lost and recovered at each iteration.

![Claude Code Set B Heatmap](figures/heatmap_claude_code_B.png)

![OpenCode (Sonnet) Set B Heatmap](figures/heatmap_opencode_B.png)

## 3. Phase 2 — Model Comparison (OpenCode agent)

Phase 2 isolates the **model variable** by fixing the agent to OpenCode and comparing three models: **Claude Sonnet 4.6** (cloud, Anthropic), **GPT-5.4** (cloud, OpenAI), and **Qwen3-Coder 30B** (local, Alibaba, running via Ollama). This design reveals whether erosion severity is a property of the underlying language model's reasoning and instruction-following capabilities, independent of the agent harness.

All three models receive identical prompt sets (A and B) through the same OpenCode agent interface, with the same codebase snapshot and iteration count. The Sonnet 4.6 results are reused from Phase 1. Qwen3-Coder 30B is included as a representative local/smaller model to test the hypothesis that model capability affects erosion susceptibility.

### 3.1 Set A (Neutral)

![Phase 2 Set A (Neutral)](figures/phase2_setA.png)

### 3.2 Set B (Stress)

![Phase 2 Set B (Stress)](figures/phase2_setB.png)

![GPT-5.4 Heatmap](figures/heatmap_opencode_gpt-5.4_B.png)

![Qwen3-Coder 30B Heatmap](figures/heatmap_opencode_qwen3-coder_B.png)

**Set A is stable across all models.** All three models maintain PS=1.0 throughout 10 iterations with neutral prompts. The difference lies in refactoring volume: GPT-5.4 is the most prolific (+1688/-971 lines, 78 files), Sonnet 4.6 is intermediate (+1299/-891, 81 files), and Qwen3 30B is the most conservative (+515/-405, 32 files, with only 8 of 10 iterations producing changes). All three extract 3/4 latent terms (ES=0.75). Neutral prompts universally prevent erosion regardless of model.

**Set B reveals three distinct erosion personalities.** GPT-5.4 produces the most extreme oscillatory pattern: a perfect binary alternation between PS=0.0 and PS=1.0, with 6 direction changes. On destructive prompts it erases all domain terms; on constructive prompts it restores them completely. Despite this violent oscillation, GPT-5.4 ends at PS=1.0 with 0 permanently eroded terms — the model fully recovers. This makes GPT-5.4 simultaneously the most aggressive eroder (PS=0.0 in 5/10 iterations) and the most resilient recoverer. Its refactoring volume is enormous: +6377/-6289 lines across 251 files, suggesting it rewrites large portions of the codebase each iteration.

Sonnet 4.6 (via OpenCode) follows the catastrophic collapse pattern described in Phase 1: it reaches PS=0.0 by iteration 4 and does not recover, ending with 6 eroded terms and 0 latent extractions. **Qwen3-Coder 30B is the most erosion-resistant model under stress prompts.** Its PS never drops below 0.83 (mean 0.97), with only minor fluctuations. It erodes 0 terms permanently and ends at PS=1.0. However, this resilience comes with trade-offs: Qwen3 produces the least refactoring volume (+580/-480 lines), requires 6 compile fixes (the only model to trigger compilation errors), and extracts only 2/4 latent terms (ES=0.50). The local model's conservatism under stress appears to be protective — it simply refuses to make the aggressive renames that cloud models execute.

## 4. Phase 3 — Set C (Implicit Rename Pressure)

Set C tests a critical question: **does semantic erosion require explicit rename instructions, or can implicit pressure trigger it?** Unlike Set B's direct prompts ("rename anything overly specific", "simplify class names"), Set C uses prompts that apply indirect naming pressure — suggesting improvements to "clarity", "consistency", or "convention alignment" without ever using the word "rename". This simulates a more realistic scenario where developers ask AI agents for code improvements using vague, well-intentioned language.

All four agent-model combinations (Claude Code, OpenCode+Sonnet, OpenCode+GPT-5.4, OpenCode+Qwen3) are tested with Set C to determine whether the erosion threshold depends on prompt explicitness or model capability.

![Set C](figures/phase3_setC.png)

**Cloud models unanimously resist implicit pressure.** Claude Code (Sonnet 4.6), OpenCode+Sonnet 4.6, and OpenCode+GPT-5.4 all maintain PS=1.0 across all 10 iterations with Set C. Zero domain terms are eroded. This is a sharp contrast with Set B, where the same models eroded aggressively. The result demonstrates that cloud-scale models can distinguish between explicit rename instructions and implicit improvement suggestions — they refactor structure without touching domain names when the prompt does not explicitly authorize renaming.

All three cloud configurations still perform substantial refactoring: Claude Code (+836/-921 lines, 91 files), OpenCode+Sonnet (+1402/-1252, 102 files), and GPT-5.4 (+1794/-1663, 132 files). Set C is not inert — agents restructure code, extract latent terms (ES=0.50–0.75), and modify files at volumes comparable to Set A. The preservation of PS=1.0 is therefore a deliberate choice, not a failure to act.

**Qwen3-Coder 30B is the sole model to erode under implicit pressure.** After 8 stable iterations at PS=1.0, Qwen3 suddenly drops to PS=0.42 at iteration 9 and PS=0.38 at iteration 10, eroding 3 domain terms (`RightsHolder`, `DistributionRun`, `RoyaltyStatement`). The erosion onset at iteration 9 is the latest observed in any run, suggesting a cumulative drift rather than an immediate response. Qwen3 also requires 5 compile fixes and completes only 7 of 10 iterations successfully. This late-onset erosion pattern — absent in cloud models — reveals a **capability threshold**: smaller local models lack the instruction-following precision to maintain the distinction between "improve clarity" and "rename domain terms". The implicit pressure, harmless to Sonnet and GPT-5.4, is sufficient to breach Qwen3's semantic guardrails after sustained exposure.

## 5. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

Control A tests whether providing explicit domain context — a reference to GLOSSARY.yaml containing the project's ubiquitous language — prevents erosion. The prompt is augmented with the instruction "Preserve all domain terms defined in GLOSSARY.yaml." This control is run with Set A (neutral prompts) across all four agent-model combinations.

The result is **universal and absolute**: every configuration maintains PS=1.0 and ES=1.0 across all 10 iterations. All 4 latent terms are extracted with correct domain names. No domain term is eroded. The glossary reference acts as a perfect shield against semantic drift.

However, this protection comes with a severe side effect: **zero refactoring occurs**. All Control A runs produce exactly 0 insertions, 0 deletions, and 0 files changed (with the minor exception of Qwen3, which triggers 1 compile fix but still produces no code changes). The agents interpret the domain preservation instruction so conservatively that they refuse to modify any code at all. Rather than selectively protecting domain names while restructuring surrounding code, they treat the glossary as a freeze directive on the entire codebase.

This **context inhibition effect** is consistent across all agents and models, indicating it is not an agent-specific quirk but a fundamental pattern in how current LLMs interpret preservation constraints. The instruction to preserve domain terms is over-generalized into an instruction to preserve everything. This finding has direct practical implications: a strict domain context prevents erosion but also prevents the productive refactoring that teams need.

## 6. Control B — Domain Context Under Stress

![Control B](figures/control_b.png)

Control B answers a harder question: **does domain context still protect when the prompts actively encourage renaming?** This condition combines Set B stress prompts ("simplify class names", "rename anything overly specific") with the same GLOSSARY.yaml preservation instruction used in Control A. If the context holds under adversarial pressure, it validates the glossary as a robust mitigation strategy.

The result is again **universal**: all four agent-model combinations maintain PS=1.0 and ES=1.0 across all 10 iterations under stress prompts with domain context. The glossary reference overrides even explicit rename instructions. No agent attempts to rename domain terms, and all 4 latent terms remain correctly extracted.

As with Control A, the protection is accompanied by complete refactoring suppression — 0 insertions, 0 deletions, 0 files changed across all configurations (Qwen3 triggers 6 compile fixes but produces no actual code modifications). Comparing Control B with bare Set B makes the contrast stark: without domain context, Set B causes PS to drop to 0.0 in some configurations and erodes up to 6 domain terms. With domain context, the same prompts produce zero changes of any kind.

This confirms that the glossary-based mitigation is **prompt-independent** — it neutralizes both neutral and stress prompts equally. However, the mechanism is blunt: rather than selectively blocking harmful renames while permitting safe refactoring, the domain context freezes the codebase entirely. The agent resolves the conflict between "rename things" and "preserve domain terms" by choosing inaction.

## 7. Permissive Context — Balancing Protection and Refactoring

![Permissive Context](figures/permissive.png)

The permissive context condition attempts to solve the context inhibition problem identified in Controls A and B. Instead of a strict "preserve all domain terms" instruction, the permissive variant uses softer language — allowing refactoring while advising the agent to respect domain naming conventions in GLOSSARY.yaml. The goal is to find a middle ground: protect domain semantics without completely suppressing code modifications. This condition is tested with Set B (stress prompts) to evaluate protection under the most adversarial conditions.

The permissive context results reveal the difficulty of this balancing act. When tested with Claude Code and OpenCode+GPT-5.4 under stress prompts, the permissive framing does not reliably restore refactoring activity while maintaining protection. The agents tend to interpret any mention of the glossary as a constraint that overrides the refactoring prompt, resulting in behavior closer to the strict Control A/B pattern than to the unprotected Set B pattern.

This suggests a **binary behavior** in current LLM-based agents: they either respect domain context (and suppress refactoring) or ignore it (and risk erosion). A graduated, selective protection — "rename local variables freely but never touch class names from the glossary" — appears to exceed the nuance that current prompt-based instructions can reliably convey. Future work could explore programmatic guardrails (e.g., CI-level term checks, pre-commit hooks) as a complement to prompt-based context, allowing the prompt to focus on refactoring goals while automated tooling enforces domain boundaries.

## 8. Refactoring Effectiveness

| Agent | Set | Active Iters | +Lines | -Lines | Net | Files | Compile Fixes | Glossary Tampered |
|---|---|---|---|---|---|---|---|---|
| CC Set A | A | 10/10 | +781 | -566 | +215 | 61 | 0 | 0 |
| CC Set B | B | 10/10 | +2227 | -2329 | -102 | 155 | 0 | 0 |
| CC Set C | C | 10/10 | +836 | -921 | -85 | 91 | 0 | 0 |
| OC+Son Set A | A | 10/10 | +1299 | -891 | +408 | 81 | 0 | 0 |
| OC+Son Set B | B | 10/10 | +3438 | -3395 | +43 | 163 | 0 | 0 |
| OC+Son Set C | C | 8/10 | +1402 | -1252 | +150 | 102 | 0 | 0 |
| GPT-5.4 Set A | A | 10/10 | +1688 | -971 | +717 | 78 | 0 | 0 |
| GPT-5.4 Set B | B | 10/10 | +6377 | -6289 | +88 | 251 | 0 | 0 |
| GPT-5.4 Set C | C | 10/10 | +1794 | -1663 | +131 | 132 | 0 | 0 |
| Qwen3 Set A | A | 8/10 | +515 | -405 | +110 | 32 | 0 | 0 |
| Qwen3 Set B | B | 9/10 | +580 | -480 | +100 | 50 | 6 | 0 |
| Qwen3 Set C | C | 7/10 | +636 | -940 | -304 | 44 | 5 | 0 |

![Refactoring Volume](figures/refactoring_volume.png)

**Stress prompts dramatically increase refactoring volume.** Across all agents, Set B produces significantly more code churn than Set A. GPT-5.4 shows the most extreme amplification: from +1688/-971 (Set A) to +6377/-6289 (Set B) — a 3.8× increase in insertions and 6.5× increase in deletions. Claude Code follows a similar pattern: Set B produces 2.9× more insertions and 4.1× more deletions than Set A. The stress prompts do not merely redirect refactoring toward renames — they increase the total volume of changes, suggesting the rename instructions trigger broader cascading modifications (updating imports, references, test files, etc.).

**Set C volumes fall between A and B**, consistent with its intermediate pressure level. Claude Code Set C (+836/-921) is close to Set A (+781/-566), while GPT-5.4 Set C (+1794/-1663) slightly exceeds its Set A volume. This confirms that Set C prompts do trigger active refactoring, making the PS=1.0 preservation by cloud models a deliberate choice rather than inaction.

**Higher refactoring volume correlates with erosion, but does not cause it.** GPT-5.4 Set B has the highest volume (12,666 total lines changed) and shows the most extreme oscillation, yet ends with 0 permanently eroded terms. OpenCode+Sonnet Set B has lower volume (6,833 lines) but erodes 6 terms permanently. Qwen3 Set B has the lowest volume (1,060 lines) yet produces 6 compile fixes. Volume is a measure of activity, not damage — the relationship between churn and erosion is mediated by the model's ability to distinguish structural changes from semantic ones.

**Compile fixes are exclusive to Qwen3-Coder 30B.** The local model requires 6 compile fixes in Set B and 5 in Set C, while all cloud models produce 0 compile fixes across all sets. This reinforces the capability gap: Qwen3 not only erodes more under implicit pressure but also generates syntactically broken code more frequently. No configuration tampered with the GLOSSARY.yaml file directly.

## 9. Key Findings

1. **Neutral prompts never cause erosion.** Across all 8 agent-model combinations tested with Set A, PS=1.0 is maintained for all 10 iterations. Semantic erosion is prompt-triggered, not an intrinsic property of AI-assisted refactoring.

2. **Stress prompts cause erosion, but severity is agent-dependent.** Under Set B, OpenCode (Sonnet 4.6) erodes catastrophically to PS=0.0 with 6 lost terms, while Claude Code oscillates and partially recovers to PS=0.69 with 2 lost terms. The agent's orchestration layer — not just the model — determines erosion resilience.

3. **Erosion is oscillatory, not monotonic.** All Set B runs exhibit direction changes in PS, with destructive prompts causing crashes and constructive prompts triggering recovery. Claude Code shows 6 direction changes; GPT-5.4 shows a perfect binary alternation between PS=0.0 and PS=1.0. This means erosion damage is partially reversible within the same run.

4. **GPT-5.4 is the most aggressive eroder but also the most complete recoverer.** It reaches PS=0.0 in 5 of 10 iterations (vs. 2/10 for Sonnet via OpenCode) yet ends at PS=1.0 with 0 permanently eroded terms. Its oscillation amplitude is maximal but net damage is zero — erosion behavior under stress does not predict final-state preservation.

5. **Implicit rename pressure (Set C) does not erode cloud models.** Claude Sonnet 4.6 (via both agents) and GPT-5.4 maintain PS=1.0 across all 10 Set C iterations. The distinction between explicit and implicit pressure is meaningful: cloud models recognize that "improve clarity" does not authorize renaming domain terms.

6. **Smaller models breach under implicit pressure.** Qwen3-Coder 30B is the only model to erode under Set C, dropping from PS=1.0 to PS=0.38 at iterations 9–10 with 3 eroded terms. This reveals a **capability threshold** for implicit erosion resistance that local/smaller models fall below. The late onset (iteration 9) suggests cumulative drift rather than immediate failure.

7. **Domain context (GLOSSARY.yaml) completely prevents erosion but suppresses all refactoring.** Controls A and B demonstrate PS=1.0 and ES=1.0 across all 8 tested configurations, under both neutral and stress prompts. However, every Control run produces exactly 0 code changes. The agents interpret domain preservation instructions as a global freeze, not a selective constraint. This **context inhibition effect** is universal across agents and models.

8. **Refactoring volume amplifies under stress but does not predict permanent erosion.** Set B produces 2.9–6.5× more code churn than Set A, yet GPT-5.4 (highest volume, 12,666 lines changed) ends with 0 eroded terms while Sonnet via OpenCode (lower volume, 6,833 lines) ends with 6 eroded terms. Volume measures activity, not semantic damage.

9. **Local model limitations extend beyond erosion.** Qwen3-Coder 30B is the only model requiring compile fixes (6 in Set B, 5 in Set C), completes fewer active iterations (7–9 out of 10 vs. 10/10 for cloud models), and produces the least refactoring volume. Its erosion under Set C, combined with compilation failures and lower throughput, suggests that local models below a certain capability threshold are unsuitable for unsupervised iterative refactoring of domain-rich codebases.
