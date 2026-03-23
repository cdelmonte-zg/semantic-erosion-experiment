# Semantic Erosion Experiment — Results Report

Generated: 2026-03-23 22:34

## 1. Results Summary

This report presents results from 31 experimental runs across 3 prompt sets (A: neutral, B: stress, C: implicit rename pressure), 2 functional agents (Claude Code, OpenCode), and 3 backend models (Sonnet 4.6, GPT-5.4, Qwen3 30B). OpenHands was also tested but produced zero code changes in headless mode and is excluded from comparative analysis -- its apparent erosion resistance is an artifact of non-functionality, not robustness.

The core finding is that semantic erosion is prompt-dependent, not agent-dependent. Under neutral prompts (Set A), all agent-model combinations maintain PS=1.0 across 10 iterations. Under stress prompts (Set B), erosion onset occurs at iteration 2 for every vulnerable configuration. The severity gap between models is dramatic: OpenCode+Sonnet erodes to PS=0.0 final, Claude Code oscillates between 0.0 and 0.69, while GPT-5.4 self-corrects back to PS=1.0. Qwen3 30B shows high inter-run variance, with PS dipping to 0.83 in one replica but remaining at 1.0 in others.

Control runs (both A and B) with domain context in the system prompt produce zero code changes across all 8 agent-model combinations -- zero insertions, zero deletions, zero files touched. This demonstrates that domain context does not merely prevent renaming; it completely inhibits refactoring. The permissive context variant, designed to allow structural changes while protecting names, also produces zero changes, confirming that even softened domain constraints suppress all agent activity.

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

Phase 1 compares three agents -- Claude Code, OpenCode, and OpenHands -- all backed by Claude Sonnet 4.6. The goal is to isolate the effect of the agent harness (prompt routing, tool use, edit strategy) from the underlying model. OpenHands is included for completeness but must be interpreted with caution: it produced zero code changes under Set B (0 insertions, 0 deletions, 0 files changed), indicating a failure to engage with the task rather than successful preservation.

Under Set A (neutral prompts), both Claude Code and OpenCode maintain perfect PS=1.0 throughout. They diverge in refactoring volume: OpenCode generates +1299/-891 lines across 81 files, while Claude Code is more conservative at +781/-566 across 61 files. Both show ES=0.75 (3/4 latent terms extracted), indicating comparable structural understanding of the domain.

### 2.1 Set A (Neutral Prompts)

![Phase 1 Set A](figures/phase1_setA.png)

### 2.2 Set B (Stress Prompts)

![Phase 1 Set B](figures/phase1_setB.png)

Under Set B (stress prompts), the agent harness matters significantly. OpenCode+Sonnet suffers catastrophic erosion: PS drops to 0.12 at iteration 2 and never recovers, ending at PS=0.0 with all 6 tracked domain terms renamed (RightsHolder, MusicalWork, DistributionRun, UsageReport, ExploitationType, RoyaltyStatement). Latent extraction also collapses to 0/4, meaning the model loses not just the names but the ability to reason about domain concepts.

Claude Code shows a qualitatively different pattern. PS also drops at iteration 2, but it oscillates: the curve reads 1.0, 0.12, 0.69, 0.19, 0.19, 0.69, 0.0, 0.69, 0.12, 0.69. This oscillation (6 direction changes) suggests Claude Code partially self-corrects in alternating iterations, though it never fully recovers to PS=1.0. The final PS=0.69 with only 2 eroded terms (MusicalWork, ExploitationType) represents a middle ground -- erosion occurs but is contained. In v4.2 of this experiment, Claude Code was able to self-correct fully back to PS=1.0 when the GLOSSARY was visible; in v4.3 with the GLOSSARY hidden, this self-correction is incomplete.

The heatmaps reveal the spatial pattern of erosion. OpenCode renames broadly and persistently, while Claude Code's erosion is patchy and intermittent, consistent with the oscillating PS curve.

![Claude Code Set B Heatmap](figures/heatmap_claude_code_B.png)

![OpenCode (Sonnet) Set B Heatmap](figures/heatmap_opencode_B.png)

## 3. Phase 2 — Model Comparison (OpenCode agent)

Phase 2 holds the agent constant (OpenCode) and varies the backend model: Sonnet 4.6, GPT-5.4, and Qwen3 30B. This isolates the model's intrinsic resistance to semantic erosion from the agent's scaffolding.

Under Set A, all three models maintain PS=1.0 across all iterations. Refactoring volume varies substantially: GPT-5.4 is the most active (+1688/-971 lines, 78 files), Sonnet is moderate (+1299/-891, 81 files), and Qwen3 is the most conservative (+515/-405, 32 files with only 8/10 active iterations). Despite these differences, all achieve equivalent preservation scores, confirming that neutral prompts do not trigger erosion regardless of model.

