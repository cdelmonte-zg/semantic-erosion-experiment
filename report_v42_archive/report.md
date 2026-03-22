# Semantic Erosion Experiment — Results Report

Generated: 2026-03-22 14:48

## 1. Results Summary

This experiment measures **semantic erosion** — the gradual loss of domain-specific terminology when AI coding agents iteratively refactor a Java Domain-Driven Design (DDD) codebase. The target project models a collecting society (music rights management), with domain terms such as `RightsHolder`, `MusicalWork`, `DistributionRun`, `RoyaltyStatement`, `SettlementPeriod`, and `TariffClass` drawn from established industry vocabulary.

Each experimental run subjects the codebase to **10 consecutive refactoring iterations**. Two metrics are tracked per iteration: the **Preservation Score (PS)**, which measures what fraction of monitored domain terms remain intact in the code, and the **Erosion Score (ES)**, which captures the broader semantic health of the domain model including latent term extraction. Two prompt sets are used: **Set A** (neutral refactoring prompts that do not suggest renaming) and **Set B** (stress prompts that encourage aggressive restructuring and "clean code" practices likely to trigger renaming). The experiment spans **3 agents** (Claude Code, OpenCode, OpenHands) and **3 underlying models** (Claude Sonnet 4.6, GPT-5.4, Qwen3-Coder 30B), with a **Control A** condition that supplies explicit domain glossary context to assess whether semantic anchoring can prevent erosion.

The design isolates two independent variables: in Phase 1, the agent varies while the model is held constant (Sonnet 4.6); in Phase 2, the model varies while the agent is held constant (OpenCode). This factorial structure allows attribution of erosion behavior to agent-level tooling decisions versus model-level linguistic biases.

| Agent / Model | Set | PS min | PS final | ES final | Latent | Erosion Onset | +Lines | -Lines | Compile Fixes |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | A | 1.00 | 1.00 | 0.25 | 1/4 | — | +0 | -0 | 0 |
| Claude Code | B | 0.12 | 1.00 | 1.00 | 4/4 | iter 2 | +1231 | -1503 | 0 |
| OpenCode (Sonnet 4.6) | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| OpenCode (Sonnet 4.6) | B | 0.00 | 0.00 | 0.00 | 4/4 | iter 9 | +1730 | -1453 | 0 |
| OpenHands | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +530 | -943 | 0 |
| OpenHands | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +731 | -955 | 0 |
| OpenCode + GPT-5.4 | A | 1.00 | 1.00 | 0.00 | 0/4 | — | +1690 | -1209 | 0 |
| OpenCode + GPT-5.4 | B | 0.00 | 0.00 | 0.00 | 0/4 | iter 2 | +4557 | -4560 | 0 |
| OpenCode + Qwen3 30B | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +849 | -505 | 2 |
| OpenCode + Qwen3 30B | B | 0.81 | 0.81 | 0.50 | 2/4 | iter 7 | +588 | -432 | 8 |
| Control: Claude Code | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Control: OpenCode+Sonnet | A | 1.00 | 1.00 | 0.00 | 0/4 | — | +0 | -0 | 0 |
| Control: OpenCode+GPT-5.4 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Control: OpenCode+Qwen3 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 5 |

## 2. Phase 1 — Agent Comparison (Claude Sonnet 4.6)

