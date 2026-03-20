#!/bin/bash
# run_all.sh — Run the complete experiment as defined in experiment.yaml.
#
# Reads experiment.yaml and executes all runs sequentially.
# Skips runs that already have complete results.
#
# Usage:
#   ./experiment/run_all.sh                  # run everything
#   ./experiment/run_all.sh --force          # re-run even if results exist
#   ./experiment/run_all.sh --dry-run        # show what would run

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

source .venv/bin/activate

FORCE=false
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

# Parse experiment.yaml
ITERATIONS=$(python3 -c "import yaml; print(yaml.safe_load(open('experiment/experiment.yaml'))['iterations'])")
MAX_FIX=$(python3 -c "import yaml; print(yaml.safe_load(open('experiment/experiment.yaml'))['max_fix_attempts'])")
RUNS_JSON=$(python3 -c "
import yaml, json
data = yaml.safe_load(open('experiment/experiment.yaml'))
print(json.dumps(data['runs']))
")

TOTAL_RUNS=$(echo "$RUNS_JSON" | python3 -c "import json,sys; runs=json.load(sys.stdin); print(sum(r['runs'] for r in runs))")
COMPLETED=0
SKIPPED=0
FAILED=0

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="experiment_${TIMESTAMP}.log"

log() {
  echo "[$(date +%H:%M:%S)] $1" | tee -a "$LOG_FILE"
}

log "=== Semantic Erosion Experiment ==="
log "Config: ${ITERATIONS} iterations, ${MAX_FIX} fix attempts, ${TOTAL_RUNS} total runs"
log ""

# Iterate over each run definition
RUN_COUNT=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")

for idx in $(seq 0 $((RUN_COUNT - 1))); do
  AGENT=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx]['agent'])")
  TYPE=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx]['type'])")
  NUM_RUNS=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx]['runs'])")

  for run_num in $(seq 1 "$NUM_RUNS"); do
    # Determine results directory
    if [ "$TYPE" == "erosion" ]; then
      SCRIPT="./experiment/run_experiment.sh"
      if [ "$run_num" -gt 1 ]; then
        RESULTS_DIR="results/${AGENT}/run-${run_num}"
      else
        RESULTS_DIR="results/${AGENT}"
      fi
    elif [ "$TYPE" == "control_a" ]; then
      SCRIPT="./experiment/run_control_a.sh"
      if [ "$run_num" -gt 1 ]; then
        RESULTS_DIR="results/control_a_${AGENT}/run-${run_num}"
      else
        RESULTS_DIR="results/control_a_${AGENT}"
      fi
    fi

    # Check if already complete — validate results contain dtd_10 key
    RESULT_COUNT=0
    if [ -d "$RESULTS_DIR" ]; then
      RESULT_COUNT=$(find "$RESULTS_DIR" -name "iteration-*.json" -exec python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if 'dtd_10' in d else 1)" {} \; -print 2>/dev/null | wc -l)
    fi

    if [ "$FORCE" == "false" ] && [ "$RESULT_COUNT" -ge "$ITERATIONS" ]; then
      log "SKIP: ${TYPE}/${AGENT} run ${run_num} — already has ${RESULT_COUNT} results"
      SKIPPED=$((SKIPPED + 1))
      continue
    fi

    RUN_LABEL="${TYPE}/${AGENT} run ${run_num}/${NUM_RUNS}"
    log "--- ${RUN_LABEL} ---"

    if [ "$DRY_RUN" == "true" ]; then
      log "  DRY RUN: would execute ${SCRIPT} ${AGENT} ${ITERATIONS} ${run_num}"
      continue
    fi

    # Execute
    if [ "$TYPE" == "erosion" ]; then
      if $SCRIPT "$AGENT" "$ITERATIONS" "$run_num" 2>&1 | tee -a "$LOG_FILE"; then
        COMPLETED=$((COMPLETED + 1))
        log "${RUN_LABEL} — COMPLETED"
      else
        FAILED=$((FAILED + 1))
        log "${RUN_LABEL} — FAILED (exit code $?)"
      fi
    elif [ "$TYPE" == "control_a" ]; then
      if $SCRIPT "$AGENT" "$ITERATIONS" "$run_num" 2>&1 | tee -a "$LOG_FILE"; then
        COMPLETED=$((COMPLETED + 1))
        log "${RUN_LABEL} — COMPLETED"
      else
        FAILED=$((FAILED + 1))
        log "${RUN_LABEL} — FAILED (exit code $?)"
      fi
    fi

    log ""
  done
done

# Generate charts
log "--- Generating charts ---"
python experiment/plot_erosion.py \
  --results-dir results/ \
  --agents claude_code aider_local control_a_claude_code \
  --output-dir article/figures 2>&1 | tee -a "$LOG_FILE"

log ""
log "=== Experiment complete ==="
log "Completed: ${COMPLETED} | Skipped: ${SKIPPED} | Failed: ${FAILED} | Total: ${TOTAL_RUNS}"
log "Results:   results/"
log "Charts:    article/figures/"
log "Log:       ${LOG_FILE}"
