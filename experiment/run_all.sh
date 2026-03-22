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
  PROMPT_SET=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx]['prompt_set'])")
  NUM_RUNS=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx]['runs'])")
  RUN_MODEL=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx].get('model', ''))")
  RUN_PHASE=$(echo "$RUNS_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)[$idx].get('phase', 1))")

  for run_num in $(seq 1 "$NUM_RUNS"); do
    # Determine results directory using standardized paths
    # Phase 2 includes model in path to distinguish runs with different models
    MODEL_SUFFIX=""
    if [ -n "$RUN_MODEL" ]; then
      MODEL_SUFFIX="/${RUN_MODEL}"
    fi

    if [ "$TYPE" == "erosion" ]; then
      SCRIPT="./experiment/run_experiment.sh"
      RESULTS_DIR="results/${AGENT}${MODEL_SUFFIX}/${PROMPT_SET}/run-${run_num}"
    elif [ "$TYPE" == "control_a" ]; then
      SCRIPT="./experiment/run_control_a.sh"
      RESULTS_DIR="results/control_a/${AGENT}${MODEL_SUFFIX}/${PROMPT_SET}/run-${run_num}"
    fi

    # Check if already complete — validate results contain preservation_score key
    RESULT_COUNT=0
    if [ -d "$RESULTS_DIR" ]; then
      RESULT_COUNT=$(find "$RESULTS_DIR" -name "iteration-*.json" -exec python3 -c "import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if 'preservation_score' in d else 1)" {} \; -print 2>/dev/null | wc -l)
    fi

    # Skip if all iterations (0..ITERATIONS) have valid results
    SKIP_THRESHOLD=$(( ITERATIONS + 1 ))
    if [ "$FORCE" == "false" ] && [ "$RESULT_COUNT" -ge "$SKIP_THRESHOLD" ]; then
      log "SKIP: ${TYPE}/${AGENT}/${PROMPT_SET} run ${run_num} — already has ${RESULT_COUNT} results"
      SKIPPED=$((SKIPPED + 1))
      continue
    fi

    RUN_LABEL="${TYPE}/${AGENT}${MODEL_SUFFIX}/${PROMPT_SET} run ${run_num}/${NUM_RUNS}"
    log "--- ${RUN_LABEL} ---"

    if [ "$DRY_RUN" == "true" ]; then
      log "  DRY RUN: would execute MODEL=${RUN_MODEL:-default} ${SCRIPT} ${AGENT} ${PROMPT_SET} ${ITERATIONS} ${run_num}"
      continue
    fi

    # Execute — pass MODEL env var for Phase 2 model override
    RUN_EXIT=0
    MODEL="${RUN_MODEL:-}" "$SCRIPT" "$AGENT" "$PROMPT_SET" "$ITERATIONS" "$run_num" 2>&1 | tee -a "$LOG_FILE"
    RUN_EXIT=${PIPESTATUS[0]}
    if [ "$RUN_EXIT" -eq 0 ]; then
      COMPLETED=$((COMPLETED + 1))
      log "${RUN_LABEL} — COMPLETED"
    else
      FAILED=$((FAILED + 1))
      log "${RUN_LABEL} — FAILED (exit code $RUN_EXIT)"
    fi

    log ""
  done
done

log ""
log "=== Experiment complete ==="
log "Completed: ${COMPLETED} | Skipped: ${SKIPPED} | Failed: ${FAILED} | Total: ${TOTAL_RUNS}"
log "Results:   results/"
log "Log:       ${LOG_FILE}"
