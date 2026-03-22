# Semantic Erosion Experiment — Results Report

Generated: 2026-03-22 14:48

## 1. Results Summary

<!-- AI:intro -->
<!-- /AI -->

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

## 4. Control A — Domain Context Mitigation

![Control A](figures/control_a.png)

<!-- AI:control_a -->
<!-- /AI -->

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

<!-- AI:refactoring -->
<!-- /AI -->

## 6. Key Findings

<!-- AI:findings -->
<!-- /AI -->

