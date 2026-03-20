# Semantic Erosion Experiment Design

## Objective

Empirically demonstrate that AI coding assistants systematically erode
domain-specific terminology when applied iteratively without domain context,
and propose a drift-detection mechanism modeled on MLOps practices.

---

## 1. Synthetic Project: Collecting Society Domain

### Why synthetic?
- Full control over the Ubiquitous Language
- No proprietary code
- Reproducible by readers
- Clean baseline (100% domain term coverage at t=0)

### Bounded Context: Rights Distribution

A simplified collecting society system with three aggregates:

```
RightsHolder         (not: User, Account, Owner)
MusicalWork          (not: Item, Asset, Content)
DistributionRun      (not: Job, Process, Batch)
```

### Domain Glossary (ground truth)

#### Primary Terms (10) — shown in charts

| Domain Term           | Semantic Role                              | Generic Equivalent (erosion target) |
|-----------------------|--------------------------------------------|-------------------------------------|
| RightsHolder          | Legal entity holding exploitation rights   | User, Account, Owner                |
| MusicalWork           | Registered copyrighted composition         | Item, Asset, Content, Track         |
| SettlementPeriod      | Contractual accounting interval            | DateRange, Period, TimeSpan         |
| DistributionRun       | Periodic royalty calculation execution      | Job, Process, Batch, Run            |
| UsageReport           | Documented exploitation of a work          | Report, Record, Log, Event          |
| TariffClass           | Rate category for exploitation type        | Category, Type, Tier, PriceLevel    |
| ExploitationType      | Legal form of work usage (broadcast, etc.) | UsageType, Type, Kind               |
| ClaimShare            | Fractional ownership of a work's rights    | Share, Percentage, Portion          |
| DistributionKey       | Algorithm selecting eligible rights holders| Rule, Filter, Selector, Criteria    |
| RoyaltyStatement      | Per-holder result of a distribution run    | Statement, Invoice, Payout, Result  |

#### Secondary Terms (8) — tracked for granularity, not in headline chart

These add statistical depth: with 18 terms, each is ~5.5% of DTD instead
of 10%, producing smoother erosion curves and reducing sensitivity to
single-term noise.

| Domain Term              | Semantic Role                                  | Generic Equivalent (erosion target)    |
|--------------------------|------------------------------------------------|----------------------------------------|
| calculateRoyalties       | Domain method: compute royalties for a run     | calculate, compute, process, run       |
| applyTariff              | Domain method: apply rate to usage              | applyRate, applyPrice, setPrice        |
| resolveClaimShares       | Domain method: determine fractional ownership   | resolveShares, splitOwnership, divide  |
| registerWork             | Domain method: register a new musical work      | addItem, createAsset, save             |
| fileUsageReport          | Domain method: submit exploitation data         | submitReport, createRecord, logUsage   |
| MandateContract          | Agreement granting exploitation rights          | Contract, Agreement, License           |
| RepertoryEntry           | Work registered in a society's catalog           | CatalogEntry, Entry, Record            |
| PerformanceRoyalty       | Royalty from live/broadcast performance          | Royalty, Payment, Fee                  |

### Project Structure (Java 17, Maven)

```
collecting-society/
├── pom.xml
├── GLOSSARY.yaml                          # ground truth
├── src/main/java/dev/cdelmonte/collecting/
│   ├── rightsholder/
│   │   ├── RightsHolder.java              # Aggregate root
│   │   ├── ClaimShare.java                # Value object
│   │   ├── MandateContract.java           # Entity
│   │   └── RightsHolderRepository.java
│   ├── musicalwork/
│   │   ├── MusicalWork.java               # Aggregate root
│   │   ├── ExploitationType.java          # Enum
│   │   ├── RepertoryEntry.java            # Value object
│   │   └── MusicalWorkRepository.java
│   ├── distribution/
│   │   ├── DistributionRun.java           # Aggregate root
│   │   ├── DistributionKey.java           # Value object
│   │   ├── SettlementPeriod.java          # Value object
│   │   ├── TariffClass.java              # Value object
│   │   ├── RoyaltyStatement.java          # Entity
│   │   ├── PerformanceRoyalty.java         # Value object
│   │   └── DistributionService.java       # Domain service
│   └── usage/
│       ├── UsageReport.java               # Aggregate root
│       └── UsageReportRepository.java
└── src/test/java/...
```

