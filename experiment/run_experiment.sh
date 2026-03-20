#!/bin/bash
# run_experiment.sh — Run the semantic erosion experiment for one agent.
#
# Usage:
#   ./experiment/run_experiment.sh <agent> <prompt_set> [iterations] [run_number]
#
# Agents: claude_code, opencode, openhands
# Prompt sets: A (neutral), B (stress)
#
# Examples:
#   ./experiment/run_experiment.sh claude_code A          # Set A, 10 iterations, run 1
#   ./experiment/run_experiment.sh opencode B 10 2        # Set B, run 2
#   ./experiment/run_experiment.sh openhands A 10 3       # Set A, run 3

set -euo pipefail

AGENT="${1:?Usage: run_experiment.sh <claude_code|opencode|openhands> <A|B> [iterations] [run_number]}"
PROMPT_SET="${2:?Usage: run_experiment.sh <agent> <A|B> [iterations] [run_number]}"
ITERATIONS="${3:-10}"
RUN_NUMBER="${4:-1}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COLLECTING_SOCIETY="${PROJECT_ROOT}/collecting-society"
GLOSSARY="${COLLECTING_SOCIETY}/GLOSSARY.yaml"
SOURCE="${COLLECTING_SOCIETY}/src"
VENV="${PROJECT_ROOT}/.venv/bin/activate"
export PYTHONPATH="${PROJECT_ROOT}/experiment:${PYTHONPATH:-}"

# Load prompts from file
if [ "$PROMPT_SET" == "A" ]; then
  PROMPT_FILE="${PROJECT_ROOT}/experiment/prompts_neutral.txt"
elif [ "$PROMPT_SET" == "B" ]; then
  PROMPT_FILE="${PROJECT_ROOT}/experiment/prompts_stress.txt"
else
  echo "ERROR: Unknown prompt set '${PROMPT_SET}'. Use: A, B"
  exit 1
fi
mapfile -t PROMPTS < "$PROMPT_FILE"

# Output directories — standardized path: results/<agent>/<prompt_set>/run-<n>/
RESULTS_DIR="${PROJECT_ROOT}/results/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
LOG_DIR="${PROJECT_ROOT}/logs/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

# Branch name
BRANCH="experiment/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"

echo "=== Semantic Erosion Experiment ==="
echo "Agent:      ${AGENT}"
echo "Prompt Set: ${PROMPT_SET}"
echo "Iterations: ${ITERATIONS}"
echo "Run:        ${RUN_NUMBER}"
echo "Branch:     ${BRANCH}"
echo "Results:    ${RESULTS_DIR}"
echo "==================================="

# --- Setup ---
cd "$COLLECTING_SOCIETY"

# Load API keys
if [ -f ~/.config/gemini.env ]; then
  set -a; source ~/.config/gemini.env; set +a
  export GEMINI_API_KEY
  export GOOGLE_GENERATIVE_AI_API_KEY="${GEMINI_API_KEY}"
  cp -f ~/.config/gemini.env "${COLLECTING_SOCIETY}/.env" 2>/dev/null || true
fi

# Reset source code to baseline
if git rev-parse "v0" >/dev/null 2>&1; then
  git checkout -B "$BRANCH" 2>/dev/null || true
  rm -rf src/
  git checkout v0 -- src/ pom.xml
  git add -A && git reset HEAD --quiet
else
  echo "ERROR: Tag 'v0' not found."
  exit 1
fi

echo ""
echo "Baseline checked out. Starting iterations..."
echo ""

# --- Backup GLOSSARY.yaml (immutable ground truth) ---
GLOSSARY_BACKUP="${PROJECT_ROOT}/.glossary_backup.yaml"
cp "$GLOSSARY" "$GLOSSARY_BACKUP"
GLOSSARY_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')

# --- Baseline measurement (iteration 0) ---
source "$VENV"
python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
  --glossary "$GLOSSARY" \
  --source "$SOURCE" \
  --agent "$AGENT" \
  --prompt-set "$PROMPT_SET" \
  --iteration 0 \
  --run "$RUN_NUMBER" \
  --output "$RESULTS_DIR/iteration-0.json" \
  --no-distance

# --- Agent runner function ---
run_agent() {
  local PROMPT="$1"
  local LOG_FILE="$2"

  if [ "$AGENT" == "claude_code" ]; then
    claude --dangerously-skip-permissions -p "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "opencode" ]; then
    opencode run "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "openhands" ]; then
    LLM_API_KEY="${GEMINI_API_KEY:-}" \
    LLM_MODEL="gemini/gemini-2.5-flash" \
    openhands --headless --override-with-envs -t "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  else
    echo "ERROR: Unknown agent '${AGENT}'. Use: claude_code, opencode, openhands"
    return 1
  fi
}