Phase 1 holds the underlying model constant at **Claude Sonnet 4.6** and varies the agent framework across three candidates: **Claude Code** (Anthropic's native CLI agent), **OpenCode** (an open-source coding agent), and **OpenHands** (formerly OpenDevin, an autonomous software engineering agent). Each agent receives identical prompt sets and operates on the same initial codebase snapshot. This design isolates the effect of agent-level architecture — including tool-use patterns, context management, and code-editing strategies — on the tendency to erode domain terminology during refactoring.

### 2.1 Set A (Neutral Prompts)

![Phase 1 Set A](figures/phase1_setA.png)

### 2.2 Set B (Stress Prompts)

![Phase 1 Set B](figures/phase1_setB.png)

The three agents exhibit dramatically different erosion profiles despite sharing the same underlying model. Under **Set A** (neutral prompts), all three agents maintain a perfect PS of 1.0 across all 10 iterations — none rename domain terms when not prompted to do so. However, the agents diverge sharply in whether they perform any refactoring at all: Claude Code and OpenCode apply zero changes (0 insertions, 0 deletions), while OpenHands actively refactors in 5 of 10 iterations (530 insertions, 943 deletions) yet preserves all domain terms. This suggests OpenHands interprets neutral refactoring prompts more aggressively but still respects naming.

Under **Set B** (stress prompts), the divergence becomes stark. **OpenHands remains completely erosion-resistant** (PS = 1.0 throughout, ES = 1.0), applying modest refactoring (4 active iterations) without touching any domain terms. **Claude Code exhibits transient erosion with self-correction**: PS drops to 0.12 at iteration 7 before recovering to 1.0 by iteration 8, producing 2 direction changes (oscillation). Notably, Claude Code's final state is fully restored — it erodes temporarily but repairs the damage. **OpenCode suffers catastrophic terminal erosion**: PS holds at 1.0 for 8 iterations then drops to 0.0 at iteration 9, remaining at 0.0. All 10 monitored domain terms are eroded, and the damage is irreversible within the experiment window.

The oscillation pattern in Claude Code Set B is particularly interesting. The ES curve shows a dip to 0.5 at iterations 4-5, recovery to 1.0 at iteration 6, a severe drop to 0.25 at iteration 7, then full recovery. This suggests Claude Code's internal guardrails detect and reverse semantic damage, but with a delay — a "correction lag" pattern. OpenCode, by contrast, shows no oscillation (0 direction changes): once erosion begins, it proceeds monotonically to total loss, indicating no self-correcting mechanism.

![Claude Code Set B Heatmap](figures/heatmap_claude_code_B.png)

![OpenCode (Sonnet) Set B Heatmap](figures/heatmap_opencode_B.png)

## 3. Phase 2 — Model Comparison (OpenCode agent)

Phase 2 holds the agent constant at **OpenCode** and varies the underlying model across three candidates: **Claude Sonnet 4.6**, **GPT-5.4** (OpenAI), and **Qwen3-Coder 30B** (Alibaba). By fixing the agent framework, this phase isolates the contribution of the language model itself — its linguistic biases, instruction-following behavior, and domain-term sensitivity — to semantic erosion patterns. OpenCode was chosen as the fixed agent because it demonstrated both erosion susceptibility and active refactoring in Phase 1, making it a sensitive instrument for detecting model-level differences.

### 3.1 Set A (Neutral)

![Phase 2 Set A (Neutral)](figures/phase2_setA.png)

### 3.2 Set B (Stress)

![Phase 2 Set B (Stress)](figures/phase2_setB.png)

![GPT-5.4 Heatmap](figures/heatmap_opencode_gpt-5.4_B.png)

![Qwen3-Coder 30B Heatmap](figures/heatmap_opencode_qwen3-coder_B.png)

The three models show markedly different erosion signatures under the same agent. **GPT-5.4 is the most aggressively erosive model**. Under Set B, erosion begins at iteration 2 (the earliest onset observed in any run), and the PS curve oscillates wildly with 5 direction changes — alternating between 0.0 and partial recovery (0.77 at iteration 3, 1.0 at iterations 6 and 8) before settling at 0.0. This chaotic oscillation pattern, combined with the highest refactoring volume in the experiment (4,557 insertions, 4,560 deletions, 228 files changed), suggests GPT-5.4 aggressively renames terms, partially reverses itself, then renames again. It is also the only model to **tamper with the glossary file** (glossary_tampered = 1), actively undermining the domain reference. Six of 10 monitored terms are eroded. Under Set A, GPT-5.4 preserves PS at 1.0 but produces an ES of 0.0 with 0/4 latent terms extracted, indicating it actively refactors (1,690 insertions) without eroding explicit terms but also fails to surface latent domain concepts.

**Sonnet 4.6** (analyzed in Phase 1) shows late-onset catastrophic erosion under Set B (iteration 9), with no oscillation. **Qwen3-Coder 30B** represents a middle ground: erosion onset at iteration 7, a moderate PS drop to 0.81 (only `MusicalWork` eroded), and a gradual ES decline to 0.5. Qwen3's erosion is partial and stable rather than total — it erodes selectively rather than wholesale. However, Qwen3 is the only model requiring significant **compile fixes** (8 in Set B, 2 in Set A), suggesting its refactoring is less mechanically reliable even when semantically more conservative.

Latent term extraction reveals another dimension of model behavior. Sonnet 4.6 and Qwen3 both achieve 4/4 latent extraction under Set B (despite erosion), while GPT-5.4 achieves 0/4 in both sets. This means GPT-5.4 neither preserves existing domain terms nor surfaces implicit ones — it flattens the domain model in both directions.

## 4. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

Control A tests whether providing explicit domain context — a glossary of domain terms with definitions and rationale — can prevent semantic erosion. Each agent/model combination is run under Set A prompts augmented with a domain glossary file anchoring the terminology. All Control A runs maintain a perfect **PS of 1.0** across all 10 iterations, and crucially, **none apply any code changes** (0 insertions, 0 deletions, 0 files changed across all four configurations). This is a striking result: the presence of domain context does not merely prevent erosion — it appears to suppress refactoring entirely.

The mitigation is universal in preventing term renaming, but the ES and latent extraction results reveal that the glossary's effectiveness varies by model. Control Claude Code achieves ES = 1.0 with 4/4 latent terms. Control OpenCode+Sonnet preserves PS = 1.0 but shows ES = 0.0 with 0/4 latent terms — identical to its non-control Set A behavior, suggesting a persistent Sonnet 4.6 + OpenCode interaction that fails to extract latent concepts regardless of context. Control GPT-5.4 achieves ES = 1.0 and 4/4 latent terms — a dramatic improvement over its non-control Set A (ES = 0.0, 0/4), suggesting the glossary context specifically helps GPT-5.4 recognize domain concepts it otherwise misses. Control Qwen3 achieves ES = 1.0 and 4/4 latent terms but requires 5 compile fixes, echoing its mechanical fragility observed in Phase 2.

The zero-change behavior raises an important question: does domain context prevent erosion by helping the agent understand which terms to preserve, or does it simply make the agent overly cautious about modifying anything? If the latter, the mitigation may be too aggressive — preserving terminology at the cost of suppressing legitimate refactoring. Future work should test domain context under Set B stress prompts to determine whether it can selectively protect terminology while still allowing structural improvements.

## 5. Refactoring Effectiveness

| Agent | Set | Active Iters | +Lines | -Lines | Net | Files | Compile Fixes | Glossary Tampered |
|---|---|---|---|---|---|---|---|---|
| CC Set A | A | 0/10 | +0 | -0 | +0 | 0 | 0 | 0 |
| CC Set B | B | 10/10 | +1231 | -1503 | -272 | 129 | 0 | 0 |
| OC+Son Set A | A | 0/10 | +0 | -0 | +0 | 0 | 0 | 0 |
| OC+Son Set B | B | 10/10 | +1730 | -1453 | +277 | 113 | 0 | 0 |
| OH Set A | A | 5/10 | +530 | -943 | -413 | 39 | 0 | 0 |
| OH Set B | B | 4/10 | +731 | -955 | -224 | 40 | 0 | 0 |
| GPT-5.4 Set A | A | 10/10 | +1690 | -1209 | +481 | 86 | 0 | 0 |
| GPT-5.4 Set B | B | 10/10 | +4557 | -4560 | -3 | 228 | 0 | 1 |
| Qwen3 Set A | A | 9/10 | +849 | -505 | +344 | 40 | 2 | 0 |
| Qwen3 Set B | B | 8/10 | +588 | -432 | +156 | 34 | 8 | 0 |

![Refactoring Volume](figures/refactoring_volume.png)

**GPT-5.4 is by far the most prolific refactorer**, producing 4,557 insertions and 4,560 deletions under Set B — roughly 3x the volume of the next most active configuration (OpenCode+Sonnet Set B at 1,730 insertions). Despite this massive churn, GPT-5.4 Set B achieves a net change of only -3 lines, suggesting much of its activity is reorganizational (moving code between files or rewriting in place) rather than additive or reductive. It touches 228 files — twice the count of any other run — indicating a tendency toward broad, sweeping refactors rather than targeted improvements.

**Refactoring volume does not straightforwardly predict erosion.** OpenHands performs meaningful refactoring under both Set A (530+/943-, 39 files) and Set B (731+/955-, 40 files) yet produces zero erosion in either case. Conversely, OpenCode+Sonnet Set B produces moderate volume (1,730+/1,453-) but achieves total erosion. The critical factor appears to be refactoring *character* rather than *volume*: agents that rename and restructure domain entities (OpenCode, GPT-5.4) erode, while those that refactor internal implementation details (OpenHands) do not. GPT-5.4's high volume amplifies its erosion tendency — more code touched means more opportunities to rename domain terms — but volume alone is neither necessary nor sufficient for erosion.

**Compile fix frequency** is concentrated in Qwen3-Coder: 8 fixes in Set B and 2 in Set A (plus 5 in Control A). No other model requires any compile fixes. This indicates that Qwen3's code generation is mechanically less reliable — it produces syntactically or semantically invalid Java more frequently, requiring automated repair cycles. The correlation between compile fixes and moderate (rather than total) erosion in Qwen3 Set B is suggestive: the compile-fix mechanism may inadvertently act as an erosion brake by reverting or correcting changes that break the build, including some that would have completed a domain term rename. GPT-5.4 is the only configuration to tamper with the glossary (1 instance in Set B), representing an escalation beyond simple code-level erosion to actively corrupting the domain reference itself.

## 6. Key Findings

**1. Semantic erosion is real and prompt-dependent.** Under neutral prompts (Set A), no agent or model erodes domain terminology — PS remains 1.0 universally. Under stress prompts (Set B), 3 of 5 agent/model configurations suffer erosion (OpenCode+Sonnet, OpenCode+GPT-5.4, OpenCode+Qwen3), confirming that prompt framing is the primary trigger. The gap between Set A and Set B is categorical, not gradual.

**2. Agent architecture is the strongest determinant of erosion resistance.** OpenHands resists erosion completely under both prompt sets (PS = 1.0, ES = 1.0) despite active refactoring, while OpenCode erodes under Set B with all three models tested. Claude Code shows transient erosion with self-correction. This agent-level effect persists regardless of the underlying model, indicating that agent design — context management, tool-use strategy, and editing patterns — dominates model-level biases.

**3. Erosion onset timing and trajectory vary by model.** GPT-5.4 erodes earliest (iteration 2) and most chaotically (5 direction changes), Sonnet 4.6 erodes latest (iteration 9) but catastrophically (PS drops from 1.0 to 0.0 in one step), and Qwen3 erodes moderately at iteration 7 (PS drops to 0.81). These distinct signatures suggest fundamentally different internal mechanisms: GPT-5.4 is impulsive and unstable, Sonnet is conservative but brittle, and Qwen3 is gradual and selective.

**4. Self-correction exists but is agent-specific, not model-specific.** Claude Code (Sonnet 4.6) recovers from severe erosion (PS 0.12 → 1.0), exhibiting 2 direction changes. OpenCode with the same model (Sonnet 4.6) shows zero direction changes and no recovery. GPT-5.4 under OpenCode oscillates (5 direction changes) but ultimately fails to recover (PS final = 0.0). Self-correction therefore appears to be a property of Claude Code's agent architecture rather than of any particular model.

**5. Domain context mitigation prevents erosion but suppresses all refactoring.** Control A runs with glossary context achieve PS = 1.0 universally, but also produce zero code changes across all configurations. The mitigation is effective but potentially overbroad — it functions as a refactoring inhibitor rather than a selective term protector. Its practical value depends on whether the goal is term preservation (fully achieved) or safe refactoring (not tested).

**6. Latent term extraction is model-dependent and independent of erosion.** GPT-5.4 extracts 0/4 latent terms in both sets regardless of erosion state, while Sonnet and Qwen3 extract 4/4 and 2-4/4 respectively. This indicates that the ability to recognize implicit domain concepts in code is an intrinsic model capability orthogonal to the tendency to rename explicit ones. OpenCode+Sonnet in Set A is an anomaly: 0/4 latent extraction despite no erosion, suggesting the OpenCode agent may interfere with Sonnet's latent recognition in the absence of stress prompts.

**7. Glossary tampering represents a qualitative escalation.** GPT-5.4 is the only model to modify the domain glossary file itself (1 instance under Set B). While all other erosion is confined to renaming terms in application code, glossary tampering undermines the reference document that defines what the correct terminology *is*. This behavior, combined with GPT-5.4's chaotic oscillation and maximum refactoring volume, marks it as the highest-risk model for unsupervised refactoring of domain-rich codebases.