---

## 2. Experiment Protocol

### Agents Under Test

| Agent                    | Mode              | Automation   | Model                     |
|--------------------------|-------------------|--------------|---------------------------|
| Claude Code              | CLI, agentic      | Full (bash)  | Sonnet 4 (cloud)          |
| GitHub Copilot           | VS Code chat      | Manual       | GPT-4o / Claude (cloud)   |
| Aider + Ollama (local)   | CLI, agentic      | Full (bash)  | Qwen3-Coder 30B (local)   |

### Why These Three

- **Claude Code** and **Copilot**: the two most widely adopted AI coding
  assistants in enterprise teams — the audience JavaMagazin readers
  actually use.
- **Aider + Ollama**: a fully local agent running an open-weight model.
  This proves the erosion effect is structural (inherent to how LLMs
  generalize) and not vendor-specific. If a local 30B model erodes
  terminology the same way cloud models do, the argument is airtight.

### Local Agent Setup (RTX 4090, 24GB VRAM)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3-Coder 30B (fits in 24GB VRAM with Q4_K_M quantization)
ollama pull qwen3-coder:30b-a3b-q4_K_M

# Increase context window (default 2k is too small)
cat > Modelfile <<EOF
FROM qwen3-coder:30b-a3b-q4_K_M
PARAMETER num_ctx 16384
PARAMETER temperature 0
EOF
ollama create qwen3-coder-experiment -f Modelfile

# Verify
ollama run qwen3-coder-experiment "Rename this Java class to something more readable: public class SettlementPeriod { ... }"

# Install Aider
pip install aider-chat

# Run Aider with local model
cd collecting-society/
aider --model ollama_chat/qwen3-coder-experiment
```

**Temperature 0** is critical: it minimizes non-determinism across runs,
making results more reproducible. Cloud agents (Claude Code, Copilot)
don't expose temperature controls, so we document this asymmetry.

### Prompt Set (escalating aggressiveness, no domain context)

Each iteration applies ONE prompt. Prompts are ordered from mild to
aggressive to produce a gradual erosion curve rather than a sudden drop.

```
P1: "Review this code and suggest better names for classes and variables."
P2: "Refactor this project to improve readability and naming."
P3: "Make this code more idiomatic Java. Improve naming conventions."
P4: "Simplify the class names and method signatures."
P5: "Clean up this codebase. Rename anything that seems overly specific."
```

**Ordering rationale:** P1-P2 are mild ("suggest", "improve"), P3 is
medium ("idiomatic" implies conformity to generic patterns), P4-P5 are
aggressive ("simplify", "overly specific" explicitly invites erosion).
The cycle repeats for iterations 6-10, applying the same gradient to
already-eroded code.

### Iteration Protocol

```
for agent in [claude_code, copilot, aider_local]:
    checkout clean baseline (git tag v0)
    for i in 1..10:
        apply prompt P[i % 5 + 1] to entire project via agent
        accept ALL suggestions that compile (see compilation gate below)
        capture agent reasoning/commentary → logs/{agent}/iteration-{i}.txt
        git commit -m "iteration-{i}-{agent}"
        run measurement script → record metrics
        # Do NOT reset — erosion is cumulative
