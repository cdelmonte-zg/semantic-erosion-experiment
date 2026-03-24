# Semantic Erosion Experiment

Do AI coding agents gradually erase domain-specific terminology when refactoring code?

This experiment measures **semantic erosion** — the loss of Domain-Driven Design (DDD) ubiquitous language when AI agents iteratively refactor a Java codebase. A collecting society rights management system serves as the subject, with domain terms like `RightsHolder`, `MusicalWork`, `DistributionRun` tracked across 10 refactoring iterations.

## TL;DR

- **Set A** (neutral prompts): no erosion — all agents and models preserve domain terms perfectly
- **Set B** (explicit rename pressure): erosion occurs, severity depends on agent and model
- **Set C** (implicit pressure): only Qwen3 30B erodes (late onset at iteration 9) — cloud models resist
- **Domain context** (strict or permissive): prevents erosion completely while enabling refactoring

## Key Findings

| Finding | Evidence |
|---------|----------|
| In this experiment, neutral prompts did not cause erosion | All agent-model combinations maintained PS=1.0 across 10 iterations |
| Stress prompts caused agent-dependent erosion | OpenCode+Sonnet crashed to PS=0.0; Claude Code oscillated to PS=0.69 |
| GPT-5.4 eroded aggressively but recovered completely | PS near-binary oscillation 0↔1, ended at 1.0 with 0 permanently eroded terms |
| Implicit pressure revealed a capability threshold | Cloud models (Sonnet, GPT-5.4) resisted; Qwen3 30B eroded at iteration 9 |
| Domain context prevented erosion while enabling refactoring | All controls: PS=1.0 with substantial code changes (+760 to +1497 lines) |

Full results in [`report/report.md`](report/report.md).

## Experimental Design

**Phase 1** — Agent comparison: Claude Code vs OpenCode, both using Claude Sonnet 4.6
**Phase 2** — Model comparison: Sonnet 4.6 vs GPT-5.4 vs Qwen3-Coder 30B, all via OpenCode
**Phase 3** — Implicit pressure: Set C prompts that suggest renaming without using the word "rename"
**Controls** — Domain context (glossary) provided to test erosion mitigation

### Prompt Sets

Representative examples from each set (5 prompts per set, cycled over 10 iterations; see `experiment/prompts_*.txt` for full sets):

- **Set A (neutral):** "Refactor this project to improve readability."
- **Set B (stress):** "Clean up this codebase. Rename anything that seems overly specific."
- **Set C (implicit):** "Some class names seem unusual. Align them with standard Java patterns."

### Metrics

- **Preservation Score (PS):** Fraction of materialized domain terms retained (1.0 = all preserved, 0.0 = all lost)
- **Emergence Score (ES):** Correct extraction of latent domain concepts from code smells

## Project Structure

```
collecting-society/     Java DDD codebase (experiment subject)
  GLOSSARY.yaml         Domain vocabulary — ground truth for metrics
  src/                  12 Java files with 10 intentional code smells
experiment/
  experiment.yaml       Run configuration (agents, models, prompt sets)
  run_all.sh            Orchestrator — runs all configured experiments
  run_experiment.sh     Single-run executor (10 iterations per run)
  measure_fidelity.py   PS/ES metrics via tree-sitter AST parsing
  generate_report.py    Report generator (tables + charts + AI analysis)
results/                Per-iteration JSON results: <agent>/<model>/<set>/run-<n>/
report/                 Generated report, charts, data summary
```

## Quick Start

### Prerequisites

- Python 3.12+, Java 17+, Maven
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and/or [OpenCode](https://opencode.ai)
- API keys for Anthropic and/or OpenAI (in `~/.config/api_keys.env`)
- Optional: [Ollama](https://ollama.ai) with Qwen3-Coder for local model runs

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
# Preview what would run
./experiment/run_all.sh --dry-run

# Run all experiments (skips already-completed runs)
./experiment/run_all.sh

# Run a single agent/set combination
./experiment/run_experiment.sh claude_code B 10 1

# Generate report from results
python experiment/generate_report.py
```

### Reproducing the Published Results

The repository includes all 28 run results (308 iteration JSONs). To regenerate the report and charts from existing data without re-running experiments:

```bash
source .venv/bin/activate
python experiment/generate_report.py    # tables + charts + AI analysis
```

Re-running experiments requires active API keys and, for Qwen3 runs, a local Ollama instance with `qwen3-coder-experiment` (30B, Q4_K_M quantization on NVIDIA RTX 4090, 24GB VRAM).

## Agents and Models

| Agent | Description | Adaptive Thinking |
|-------|-------------|-------------------|
| Claude Code | Anthropic's CLI agent | Yes (up to 32K tokens) |
| OpenCode | Open-source CLI agent | No |

| Model | Provider | Type |
|-------|----------|------|
| Claude Sonnet 4.6 | Anthropic (cloud) | Phase 1 baseline + Phase 2 |
| GPT-5.4 | OpenAI (cloud) | Phase 2 |
| Qwen3-Coder 30B | Ollama (local, Q4_K_M quantization) | Phase 2 |

## The Subject Codebase

A synthetic collecting society domain model (royalty distribution for musical works) built with strict DDD ubiquitous language. The codebase contains 10 intentional code smells that invite refactoring, including:

- **God Class** (DistributionService, 170 lines)
- **Primitive Obsession** (raw `LocalDate` pairs instead of `SettlementPeriod`)
- **Data Clumps** (loose fields instead of `RightsShare` value object)
- **Switch on Type** (tariff rates via switch instead of enum field)

The glossary defines 6 **materialized terms** (existing types) and 4 **latent terms** (concepts that should emerge through refactoring). This allows measuring both erosion and correct domain concept extraction.

## Known Limitations

- **Adaptive thinking asymmetry:** Claude Code enables extended thinking by default (up to 32K tokens); OpenCode does not. This is a confounding variable in Phase 1.
- **Permissive context tested on 2 configurations only:** Claude Code + Sonnet and OpenCode + GPT-5.4. Qwen3 — the most erosion-prone model — was not tested under permissive context.
- **Single run for most configurations:** Cost constraints limited most runs to 1 replica. Qwen3 has 3 replicas due to high observed variance.

## License

MIT License for code. CC-BY 4.0 for results and report.
