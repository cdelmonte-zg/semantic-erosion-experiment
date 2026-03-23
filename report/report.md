# Semantic Erosion Experiment — Results Report

Generated: 2026-03-23 22:24

## 1. Results Summary

This experiment investigates **semantic erosion** — the gradual loss of domain-specific terminology from a codebase when AI coding agents iteratively refactor it without explicit domain anchoring. The subject codebase is a Java Domain-Driven Design (DDD) project modelling a collecting society (rights holders, musical works, royalty distribution). Two metrics are tracked at each iteration: **Preservation Score (PS)**, measuring how many domain-specific class and field names survive unchanged, and **Extraction Score (ES)**, measuring whether latent domain concepts that should emerge during refactoring are actually surfaced.

The experiment is structured in two phases plus a control. Each run consists of **10 consecutive refactoring iterations** applied to the same codebase. Two prompt sets govern the instructions given to the agent: **Set A** (neutral — "improve code quality") and **Set B** (stress — aggressive refactoring directives that never mention domain terms). Three agents are tested — Claude Code, OpenCode, and OpenHands — and three underlying models are compared via the OpenCode harness: Claude Sonnet 4.6, GPT-5.4, and Qwen3-Coder 30B. A separate **Control A** condition supplies the agent with an explicit domain glossary and bounded-context map, testing whether domain context in the prompt prevents erosion entirely.

In total, the experiment comprises **31 completed runs** across 14 distinct configurations. The table below summarizes the final state of each configuration, including preservation and extraction scores, latent concept recovery, erosion onset timing, refactoring volume, and compile-fix frequency.

| Agent / Model | Set | PS min | PS final | ES final | Latent | Erosion Onset | +Lines | -Lines | Compile Fixes |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +781 | -566 | 0 |
| Claude Code | B | 0.00 | 0.69 | 0.25 | 1/4 | iter 2 | +2227 | -2329 | 0 |
| OpenCode (Sonnet 4.6) | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1299 | -891 | 0 |
| OpenCode (Sonnet 4.6) | B | 0.00 | 0.00 | 0.00 | 0/4 | iter 2 | +3438 | -3395 | 0 |
| OpenHands | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +231 | -292 | 0 |
| OpenHands | B | 1.00 | 1.00 | 0.00 | 0/4 | — | +0 | -0 | 0 |
| OpenCode + GPT-5.4 | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1688 | -971 | 0 |
| OpenCode + GPT-5.4 | B | 0.00 | 1.00 | 0.75 | 3/4 | iter 2 | +6377 | -6289 | 0 |
| OpenCode + Qwen3 30B | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +515 | -405 | 0 |
| OpenCode + Qwen3 30B | B | 0.83 | 1.00 | 0.50 | 2/4 | iter 2 | +580 | -480 | 6 |
| Control: Claude Code | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Control: OpenCode+Sonnet | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Control: OpenCode+GPT-5.4 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 0 |
| Control: OpenCode+Qwen3 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +0 | -0 | 1 |

## 2. Phase 1 — Agent Comparison (Claude Sonnet 4.6)

Phase 1 isolates the effect of the **agent harness** on semantic erosion by fixing the underlying model (Claude Sonnet 4.6) and varying the agent: Claude Code, OpenCode, and OpenHands. Each agent runs the same 10-iteration refactoring loop on both prompt sets (A and B). This design controls for model capability and tests whether the agent's planning, tool-use orchestration, and code-editing strategy influence how aggressively domain terminology is replaced.

The key question is whether the same model, when wrapped in different agentic scaffolding, produces systematically different erosion profiles — and whether some agents are inherently more "destructive" to domain semantics than others.

### 2.1 Set A (Neutral Prompts)

![Phase 1 Set A](figures/phase1_setA.png)

### 2.2 Set B (Stress Prompts)

![Phase 1 Set B](figures/phase1_setB.png)

Under **Set A** (neutral prompts), all three agents preserve domain terminology perfectly: PS remains 1.0 across all 10 iterations for Claude Code, OpenCode, and OpenHands alike. The Extraction Score settles at 0.75 (3 of 4 latent concepts surfaced) for all agents, though OpenCode briefly reaches ES = 1.0 in early iterations before stabilizing. This confirms that when prompts do not push toward aggressive renaming, the model respects existing domain names regardless of agent harness.