```

### Compilation Gate

After each agent response:

1. Run `mvn compile -q`
2. If compilation **succeeds**: accept changes, commit, measure.
3. If compilation **fails**: give the agent ONE auto-fix attempt:
   `"The previous refactoring broke compilation. Here are the errors: {errors}. Fix them without reverting the renames."`
4. If the fix attempt **also fails**: `git checkout .` to revert that
   iteration, log it as `"status": "compilation_failure"`, and proceed
   to the next iteration.

This is realistic — no one accepts code that doesn't compile — and
prevents lost iterations from skewing the curve.

### Agent Reasoning Capture

For each iteration, capture the agent's output text (not just the code
diff) into `logs/{agent}/iteration-{i}.txt`. This provides qualitative
data for the article: *why* did the LLM rename `SettlementPeriod` to
`DateRange`? The reasoning text reveals the generalization bias directly.

- **Claude Code:** stdout is already text — redirect to log file.
- **Aider:** `--verbose` flag captures model reasoning.
- **Copilot:** screenshot the chat panel (manual).

### Automation Scripts

Claude Code and Aider are both CLI tools, so the same harness works:

```bash
#!/bin/bash
# run_agent.sh — Run one agent for N iterations
AGENT=$1      # "claude_code" | "aider_local"
ITERATIONS=10

PROMPTS=(
  "Review this code and suggest better names for classes and variables."
  "Refactor this project to improve readability and naming."
  "Make this code more idiomatic Java. Improve naming conventions."
  "Simplify the class names and method signatures."
  "Clean up this codebase. Rename anything that seems overly specific."
)

git checkout v0 -b "experiment/${AGENT}"

for i in $(seq 1 $ITERATIONS); do
  PROMPT="${PROMPTS[$(( (i - 1) % 5 ))]}"
  LOG_DIR="logs/${AGENT}"
  mkdir -p "$LOG_DIR"

  if [ "$AGENT" == "claude_code" ]; then
    claude --dangerously-skip-permissions -p "$PROMPT" 2>&1 | tee "${LOG_DIR}/iteration-${i}.txt"
  elif [ "$AGENT" == "aider_local" ]; then
    echo "$PROMPT" | aider --model ollama_chat/qwen3-coder-experiment \
      --yes-always --no-auto-commits --verbose 2>&1 | tee "${LOG_DIR}/iteration-${i}.txt"
  fi

  # Compilation gate
  if mvn compile -q 2>/dev/null; then
    git add -A
    git commit -m "iteration-${i}-${AGENT}"
  else
    ERRORS=$(mvn compile 2>&1 | tail -30)
    FIX_PROMPT="The previous refactoring broke compilation. Fix these errors without reverting the renames: ${ERRORS}"

    if [ "$AGENT" == "claude_code" ]; then
      claude --dangerously-skip-permissions -p "$FIX_PROMPT" 2>&1 | tee -a "${LOG_DIR}/iteration-${i}.txt"
    elif [ "$AGENT" == "aider_local" ]; then
      echo "$FIX_PROMPT" | aider --model ollama_chat/qwen3-coder-experiment \
        --yes-always --no-auto-commits --verbose 2>&1 | tee -a "${LOG_DIR}/iteration-${i}.txt"
    fi

    if mvn compile -q 2>/dev/null; then
      git add -A
      git commit -m "iteration-${i}-${AGENT}-fixed"
    else
      git checkout .
      echo '{"status": "compilation_failure"}' > "results/${AGENT}/iteration-${i}-failed.json"
    fi
  fi

  python experiment/measure_dtd.py \
    --glossary GLOSSARY.yaml \
    --source src/ \
    --agent "$AGENT" \
    --iteration "$i" \
    --output "results/${AGENT}/iteration-${i}.json"