# --- Iteration loop ---
for i in $(seq 1 "$ITERATIONS"); do
  PROMPT="${PROMPTS[$(( (i - 1) % ${#PROMPTS[@]} ))]}"
  ITERATION_LOG="${LOG_DIR}/iteration-${i}.txt"
  ITERATION_RESULT="${RESULTS_DIR}/iteration-${i}.json"

  echo "--- Iteration ${i}/${ITERATIONS} ---"
  echo "Prompt: ${PROMPT}"
  echo ""

  # --- Run agent ---
  AGENT_EXIT=0
  run_agent "$PROMPT" "$ITERATION_LOG" || AGENT_EXIT=$?

  if [ "$AGENT_EXIT" -ne 0 ]; then
    echo "WARNING: Agent exited with code ${AGENT_EXIT}."
  fi

  # --- Detect and restore GLOSSARY tampering ---
  GLOSSARY_TAMPERED=false
  CURRENT_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')
  if [ "$CURRENT_HASH" != "$GLOSSARY_HASH" ]; then
    GLOSSARY_TAMPERED=true
    echo "WARNING: Agent modified GLOSSARY.yaml in iteration ${i}!"
    cp "$GLOSSARY" "${LOG_DIR}/glossary-tampered-iteration-${i}.yaml"
    cp "$GLOSSARY_BACKUP" "$GLOSSARY"
    echo "GLOSSARY.yaml restored from backup."
  fi

  # --- Check if anything changed ---
  if git diff --quiet && git diff --cached --quiet; then
    echo "No changes in iteration ${i}. Skipping."
    echo '{"status": "no_changes", "iteration": '"${i}"'}' > "${RESULTS_DIR}/iteration-${i}-skipped.json"
    echo ""
    continue
  fi

  # --- Compilation gate (3 attempts) ---
  COMPILE_OK=false
  COMPILE_ERROR_COUNT=0
  COMPILE_AUTOFIX="none"
  MAX_FIX_ATTEMPTS=3
  FIX_ATTEMPT=0

  COMPILE_OUTPUT=$(mvn compile 2>&1)
  if echo "$COMPILE_OUTPUT" | grep -q "BUILD SUCCESS"; then
    COMPILE_OK=true
  else
    COMPILE_ERROR_COUNT=$(echo "$COMPILE_OUTPUT" | grep -c "^\[ERROR\]" || true)
    echo "$COMPILE_OUTPUT" > "${LOG_DIR}/compile-errors-iteration-${i}.txt"

    while [ "$FIX_ATTEMPT" -lt "$MAX_FIX_ATTEMPTS" ] && [ "$COMPILE_OK" == "false" ]; do
      FIX_ATTEMPT=$((FIX_ATTEMPT + 1))
      echo "Compilation failed (${COMPILE_ERROR_COUNT} errors). Fix attempt ${FIX_ATTEMPT}/${MAX_FIX_ATTEMPTS}..."

      FIX_PROMPT="The previous refactoring broke compilation. Fix these errors without reverting the renames: $(echo "$COMPILE_OUTPUT" | tail -30)"
      run_agent "$FIX_PROMPT" "${LOG_DIR}/fix-attempt-${i}-${FIX_ATTEMPT}.txt" || true

      COMPILE_OUTPUT=$(mvn compile 2>&1)
      if echo "$COMPILE_OUTPUT" | grep -q "BUILD SUCCESS"; then
        COMPILE_OK=true
        COMPILE_AUTOFIX="succeeded_attempt_${FIX_ATTEMPT}"
        echo "Auto-fix succeeded on attempt ${FIX_ATTEMPT}."
      else
        COMPILE_ERROR_COUNT=$(echo "$COMPILE_OUTPUT" | grep -c "^\[ERROR\]" || true)
        echo "$COMPILE_OUTPUT" >> "${LOG_DIR}/compile-errors-iteration-${i}.txt"
      fi
    done

    if [ "$COMPILE_OK" == "false" ]; then
      COMPILE_AUTOFIX="failed_after_${MAX_FIX_ATTEMPTS}_attempts"
      echo "All fix attempts failed. Run terminated at iteration ${i}."

      cat > "${RESULTS_DIR}/iteration-${i}.json" << FEOF
{
  "agent": "${AGENT}",
  "prompt_set": "${PROMPT_SET}",
  "iteration": ${i},
  "run": ${RUN_NUMBER},
  "status": "compilation_failure",
  "compile_error_count": ${COMPILE_ERROR_COUNT},
  "compile_autofix": "${COMPILE_AUTOFIX}",
  "fix_attempts": ${FIX_ATTEMPT},
  "glossary_tampered": ${GLOSSARY_TAMPERED}
}
FEOF

      for j in $(seq $((i + 1)) "$ITERATIONS"); do
        echo "{\"status\": \"skipped_due_to_prior_failure\", \"iteration\": ${j}}" \
          > "${RESULTS_DIR}/iteration-${j}.json"
      done

      git checkout . && git clean -fd src/
      break
    fi
  fi

  # --- Commit ---
  git add -A
  git commit -m "iteration-${i}-${AGENT}-${PROMPT_SET}-run${RUN_NUMBER}" || true

  # --- Verify GLOSSARY before measurement ---
  CURRENT_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')
  if [ "$CURRENT_HASH" != "$GLOSSARY_HASH" ]; then
    echo "ERROR: GLOSSARY.yaml checksum mismatch before measurement!"
    cp "$GLOSSARY_BACKUP" "$GLOSSARY"
  fi

  # --- Measure ---
  echo "Measuring..."
  source "$VENV"
  python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
    --glossary "$GLOSSARY" \
    --source "$SOURCE" \
    --agent "$AGENT" \
    --prompt-set "$PROMPT_SET" \
    --iteration "$i" \
    --run "$RUN_NUMBER" \
    --output "$ITERATION_RESULT"

  # Inject metadata
  python3 -c "
import json
with open('${ITERATION_RESULT}') as f:
    data = json.load(f)
data['compile_error_count'] = ${COMPILE_ERROR_COUNT}
data['compile_autofix'] = '${COMPILE_AUTOFIX}'
data['glossary_tampered'] = True if '${GLOSSARY_TAMPERED}' == 'true' else False
with open('${ITERATION_RESULT}', 'w') as f:
    json.dump(data, f, indent=2)
"

  echo ""
done

echo "=== Experiment complete ==="
echo "Results in: ${RESULTS_DIR}"
echo "Logs in:    ${LOG_DIR}"