### 3.1 Set A (Neutral)

![Phase 2 Set A (Neutral)](figures/phase2_setA.png)

### 3.2 Set B (Stress)

![Phase 2 Set B (Stress)](figures/phase2_setB.png)

![GPT-5.4 Heatmap](figures/heatmap_opencode_gpt-5.4_B.png)

![Qwen3-Coder 30B Heatmap](figures/heatmap_opencode_qwen3-coder_B.png)

Under Set B, model differences become stark. Sonnet 4.6 erodes catastrophically (PS final=0.0, 6/6 terms renamed, 0/4 latent). GPT-5.4 erodes and self-corrects in a dramatic oscillating pattern: PS alternates between 0.0 and 1.0 across iterations (6 direction changes), ultimately recovering to PS=1.0 final with 3/4 latent terms. This self-correction behavior is unique to GPT-5.4 and suggests the model has strong internal priors about domain naming that reassert themselves even after stress-induced renaming. The cost of this oscillation is massive churn: +6377/-6289 lines across 251 files, the highest refactoring volume in the entire experiment.

Qwen3 30B presents a different profile. Its PS minimum is 0.83 (not 0.0), indicating it never fully succumbs to stress prompts. However, Qwen3 shows high variance across 3 replicas: one run maintains PS=1.0 throughout, while another dips to 0.83. The model also requires 6 compile fixes, suggesting lower code generation reliability. Its final PS=1.0 masks this instability -- the mean PS of 0.97 better reflects its actual behavior. Qwen3's conservative refactoring volume (+580/-480) may partly explain its resilience: it simply changes less code per iteration, reducing the surface area for erosion.

## 4. Phase 3 — Set C (Implicit Rename Pressure)

Set C tests implicit rename pressure: prompts that do not explicitly request renaming but use alternative terminology that could nudge the model toward synonym substitution. This is a subtler and arguably more realistic threat model than Set B's direct stress prompts.

Cloud models (Sonnet 4.6, GPT-5.4) and Claude Code all maintain PS=1.0 throughout Set C. None of them rename any tracked domain terms. The implicit pressure is insufficient to overcome their naming stability. However, latent extraction scores vary: Claude Code ends at ES=0.5 (2/4), OpenCode+Sonnet at ES=0.75 (3/4), and GPT-5.4 at ES=0.5 (2/4), suggesting that implicit pressure may degrade deeper domain understanding even when surface names are preserved.

![Set C](figures/phase3_setC.png)

Qwen3 30B is the sole model vulnerable to implicit rename pressure. Its PS holds at 1.0 for 8 iterations, then drops sharply to 0.42 at iteration 9 and 0.38 at iteration 10. Three domain terms are eroded (RightsHolder, DistributionRun, RoyaltyStatement), and 5 compile fixes are required. This late-onset erosion pattern -- stable for most of the run, then sudden collapse -- is distinct from Set B's immediate erosion at iteration 2. It suggests that Qwen3 accumulates implicit pressure across iterations until a tipping point is reached.

Across 3 replicas of the Qwen3 Set C run, 2 out of 3 show this erosion pattern (PS dropping to ~0.38), while the behavior in the aggregate confirms Qwen3 as the only model susceptible to implicit rename pressure. This finding is significant because implicit pressure is the most common real-world scenario: developers rarely ask an AI to "rename MusicalWork to Song," but they might consistently use colloquial synonyms in their prompts. Qwen3's vulnerability here, combined with its high variance, makes it the least predictable model in the experiment.

## 5. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

Control A adds domain context (a glossary of canonical term definitions) to the system prompt, then runs Set A (neutral) prompts. The result is unambiguous: all four agent-model combinations (Claude Code, OpenCode+Sonnet, OpenCode+GPT-5.4, OpenCode+Qwen3) produce exactly zero code changes. Zero insertions, zero deletions, zero files modified. PS=1.0 and ES=1.0 across all 10 iterations for every run.

This is a stronger result than expected. The hypothesis was that domain context would prevent renaming while allowing structural refactoring to proceed. Instead, domain context completely suppresses all refactoring activity. The agents interpret the glossary as a signal that the codebase should not be modified at all, not merely that names should be preserved. This over-inhibition effect is consistent across all models, including Qwen3 which otherwise shows the weakest naming discipline. The only anomaly is Qwen3 requiring 1 compile fix despite making no code changes, likely from an attempted edit that was rolled back.

## 6. Control B — Domain Context Under Stress

![Control B](figures/control_b.png)

Control B is the critical test: domain context combined with Set B stress prompts. If domain context can protect naming under adversarial conditions, this is where it must prove itself. The result mirrors Control A exactly: zero code changes across all four agent-model combinations. PS=1.0, ES=1.0, zero insertions, zero deletions, 10/10 iterations with no modifications.