done
```

For **Copilot**, the same prompts are entered manually in VS Code Chat.
After each response, accept all suggestions, commit, and run the
measurement script. Document each step with screenshots for the article.

### Repeated Runs for Cloud Agents

Cloud agents (Claude Code, Copilot) don't expose temperature controls,
introducing non-determinism. To account for this:

- Run the full 10-iteration experiment **3 times** per cloud agent.
- Report **mean DTD + standard deviation** at each iteration.
- If variance is low (< 0.05), the erosion pattern is robust.
- If variance is high, the non-determinism itself is a finding.

**Cost estimate:** 3 runs x 10 iterations x 2 cloud agents = 60
invocations. At ~$0.50-1.00 per refactoring pass (Sonnet 4), budget
~$30-60 for Claude Code. Copilot is subscription-based, no extra cost.

Aider+Ollama at temperature 0 is deterministic — one run is sufficient.

### Controls

- **Control A (positive):** Same prompts but WITH domain context:
  "Refactor this project to improve readability. Preserve all domain
  terms defined in GLOSSARY.yaml. This is a collecting society system."
  Run with all three agents to show that context mitigates erosion.
- **Control B (local vs cloud):** Compare Aider+Ollama at temperature 0
  (deterministic) vs temperature 0.7 (default). If erosion patterns
  are similar, non-determinism is not the driver — generalization is.

---

## 3. Measurement

### 3.1 Domain Term Density (DTD)

The primary metric. Ratio of glossary terms present in identifiers.

```
DTD = |glossary_terms ∩ code_identifiers| / |glossary_terms|
```

At t=0, DTD = 1.0 (all 18 terms present).
Erosion = DTD declining over iterations.

DTD is reported at two levels:
- **DTD-10:** primary terms only (for the headline chart)
- **DTD-18:** all terms including secondary (for statistical depth)

### 3.2 Semantic Distance (primary, not optional)

For each renamed term, compute cosine similarity between the original
and replacement using sentence-transformers embeddings:

```
semantic_distance("RightsHolder", "User") = 1 - cosine_sim(embed(a), embed(b))
```

This gives a **continuous** erosion metric alongside the binary DTD.
A term like `RightsHolder` → `RightsOwner` has low distance (partial
erosion) while `RightsHolder` → `User` has high distance (full erosion).

**Use in the article:**
- DTD is the headline number (simple, visual, charts well)
- Semantic distance is the depth layer (shows erosion is a gradient)
- Per-term distance heatmap across iterations makes a compelling figure

### 3.3 Extraction Script (Python)

```python
#!/usr/bin/env python3
"""
extract_identifiers.py — Extract all Java identifiers from a project.
Parses .java files, extracts class names, method names, field names,
parameter names, and local variable names using tree-sitter.
"""

# Input:  path to Java source root
# Output: set of identifiers (split by camelCase into constituent terms)

