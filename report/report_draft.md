# Semantic Erosion Experiment — Results Report

Generated: 2026-03-24 13:36

## 1. Results Summary

<!-- AI:intro -->
<!-- /AI -->

| Agent / Model | Set | PS min | PS final | ES final | Latent | Erosion Onset | +Lines | -Lines | Compile Fixes |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +781 | -566 | 0 |
| Claude Code | B | 0.00 | 0.69 | 0.25 | 1/4 | iter 2 | +2227 | -2329 | 0 |
| OpenCode (Sonnet 4.6) | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1299 | -891 | 0 |
| OpenCode (Sonnet 4.6) | B | 0.00 | 0.00 | 0.00 | 0/4 | iter 2 | +3438 | -3395 | 0 |
| OpenCode + GPT-5.4 | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +1688 | -971 | 0 |
| OpenCode + GPT-5.4 | B | 0.00 | 1.00 | 0.75 | 3/4 | iter 2 | +6377 | -6289 | 0 |
| OpenCode + Qwen3 30B | A | 1.00 | 1.00 | 0.75 | 3/4 | — | +515 | -405 | 0 |
| OpenCode + Qwen3 30B | B | 0.83 | 1.00 | 0.50 | 2/4 | iter 2 | +461 | -431 | 6 |
| Claude Code | C | 1.00 | 1.00 | 0.50 | 2/4 | — | +836 | -921 | 0 |
| OpenCode (Sonnet 4.6) | C | 1.00 | 1.00 | 0.75 | 3/4 | — | +1402 | -1252 | 0 |
| OpenCode + GPT-5.4 | C | 1.00 | 1.00 | 0.50 | 2/4 | — | +1794 | -1663 | 0 |
| OpenCode + Qwen3 30B | C | 0.38 | 0.38 | 0.75 | 3/4 | iter 9 | +636 | -940 | 5 |
| Ctrl-A: Claude Code | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +760 | -591 | 0 |
| Ctrl-A: OC+Sonnet | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +1237 | -675 | 0 |
| Ctrl-A: OC+GPT-5.4 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +1248 | -1058 | 0 |
| Ctrl-A: OC+Qwen3 | A | 1.00 | 1.00 | 1.00 | 4/4 | — | +1044 | -353 | 1 |
| Ctrl-B: Claude Code | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +806 | -892 | 0 |
| Ctrl-B: OC+Sonnet | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +1002 | -774 | 0 |
| Ctrl-B: OC+GPT-5.4 | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +1497 | -1131 | 0 |
| Ctrl-B: OC+Qwen3 | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +502 | -323 | 6 |
| Permissive: Claude Code | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +918 | -855 | 0 |
| Permissive: OC+GPT-5.4 | B | 1.00 | 1.00 | 1.00 | 4/4 | — | +1565 | -1235 | 0 |

## 2. Phase 1 — Agent Comparison (Claude Sonnet 4.6)

<!-- AI:phase1 -->
<!-- /AI -->

### 2.1 Set A (Neutral Prompts)

![Phase 1 Set A](figures/phase1_setA.png)

### 2.2 Set B (Stress Prompts)

![Phase 1 Set B](figures/phase1_setB.png)

<!-- AI:phase1_analysis -->
<!-- /AI -->

![Claude Code Set B Heatmap](figures/heatmap_claude_code_B.png)

![OpenCode (Sonnet) Set B Heatmap](figures/heatmap_opencode_B.png)

## 3. Phase 2 — Model Comparison (OpenCode agent)

<!-- AI:phase2 -->
<!-- /AI -->

### 3.1 Set A (Neutral)

![Phase 2 Set A (Neutral)](figures/phase2_setA.png)

### 3.2 Set B (Stress)

![Phase 2 Set B (Stress)](figures/phase2_setB.png)

![GPT-5.4 Heatmap](figures/heatmap_opencode_gpt-5.4_B.png)

![Qwen3-Coder 30B Heatmap](figures/heatmap_opencode_qwen3-coder_B.png)

<!-- AI:phase2_analysis -->
<!-- /AI -->

## 4. Phase 3 — Set C (Implicit Rename Pressure)

<!-- AI:setc -->
<!-- /AI -->

![Set C](figures/phase3_setC.png)

<!-- AI:setc_analysis -->
<!-- /AI -->

## 5. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

<!-- AI:control_a -->
<!-- /AI -->

## 6. Control B — Domain Context Under Stress

![Control B](figures/control_b.png)

<!-- AI:control_b -->
<!-- /AI -->

## 7. Permissive Context — Balancing Protection and Refactoring

![Permissive Context](figures/permissive.png)

<!-- AI:permissive -->
<!-- /AI -->

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
| Qwen3 Set B | B | 8/10 | +461 | -431 | +30 | 43 | 6 | 0 |
| Qwen3 Set C | C | 7/10 | +636 | -940 | -304 | 44 | 5 | 0 |

![Refactoring Volume](figures/refactoring_volume.png)

<!-- AI:refactoring -->
<!-- /AI -->

## 9. Key Findings

<!-- AI:findings -->
<!-- /AI -->

