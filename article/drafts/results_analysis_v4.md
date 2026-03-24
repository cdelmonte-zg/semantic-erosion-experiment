# Semantic Erosion Experiment — Results Analysis v4.1

**Date:** 2026-03-21
**Status:** Phase 1 complete, Phase 2 partial (GPT-5.4 complete, Qwen3 pending)

---

## 1. Executive Summary

The experiment confirms that semantic erosion is **prompt-triggered and
agent-dependent**, not an intrinsic property of LLMs. With neutral
refactoring prompts, no agent erodes domain terminology. With stress
prompts that explicitly invite renaming, erosion occurs — but its severity
depends on the agent architecture, not just the model.

The domain context mitigation (GLOSSARY.yaml reference in prompt)
completely prevents erosion across all tested configurations.

---

## 2. Phase 1 Results — Isolate the Agent

**Fixed variable:** Model (Claude Sonnet 4.6)
**Varied variable:** Agent (Claude Code, OpenCode)

### Set A — Neutral Prompts ("Refactor to improve readability")

| Agent       | Run 1 | Run 2 | Run 3 | Min PS | Erosion? |
|-------------|-------|-------|-------|--------|----------|
| Claude Code | 1.0   | 1.0   | 1.0   | 1.0    | NO       |
| OpenCode    | 1.0   | 1.0   | 1.0   | 1.0    | NO       |

**Finding 1: Neutral refactoring prompts never cause erosion.**
Both agents preserve every materialized domain term across all
iterations. The agents also correctly extract latent terms (ES=1.0)
with the correct domain names from GLOSSARY.yaml.

### Set B — Stress Prompts ("Simplify class names", "Rename anything overly specific")

| Agent       | Run 1 min PS | Run 2 min PS | Run 3 min PS | Erosion? |
|-------------|-------------|-------------|-------------|----------|
| Claude Code | **0.12**    | **0.69**    | **0.0**     | **YES**  |
| OpenCode    | **0.0**     | —           | —           | **YES**  |

**Finding 2: Stress prompts cause erosion, but severity is agent-dependent.**