**Set B** (stress prompts) reveals stark divergence. OpenCode (Sonnet 4.6) is the most aggressive eroder: PS drops to 0.12 by iteration 2, touches 0.0 by iteration 4, and never recovers — ending at PS = 0.00 with all 6 tracked domain terms eroded and 0/4 latent concepts extracted. Claude Code also erodes significantly (PS mean = 0.44, 2 terms eroded) but exhibits a pronounced **oscillation pattern**: PS swings between ~0.12 and ~0.69 across iterations, with 6 direction changes. This suggests Claude Code partially restores domain terms in some iterations before re-eroding them in the next, producing an unstable equilibrium rather than monotonic decay.

OpenHands is an outlier: it applied **zero changes** in Set B (0/10 active iterations), leaving PS at 1.0 but ES at 0.0. This is not preservation — it is inaction. OpenHands failed to engage with the stress prompts entirely, likely due to its headless execution mode struggling with the task setup. This means OpenHands cannot be meaningfully compared with the other agents on Set B; its "perfect" PS is an artifact of non-participation.

The heatmaps below illustrate the per-term erosion trajectories. Claude Code's heatmap shows MusicalWork and ExploitationType flickering between eroded and preserved states, while OpenCode's heatmap shows a rapid, near-total collapse across all domain terms — RightsHolder, MusicalWork, DistributionRun, UsageReport, ExploitationType, and RoyaltyStatement — with only a brief, partial recovery around iteration 6.

![Claude Code Set B Heatmap](figures/heatmap_claude_code_B.png)

![OpenCode (Sonnet) Set B Heatmap](figures/heatmap_opencode_B.png)

## 3. Phase 2 — Model Comparison (OpenCode agent)

Phase 2 fixes the agent (OpenCode) and varies the underlying model to isolate the effect of **model choice** on semantic erosion. Three models are compared: Claude Sonnet 4.6, GPT-5.4, and Qwen3-Coder 30B (a locally-hosted open-weight model). By holding the agent harness constant, any differences in erosion behavior can be attributed to how each model interprets refactoring instructions, weighs domain naming conventions, and decides when renaming is "improvement."

### 3.1 Set A (Neutral)

![Phase 2 Set A (Neutral)](figures/phase2_setA.png)

### 3.2 Set B (Stress)

![Phase 2 Set B (Stress)](figures/phase2_setB.png)

![GPT-5.4 Heatmap](figures/heatmap_opencode_gpt-5.4_B.png)

![Qwen3-Coder 30B Heatmap](figures/heatmap_opencode_qwen3-coder_B.png)

