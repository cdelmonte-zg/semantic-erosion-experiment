# Semantic Erosion Experiment

Do AI coding agents gradually erase domain-specific terminology when refactoring code?

This experiment measures **semantic erosion** — the loss of Domain-Driven Design (DDD) ubiquitous language when AI agents iteratively refactor a Java codebase. A collecting society rights management system serves as the subject, with domain terms like `RightsHolder`, `MusicalWork`, `DistributionRun` tracked across 10 refactoring iterations.

## Key Findings

| Finding | Evidence |
|---------|----------|
| Neutral prompts never cause erosion | All agent-model combinations maintain PS=1.0 across 10 iterations |
| Stress prompts cause agent-dependent erosion | OpenCode+Sonnet crashes to PS=0.0; Claude Code oscillates to PS=0.69 |
| GPT-5.4 erodes aggressively but recovers completely | PS alternates 0↔1, ends at 1.0 with 0 permanently eroded terms |
| Implicit pressure reveals a capability threshold | Cloud models (Sonnet, GPT-5.4) resist; Qwen3 30B erodes at iteration 9 |
| Domain context prevents erosion but kills refactoring | All controls: PS=1.0 but 0 code changes — context inhibition effect |

Full results in [`report/report.md`](report/report.md).

## Experimental Design

**Phase 1** — Agent comparison: Claude Code vs OpenCode, both using Claude Sonnet 4.6
**Phase 2** — Model comparison: Sonnet 4.6 vs GPT-5.4 vs Qwen3-Coder 30B, all via OpenCode
**Phase 3** — Implicit pressure: Set C prompts that suggest renaming without using the word "rename"
**Controls** — Domain context (glossary) provided to test erosion mitigation

### Prompt Sets

- **Set A (neutral):** "Refactor this project to improve readability."
- **Set B (stress):** "Clean up this codebase. Rename anything that seems overly specific."
- **Set C (implicit):** "Some class names seem unusual. Align them with standard Java patterns."

### Metrics

- **Preservation Score (PS):** Fraction of materialized domain terms retained (1.0 = all preserved)
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
results/                Per-iteration JSON results by agent/model/set
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

### Results

Each iteration produces a JSON file with per-term tracking:

```
results/<agent>/<model>/<prompt_set>/run-<n>/iteration-<i>.json
```

## Agents and Models

| Agent | Description | Adaptive Thinking |
|-------|-------------|-------------------|
| Claude Code | Anthropic's CLI agent | Yes (up to 32K tokens) |
| OpenCode | Open-source CLI agent | No |

| Model | Provider | Type |
|-------|----------|------|
| Claude Sonnet 4.6 | Anthropic (cloud) | Phase 1 baseline + Phase 2 |
| GPT-5.4 | OpenAI (cloud) | Phase 2 |
| Qwen3-Coder 30B | Ollama (local) | Phase 2 |

## The Subject Codebase

A synthetic collecting society domain model (royalty distribution for musical works) built with strict DDD ubiquitous language. The codebase contains 10 intentional code smells that invite refactoring, including:

- **God Class** (DistributionService, 170 lines)
- **Primitive Obsession** (raw `LocalDate` pairs instead of `SettlementPeriod`)
- **Data Clumps** (loose fields instead of `RightsShare` value object)
- **Switch on Type** (tariff rates via switch instead of enum field)

The glossary defines 6 **materialized terms** (existing types) and 4 **latent terms** (concepts that should emerge through refactoring). This allows measuring both erosion and correct domain concept extraction.

## License

Research project. Results and methodology are available for academic use.