This confirms that domain context is a fully effective shield against semantic erosion -- but at the cost of total refactoring paralysis. Even under stress prompts that would otherwise cause catastrophic erosion (PS=0.0 for OpenCode+Sonnet, oscillating for Claude Code and GPT-5.4), the presence of domain context in the system prompt prevents any agent from touching the code. Qwen3 again shows 6 compile fixes with zero net changes, reinforcing that it attempts modifications but consistently fails or rolls them back when domain context is present. The protection is absolute but the trade-off is clear: you cannot have domain-context protection and useful refactoring simultaneously with current agent architectures.

## 7. Permissive Context — Balancing Protection and Refactoring

![Permissive Context](figures/permissive.png)

The permissive context variant was designed to address the over-inhibition problem discovered in Controls A and B. Instead of a strict glossary, it provides softer guidance: "these domain terms should be preserved, but structural improvements are welcome." The goal was to find a middle ground where agents refactor freely but respect canonical names.

The result is disappointing: permissive context also produces zero code changes. Despite the explicitly permissive wording, agents still interpret the presence of any domain naming guidance as a prohibition on modification. This suggests the over-inhibition is not caused by the strictness of the wording but by the mere existence of domain constraints in the system prompt. Current agent architectures appear to have a binary response to domain context -- either they ignore it entirely (when absent) or they treat it as a do-not-touch directive (when present in any form). Finding a calibration point between these two extremes remains an open problem.

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

Refactoring volume varies dramatically across models and is not correlated with erosion resistance. GPT-5.4 produces the highest churn in every prompt set: +6377/-6289 under Set B (the experiment maximum), +1794/-1663 under Set C, and +1688/-971 under Set A. This hyperactivity is linked to its oscillating self-correction pattern -- it renames, then undoes, then renames again, inflating line counts without net structural progress (Set B net: +88 lines).

Qwen3 30B sits at the opposite extreme with the lowest refactoring volume across all sets (+515/-405 for Set A, +580/-480 for Set B, +636/-940 for Set C). It also has the fewest active iterations (8/10, 9/10, 7/10 respectively) and is the only model requiring compile fixes (6 in Set B, 5 in Set C). The negative net in Set C (-304 lines) is unusual and coincides with its late-onset erosion, suggesting the renaming process involved deleting code that referenced old names without fully recreating it under new names.

Claude Code and OpenCode+Sonnet occupy the middle ground. Claude Code is consistently more conservative than OpenCode on the same model (Sonnet 4.6): +781 vs +1299 insertions under Set A, +2227 vs +3438 under Set B. No agent or model tampered with the glossary file in any run, confirming that erosion operates purely through code modifications rather than by altering the reference definitions.

## 9. Key Findings

**1. Semantic erosion is prompt-triggered, not inevitable.** Under neutral prompts (Set A), every agent-model combination maintains PS=1.0 for 10 iterations. Erosion requires explicit or implicit rename pressure in the prompt.

**2. Erosion severity is model-dependent.** Under identical stress prompts (Set B) and agent (OpenCode), Sonnet 4.6 erodes to PS=0.0 (catastrophic, irreversible), GPT-5.4 oscillates between 0.0 and 1.0 (self-correcting), and Qwen3 30B dips minimally to 0.83 (high variance across replicas). The agent harness also matters: Claude Code partially contains erosion that is catastrophic under OpenCode with the same Sonnet model.

**3. Qwen3 30B is uniquely vulnerable to implicit pressure.** Set C (implicit rename) causes no erosion in Sonnet 4.6, GPT-5.4, or Claude Code, but Qwen3 erodes to PS=0.38 in 2 out of 3 replicas. The erosion onset is late (iteration 9), suggesting accumulated pressure rather than immediate susceptibility. This makes Qwen3 the most unpredictable model: high variance, late-onset failures, and the only model affected by subtle synonym pressure.

**4. Domain context is a complete but blunt mitigation.** All 8 control runs (Controls A and B) produce zero code changes. Domain context in the system prompt does not selectively protect naming -- it suppresses all refactoring. The permissive context variant, designed to allow structural changes while protecting names, also produces zero changes. Current agent architectures cannot distinguish between "preserve these names" and "do not touch this code."

**5. GLOSSARY visibility affects self-correction.** In v4.2 (GLOSSARY visible), Claude Code self-corrected fully from erosion back to PS=1.0. In v4.3 (GLOSSARY hidden), Claude Code oscillates between PS=0.0 and 0.69 but never recovers to 1.0. The GLOSSARY serves as an anchor that enables recovery, not just prevention.

**6. OpenHands results are artifacts.** OpenHands produces PS=1.0 under Set B with zero code changes (0 insertions, 0 deletions). This is not erosion resistance -- it is a failure of the headless runtime to execute the refactoring task at all. OpenHands should be excluded from any comparative claims about agent robustness.