# Key: split CamelCase into words
#   "RightsHolder" → {"rights", "holder"}
#   "User"         → {"user"}
#   "getDateRange" → {"get", "date", "range"}
```

### 3.4 Glossary Match

```python
"""
measure_dtd.py — Compute Domain Term Density at a given commit.

1. Load GLOSSARY.yaml (term → [generic_equivalents])
2. Extract identifiers from source tree
3. For each glossary term:
   a. Check if domain term appears in identifiers → PRESERVED
   b. Check if any generic equivalent appears → ERODED
   c. Neither → DISAPPEARED (term no longer represented)
4. Compute DTD-10, DTD-18, and per-term status
5. For eroded terms, compute semantic distance (original → replacement)
"""
```

### 3.5 Output Format

Per iteration, per agent:

```json
{
  "agent": "claude_code",
  "iteration": 3,
  "run": 1,
  "commit": "a1b2c3d",
  "dtd_10": 0.7,
  "dtd_18": 0.78,
  "terms": {
    "RightsHolder":     { "status": "preserved", "current_name": "RightsHolder", "distance": 0.0 },
    "MusicalWork":      { "status": "eroded",    "current_name": "MusicAsset",   "distance": 0.42 },
    "SettlementPeriod": { "status": "eroded",    "current_name": "DateRange",    "distance": 0.61 },
    "DistributionRun":  { "status": "preserved", "current_name": "DistributionRun", "distance": 0.0 },
    "UsageReport":      { "status": "preserved", "current_name": "UsageReport",  "distance": 0.0 },
    "TariffClass":      { "status": "eroded",    "current_name": "PriceCategory","distance": 0.38 },
    "calculateRoyalties": { "status": "eroded",  "current_name": "compute",      "distance": 0.35 },
    "applyTariff":      { "status": "preserved", "current_name": "applyTariff",  "distance": 0.0 }
  },
  "agent_reasoning_file": "logs/claude_code/iteration-3.txt"
}
```

---

## 4. Expected Results

### Hypothesis

DTD decreases monotonically across iterations for all agents when no
domain context is provided. The rate of erosion varies by agent but the
direction is consistent.

### Expected Erosion Pattern

```
Iteration:  0    1    2    3    4    5    6    7    8    9   10
DTD-10:    1.0  0.9  0.9  0.8  0.7  0.6  0.5  0.5  0.4  0.4  0.3
DTD-18:    1.0  0.94 0.89 0.83 0.78 0.67 0.61 0.56 0.50 0.44 0.39
```

The 18-term DTD produces a smoother curve because each term contributes
~5.5% instead of 10%.

Typical erosion trajectory per term:

```
RightsHolder     → AccountHolder → Owner → User
SettlementPeriod → AccountingPeriod → DateRange
TariffClass      → PriceCategory → Tier
calculateRoyalties → computeRoyalties → calculate → process
```

### Key Charts

#### Chart 1: "Erosion Curves" (the money chart)

X-axis: iteration (0-10)
Y-axis: Domain Term Density (0.0-1.0)
Lines:
  - Claude Code (cloud, large model) — mean + stddev band from 3 runs
  - Copilot (cloud, large model) — mean + stddev band from 3 runs
  - Aider + Qwen3-Coder 30B (local, open-weight) — single run
  - Control A: Claude Code with domain context
  - Control A: Aider with domain context

#### Chart 2: "Semantic Distance Heatmap"

X-axis: iteration (0-10)
Y-axis: domain terms (18 rows)
Color: semantic distance (0.0 = preserved, 1.0 = fully eroded)

This shows *which* terms erode first and how far they drift — more
nuanced than the binary DTD chart.

#### Chart 3: "Agent Reasoning Taxonomy" (qualitative)

A categorized summary of *why* agents renamed terms, based on captured
reasoning logs. Expected categories:
- "More readable" (subjective generalization)
- "Java convention" (appeal to idiom)
- "Overly specific" (explicit domain-to-generic shift)
- "Inconsistent with rest of codebase" (self-reinforcing erosion)

---

## 5. MLOps-Style Solution: Semantic Drift Detection

### Concept Mapping

| MLOps Concept         | Semantic Erosion Equivalent           |
|-----------------------|---------------------------------------|
| Training distribution | Domain glossary (GLOSSARY.yaml)       |
| Live/production data  | Code identifiers at HEAD              |
| Data drift            | Semantic drift (DTD decline)          |
| Drift monitor         | CI check comparing DTD to baseline    |
| Alert threshold       | Minimum acceptable DTD (e.g., 0.8)   |
| Retraining trigger    | Glossary review with domain experts   |

### CI Pipeline (GitHub Actions)

```yaml
name: Semantic Drift Check
on: [pull_request]

jobs:
  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Measure Domain Term Density
        run: python scripts/measure_dtd.py --glossary GLOSSARY.yaml --source src/
      - name: Check threshold
        run: python scripts/check_threshold.py --min-dtd 0.8
```

### GLOSSARY.yaml Format

```yaml
bounded_context: rights-distribution
version: "1.0"
terms:
  - domain_term: RightsHolder
    definition: "Legal entity holding exploitation rights for musical works"
    type: primary
    reject:
      - User
      - Account
      - Owner
      - Person
  - domain_term: SettlementPeriod
    definition: "Contractual accounting interval for royalty calculation"
    type: primary
    reject:
      - DateRange
      - Period
      - TimeSpan
      - Interval
  - domain_term: calculateRoyalties
    definition: "Compute royalties owed to rights holders for a distribution run"
    type: secondary
    reject:
      - calculate
      - compute
      - process
      - run
  # ... etc
