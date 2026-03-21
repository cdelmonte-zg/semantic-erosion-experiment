# Experiment Design v4 — Glossary-Driven Semantic Erosion Detection

## Overview

This experiment measures whether AI coding agents systematically erode
domain-specific terminology when applied iteratively without domain context.
It uses a glossary-driven evaluation framework with weighted, stateful term
tracking.

## Metrics

### Preservation Score (PS)

Measures retention of the 6 initially materialized domain terms.

    PS = sum(weight_i * location_weight_i) / sum(weight_i)
        for all terms where initial_state = materialized

**location_weight** is the max weight across all locations where the term
appears:

| Location         | Weight |
|------------------|--------|
| class_name       | 1.0    |
| interface_name   | 1.0    |
| enum_name        | 1.0    |
| record_name      | 1.0    |
| method_name      | 0.6    |
| field_name       | 0.6    |
| parameter_name   | 0.3    |
| local_variable   | 0.3    |

PS = 1.0 at baseline (all materialized terms present as types).

### Emergence Score (ES)

Measures correct materialization of the 4 latent domain terms.

    ES = sum(weight_i * 1.0) / sum(weight_i)
        for latent terms that were extracted (correctly or erroneously)

ES is `null` when no latent terms have been extracted (nothing to score).

### extraction_ratio

    extraction_ratio = latent_extracted / latent_total

Where `latent_extracted` counts latent terms that appeared as types (either
correctly materialized or eroded). Value is 0.0 when no latent terms have
been extracted.

## Term States (6)

| State                    | Meaning                                               |
|--------------------------|-------------------------------------------------------|
| MATERIALIZED             | Domain term present as a type name (initial for 6)    |
| LATENT                   | Concept exists but no dedicated type (initial for 4)  |
| CORRECTLY_MATERIALIZED   | Latent term emerged with correct domain name          |
| DEGRADED                 | Domain term lost from types, survives in methods/fields |
| ERODED                   | Generic equivalent found in place of domain term      |
| DISAPPEARED              | Neither domain term nor generic equivalent found      |

## Agent Matrix

| Agent        | Mode           | Automation  | Model                   |
|--------------|----------------|-------------|-------------------------|
| Claude Code  | CLI, agentic   | Full (bash) | Sonnet 4 (cloud)        |
| OpenCode     | CLI, agentic   | Full (bash) | Configurable            |
| OpenHands    | CLI, headless  | Full (bash) | Gemini 2.5 Flash (cloud)|

## Prompt Sets

- **Set A (neutral):** `prompts_neutral.txt` -- generic refactoring prompts
  without domain-triggering language.
- **Set B (stress):** `prompts_stress.txt` -- prompts that explicitly invite
  renaming and simplification.

Each set contains 5 prompts, cycled across 10 iterations.

## Controls

- **Control A:** Same prompts with domain context prefix from
  `context_prompt.txt`. Tests whether explicit domain awareness mitigates
  erosion.

## Results Directory Structure

    results/<agent>/<prompt_set>/run-<n>/iteration-<i>.json
    results/control_a/<agent>/<prompt_set>/run-<n>/iteration-<i>.json

## Experiment Lifecycle

1. **Configure:** Edit `experiment/experiment.yaml` to define agents, prompt
   sets, number of runs.
2. **Validate glossary:** `python experiment/validate_glossary.py
   collecting-society/GLOSSARY.yaml`
3. **Run:** `./experiment/run_all.sh` (or `--dry-run` to preview).
4. **Measure:** Happens automatically per iteration via `measure_fidelity.py`.
5. **Check thresholds:** `python experiment/check_threshold.py --from-json
   <result.json> --min-ps 0.9 --min-es 0.5`
6. **Analyze:** Review per-term state transitions across iterations.

TODO: Add smoke test for DistributionService

## Phase 2b (Planned) — Extended Thinking Variant

**Question:** Does extended thinking preserve domain language better,
or does it produce more plausible (and therefore more dangerous)
semantic erosion?

**Setup:**
- Agent: Claude Code (same as Phase 1)
- Model: Sonnet 4.6 with extended thinking enabled
- Prompt set: A (neutral) only
- Runs: 1 × 5 iterations (subset — cost control)
- Control: compare against Phase 1 Claude Code results

**Metrics to add:**
- Thinking token count per iteration
- Compare PS/ES against standard Sonnet 4.6 runs

**When to run:** After Phase 1 + Phase 2 results are analyzed.
Decision based on whether standard runs show erosion.

**Rationale:** If extended thinking reduces erosion → practical advice
("give more cognitive budget"). If it produces more coherent erosion →
stronger capability threshold finding. Both outcomes are publishable.

## Known Asymmetry: Adaptive Thinking

Claude Code enables adaptive thinking by default on Sonnet 4.6
(up to 32K thinking tokens per prompt). OpenCode and OpenHands call
the Anthropic API without the `thinking` parameter, which defaults
to thinking disabled.

This means Claude Code gets more "cognitive budget" per iteration,
which may contribute to:
- More aggressive refactoring decisions
- More coherent cross-file renames
- Higher token consumption per iteration

This asymmetry reflects real-world usage — developers use tools
with their default configurations. It is documented as a known
variable, not controlled for in Phase 1.

If future work isolates this variable, the question becomes:
"Does adaptive thinking preserve domain language better, or does
it produce more plausible semantic erosion?"