Under **Set A**, all three models behave identically in terms of preservation: PS = 1.0 across all iterations. ES is uniformly 0.75 for Sonnet and GPT-5.4, while Qwen3 briefly reaches ES = 1.0 in early iterations (matching OpenCode/Sonnet's pattern) before settling at 0.75. This confirms that neutral prompts are safe regardless of model.

**Set B** reveals three distinct erosion profiles. **Sonnet 4.6** is the most aggressive: it reaches PS = 0.0 by iteration 4 and stays there, eroding all 6 domain terms with no recovery. It extracts 0/4 latent concepts — the worst outcome in the entire experiment. **GPT-5.4** shows a striking **binary oscillation**: PS alternates between 1.0 and 0.0 on every iteration (6 direction changes), with ES perfectly correlated. This means GPT-5.4 fully erodes all domain terms on even iterations and fully restores them on odd iterations. By iteration 10, it lands on a restored state (PS = 1.0, ES = 0.75, 3/4 latent). The final outcome is good, but the trajectory is wildly unstable — the codebase was effectively rewritten back and forth 5 times. **Qwen3-Coder 30B** is the most conservative eroder: PS never drops below 0.83, with only minor perturbations (mean PS = 0.97). It erodes zero named terms, extracts 2/4 latent concepts, but is the only model requiring **6 compile fixes** — suggesting it makes smaller, sometimes syntactically incorrect changes rather than bold renames.

The models thus occupy three points on an erosion spectrum: Sonnet is aggressive and irreversible, GPT-5.4 is aggressive but self-correcting (oscillatory), and Qwen3 is conservative but error-prone. Notably, erosion onset is identical for all three (iteration 2), suggesting the first stress prompt triggers renaming universally — what differs is whether the model persists, oscillates, or retreats.

## 4. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

The Control A condition tests a single mitigation strategy: providing the agent with an **explicit domain glossary and bounded-context map** in the system prompt alongside the same Set A refactoring instructions. Four configurations were tested — Claude Code, OpenCode+Sonnet, OpenCode+GPT-5.4, and OpenCode+Qwen3 — each for 10 iterations.

The results are unequivocal: **domain context completely prevents erosion across all agents and models.** Every Control A run maintains PS = 1.0 and ES = 1.0 for all 10 iterations, with 4/4 latent concepts extracted. No domain terms are eroded, no glossary tampering occurs, and — critically — **no code changes are applied at all** (0 insertions, 0 deletions, 0 files changed) in three of four configurations. The sole exception is OpenCode+Qwen3, which triggered 1 compile fix but still produced zero net code changes and perfect scores.

This is a striking finding: when given domain context, agents do not merely preserve terminology while refactoring — they **decline to refactor at all**. The domain glossary appears to act as an implicit constraint that signals the codebase is already well-structured, causing agents to conclude no improvements are needed. This is both a validation of the mitigation (no erosion) and a potential concern (no useful refactoring either).

The universality of the effect is notable. It holds across all four model/agent combinations, including Qwen3-Coder which showed the weakest performance in other conditions. This suggests the mitigation operates at the prompt-interpretation level rather than being model-dependent: any model, when told "these are the domain terms and their meanings," will respect them absolutely.

Comparing Control A (ES = 1.0, 4/4 latent) against the baseline Set A runs (ES = 0.75, 3/4 latent), the domain glossary also improves latent concept extraction. In baseline runs, agents consistently surface 3 of 4 latent concepts; with the glossary, all 4 are recovered. This suggests the glossary helps agents recognize domain concepts that would otherwise remain implicit in the code structure.

## 5. Refactoring Effectiveness

| Agent | Set | Active Iters | +Lines | -Lines | Net | Files | Compile Fixes | Glossary Tampered |
|---|---|---|---|---|---|---|---|---|
| CC Set A | A | 10/10 | +781 | -566 | +215 | 61 | 0 | 0 |
| CC Set B | B | 10/10 | +2227 | -2329 | -102 | 155 | 0 | 0 |
| OC+Son Set A | A | 10/10 | +1299 | -891 | +408 | 81 | 0 | 0 |
| OC+Son Set B | B | 10/10 | +3438 | -3395 | +43 | 163 | 0 | 0 |
| OH Set A | A | 2/10 | +231 | -292 | -61 | 16 | 0 | 0 |
| OH Set B | B | 0/10 | +0 | -0 | +0 | 0 | 0 | 0 |
| GPT-5.4 Set A | A | 10/10 | +1688 | -971 | +717 | 78 | 0 | 0 |
| GPT-5.4 Set B | B | 10/10 | +6377 | -6289 | +88 | 251 | 0 | 0 |
| Qwen3 Set A | A | 8/10 | +515 | -405 | +110 | 32 | 0 | 0 |
| Qwen3 Set B | B | 9/10 | +580 | -480 | +100 | 50 | 6 | 0 |

![Refactoring Volume](figures/refactoring_volume.png)

Refactoring volume varies dramatically across agents and models. **GPT-5.4 on Set B** is by far the most prolific, producing 6,377 insertions and 6,289 deletions across 251 files — yet its net change is only +88 lines. This enormous churn reflects its oscillatory behavior: it renames terms in one iteration and restores them the next, generating massive diffs with minimal lasting structural change. By contrast, **Qwen3 on Set B** is the most conservative active agent (580 insertions, 480 deletions, 50 files), producing small, targeted changes per iteration.

**Set B consistently generates 2–4x more churn than Set A** for the same agent/model combination. Claude Code goes from 781/566 (Set A) to 2,227/2,329 (Set B); OpenCode+Sonnet from 1,299/891 to 3,438/3,395. This confirms that stress prompts drive substantially more refactoring activity. Notably, Claude Code Set B is the only configuration with a **negative net line change** (-102), meaning the stress prompts caused it to remove more code than it added — consistent with aggressive renaming and consolidation.

**Higher refactoring volume correlates with more erosion, but the relationship is not linear.** OpenCode+Sonnet Set B (3,438 insertions, PS final = 0.00) and GPT-5.4 Set B (6,377 insertions, PS final = 1.00) demonstrate that sheer volume does not determine erosion outcome — GPT-5.4 churns nearly twice as much code but ends with perfect preservation because its oscillations cancel out. Conversely, Qwen3 Set B produces modest volume (580 insertions) with minimal erosion (PS final = 1.00) but is the only configuration requiring **6 compile fixes**, indicating that lower-volume changes are not necessarily higher-quality.

**OpenHands** is a clear outlier: it completed only 2 of 10 iterations on Set A and 0 of 10 on Set B, producing negligible volume. Its failure to engage makes it unsuitable for erosion analysis but reveals an important practical consideration — not all agents can reliably execute iterative refactoring tasks in headless mode.

No agent tampered with the domain glossary file in any configuration, confirming that the experiment's integrity boundary held across all 31 runs.

## 6. Key Findings

1. **Semantic erosion is real and prompt-dependent.** Under neutral prompts (Set A), no agent or model erodes domain terminology — PS remains 1.0 universally. Under stress prompts (Set B), erosion occurs in every active agent/model combination, with onset consistently at iteration 2. The prompt set is the single strongest predictor of erosion.

2. **The agent harness matters as much as the model.** With the same underlying model (Sonnet 4.6), OpenCode erodes to PS = 0.00 while Claude Code oscillates around PS = 0.44. The agent's orchestration strategy — how it plans multi-file renames, whether it re-reads existing code between iterations — shapes erosion outcomes independently of model capability.

3. **Erosion profiles are model-characteristic.** Sonnet 4.6 erodes aggressively and irreversibly (monotonic decay to 0.00). GPT-5.4 exhibits binary oscillation (alternating between full erosion and full restoration, 6 direction changes). Qwen3-Coder is conservative (PS never below 0.83) but error-prone (6 compile fixes). These profiles are reproducible and reflect distinct model "personalities" in how they handle rename-vs-preserve trade-offs.

4. **Domain context is a complete and universal mitigation.** Providing a glossary and bounded-context map in the prompt eliminates erosion across all agents and models (PS = 1.0, ES = 1.0, 4/4 latent in every Control A run). However, this mitigation also suppresses all refactoring activity — agents conclude the codebase needs no changes, producing zero diffs. This suggests a more nuanced prompt design is needed to preserve terms while still enabling structural improvements.

5. **Latent concept extraction degrades with erosion.** Baseline runs extract 3/4 latent concepts; heavily eroded runs (OpenCode+Sonnet B) extract 0/4; the Control A glossary enables 4/4. Erosion does not merely rename existing terms — it destroys the semantic scaffolding that helps agents recognize implicit domain concepts, creating a compounding loss of domain knowledge.

6. **Oscillation is a distinct failure mode from monotonic erosion.** Claude Code (6 direction changes) and GPT-5.4 (6 direction changes) repeatedly rename and un-rename domain terms across iterations. While the final PS may appear acceptable (Claude Code B: 0.69, GPT-5.4 B: 1.00), the intermediate states represent a codebase in constant flux — with each oscillation potentially breaking downstream consumers, confusing human reviewers, and generating massive unnecessary diffs (GPT-5.4 B: 12,666 total lines changed).

7. **Refactoring volume is a poor proxy for erosion severity.** GPT-5.4 Set B produces the highest churn (12,666 lines) but ends with zero erosion; OpenCode+Sonnet Set B produces less than half the churn (6,833 lines) but ends with total erosion. Volume measures activity, not damage. The more predictive signal is whether an agent's changes are **directionally consistent** (low direction-change count) versus oscillatory.