```

---

## 6. Repository Structure (for publication)

```
semantic-erosion-experiment/
├── README.md
├── LICENSE
├── collecting-society/           # Synthetic project (Java)
│   ├── pom.xml
│   ├── GLOSSARY.yaml
│   └── src/
├── experiment/
│   ├── prompts.txt               # The 5 prompt templates (ordered by aggressiveness)
│   ├── run_experiment.sh         # Automation script (with compilation gate)
│   ├── extract_identifiers.py    # tree-sitter based extractor
│   ├── measure_dtd.py            # DTD computation + semantic distance
│   ├── check_threshold.py        # CI threshold check
│   └── plot_erosion.py           # Generate erosion curves + heatmap
├── results/
│   ├── claude_code/
│   │   ├── run-1/                # 3 runs for variance analysis
│   │   ├── run-2/
│   │   └── run-3/
│   ├── copilot/
│   │   ├── run-1/
│   │   ├── run-2/
│   │   └── run-3/
│   ├── aider_local/              # Single run (deterministic)
│   ├── control_a/
│   └── control_b_temperature/
├── logs/                         # Agent reasoning capture
│   ├── claude_code/
│   ├── copilot/                  # Screenshots
│   └── aider_local/
└── article/
    └── figures/
        ├── erosion_curves.png    # Chart 1: the money chart
        ├── distance_heatmap.png  # Chart 2: per-term semantic distance
        └── reasoning_taxonomy.png # Chart 3: why agents rename
```

---

## 7. Practical Considerations

### Time Estimate

- Build synthetic project:          4-6 hours
- Ollama setup + model pull:        1 hour
- Run experiment (3 agents x 10):   6-8 hours (scripted runs x3 for cloud agents,
                                               Copilot manual x3)
- Measurement scripts:              2-3 hours
- Analysis + charts:                2-3 hours
- Total:                            ~2 weekends

### Hardware Requirements

- **RTX 4090 (24GB VRAM):** Qwen3-Coder 30B Q4_K_M fits comfortably
  (~18GB VRAM, 6GB left for KV cache).
  Expect ~15-25 tokens/sec for generation, which is fast enough for
  the experiment (each refactoring pass takes 1-3 minutes).
- **RAM:** 32GB+ recommended (Ollama loads model parameters into VRAM,
  but KV cache and system overhead need regular RAM).
- **Disk:** ~20GB for the model file + experiment data.

### Cost Budget

| Item                      | Estimated Cost |
|---------------------------|---------------|
| Claude Code (60 calls)    | $30-60        |
| Copilot (subscription)    | $0 (existing) |
| Aider + Ollama (local)    | $0 (compute)  |
| **Total**                 | **~$30-60**   |

### Risks and Mitigations

1. **Agent refuses to rename:** Some agents might preserve domain terms
   if the code is well-structured. **Mitigation:** prompts escalate in
   aggressiveness (P1→P5). If an agent preserves terms, that's also a
   valid result — document it as agent-specific resistance.

2. **Non-determinism:** LLM outputs vary across runs. **Mitigation:**
   Aider at temperature 0 for deterministic baseline. Cloud agents run
   3x with mean+stddev reported. Document temperature asymmetry as a
   methodological observation, not a limitation.

3. **Agent breaks compilation:** **Mitigation:** compilation gate with
   one auto-fix attempt. If both fail, skip iteration and log failure.
   Compilation failure rate per agent is itself a reportable metric.

4. **Local model too weak:** If Qwen3-Coder 30B can't handle full-project
   refactoring coherently, fall back to file-by-file prompts. This is
   a realistic limitation to document, not hide.

5. **Erosion happens too fast:** If DTD drops to ~0.3 by iteration 3,
   the remaining iterations are flat and uninteresting. **Mitigation:**
   prompt escalation (mild first, aggressive later) produces a more
   gradual curve. If still too fast, the speed itself is the headline
   finding.

6. **Erosion doesn't happen:** If agents consistently preserve domain
   terms, the hypothesis is falsified. **Mitigation:** this is a valid
   result. The article becomes "when and why AI assistants do/don't
   erode domain language" — still publishable and arguably more nuanced.

### What Makes This Publishable

- **Reproducible:** synthetic project + scripts + prompts, all open source
- **Quantitative:** DTD metric + semantic distance with charts, not anecdotes
- **Multi-dimensional:** binary (DTD) + continuous (distance) + qualitative (reasoning)
- **Actionable:** GLOSSARY.yaml + CI check = reader can use Monday morning
- **Novel framing:** MLOps drift detection applied to domain language
- **Cross-agent:** cloud vs local, commercial vs open-weight — structural claim