- **Claude Code** erodes most aggressively: PS drops to 0.0-0.12 at
  specific iterations (prompt "Rename anything overly specific"),
  then recovers to 1.0 on the next iteration ("Refactor to improve
  readability"). The oscillatory pattern is consistent across 3 runs.

- **OpenCode** erodes late: PS=1.0 for 8 iterations, then drops to
  0.0 at iterations 9-10. Less aggressive than Claude Code.



**Finding 3: The oscillatory erosion pattern.**
Erosion is not monotonic — it oscillates with the prompt cycle.
Destructive prompts ("rename anything overly specific") cause PS
to crash. Constructive prompts ("refactor to improve readability")
restore domain terms. The same agent both destroys and rebuilds
the ubiquitous language depending on the prompt.

This means a single "cleanup" prompt can undo months of careful
domain naming in one pass — but the damage is reversible if the
next prompt is constructive.

**Finding 4: Agent architecture matters.**
The difference between Claude Code and OpenCode erosion patterns may be related to:
- How each agent orchestrates LLM calls (single-shot vs multi-step)
- How each agent presents the codebase context
- Whether adaptive thinking is enabled (Claude Code enables it by
  default; OpenCode does not)

### Control A — Domain Context Mitigation

| Agent       | Run 1 | Run 2 | Run 3 | Min PS | Erosion? |
|-------------|-------|-------|-------|--------|----------|
| Claude Code | 1.0   | 1.0   | 1.0   | 1.0    | NO       |

**Finding 5: Domain context completely prevents erosion.**
Adding "Preserve all domain terms defined in GLOSSARY.yaml" to the
prompt maintains PS=1.0 across all iterations, even with stress prompts.
The agents still improve code structure but do not rename domain terms.

---

## 3. Phase 2 Results — Isolate the Model

**Fixed variable:** Agent (OpenCode)
**Varied variable:** Model (Sonnet 4.6, GPT-5.4, Qwen3-Coder 30B)

### Set A — Neutral Prompts

| Model          | PS    | ES   | Latent Extracted | Erosion? |
|----------------|-------|------|------------------|----------|
| Sonnet 4.6     | 1.0   | 1.0  | 4/4              | NO       |
| GPT-5.4        | 1.0   | None | 0/4              | NO       |
| Qwen3-Coder 30B| —     | —    | —                | NOT TESTED|

**Finding 6: Model capability affects refactoring depth, not erosion.**
Sonnet 4.6 extracts all 4 latent terms correctly (ES=1.0).
GPT-5.4 preserves all materialized terms but does not extract any
latent terms (0/4). Both preserve PS=1.0 — no erosion with neutral prompts.

### Set B — Stress Prompts

| Model          | Min PS | PS=0.0 count | Erosion? |
|----------------|--------|-------------|----------|
| Sonnet 4.6     | 0.0    | 2/10        | YES      |
| GPT-5.4        | 0.0    | **5/10**    | **YES, MORE AGGRESSIVE** |
| Qwen3-Coder 30B| —      | —           | NOT TESTED|

**Finding 7: GPT-5.4 erodes more aggressively than Sonnet 4.6.**
With stress prompts, GPT-5.4 reaches PS=0.0 in 5 out of 10 iterations,
compared to 2/10 for Sonnet 4.6 via OpenCode. The oscillatory pattern
is present but more extreme — GPT-5.4 alternates between total
destruction (PS=0.0) and complete restoration (PS=1.0).

### Control A — Domain Context with GPT-5.4

| Model   | PS    | All iterations | Erosion? |
|---------|-------|----------------|----------|
| GPT-5.4 | 1.0   | 10/10          | NO       |

**Finding 8: Domain context protects against GPT-5.4 erosion too.**
The GLOSSARY.yaml reference in the prompt prevents erosion across
models, not just across agents. The mitigation is model-independent.

---

## 4. Emergence Score (ES) Analysis

| Configuration          | ES    | Latent Extracted |
|------------------------|-------|------------------|
| Claude Code Set A      | 1.0   | 1-4/4            |
| OpenCode+Sonnet Set A  | 1.0   | 4/4              |
| OpenCode+GPT-5.4 Set A | None  | 0/4              |
| OpenCode+GPT-5.4 Set B | 0.0-1.0 | 0-4/4 (oscillates) |

**Finding 9: Correct emergence requires sufficient model capability.**
Sonnet 4.6 consistently extracts latent terms with the correct domain
names from GLOSSARY.yaml. GPT-5.4 either doesn't extract them (Set A)
or extracts them with mixed correctness (Set B). When GPT-5.4 does
extract latent terms, it sometimes uses incorrect names (ES=0.0)
but sometimes gets them right (ES=1.0) — further evidence of
the oscillatory, non-deterministic nature of LLM refactoring.

---

## 5. Key Takeaways for the Article

### The central sentence:
> "Each individual rename is plausible. The cumulative effect is erosion."

### Actionable advice for teams:
1. **Never use prompts that mention "simplify names" or "rename"** when
   working with domain-rich code. Use neutral refactoring prompts.
2. **Always provide domain context** (GLOSSARY.yaml) when using AI
   coding assistants on DDD projects.
3. **The CI guardrail works**: a PS threshold check on every PR catches
   erosion before it reaches production.
4. **Agent choice matters**: some agents are structurally more resistant
   to erosion than others, independent of the underlying model.

### What's novel:
- Erosion is **prompt-triggered**, not intrinsic
- Erosion is **oscillatory**, not monotonic
- Erosion is **agent-dependent**, not just model-dependent
- Domain context **completely prevents** erosion
- GPT-5.4 erodes **more aggressively** than Sonnet 4.6

---

## 6. Limitations

1. **Qwen3-Coder 30B (local)**: Not tested due to OpenCode integration
   issues with Ollama. The capability threshold hypothesis remains
   untested for local models in this experiment version.

2. **Adaptive thinking asymmetry**: Claude Code enables adaptive thinking
   by default (up to 32K thinking tokens). OpenCode does not.
   This is a confounding variable in Phase 1.

3. **Single run for OpenCode**: Cost constraints limited
   OpenCode Set B to 1 run. Variance is measured
   only on Claude Code (3 runs, free via Max subscription).

4. **Prompt set design**: Set B prompts explicitly invite renaming
   ("rename anything overly specific"). A Set C with realistic but
   less explicit prompts would strengthen the finding.

---

## 7. Cost Summary

| Provider   | Spent   | Budget  | Remaining |
|------------|---------|---------|-----------|
| Anthropic  | ~$45    | $50     | ~$5       |
| OpenAI     | ~$3     | $10     | ~$7       |
| Claude Max | $0      | (subsc.)| unlimited |
| Ollama     | $0      | (local) | unlimited |
