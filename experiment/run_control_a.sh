#!/bin/bash
# run_control_a.sh — Run Control A: same prompts WITH domain context.
#
# Usage:
#   ./experiment/run_control_a.sh <agent> <prompt_set> [iterations] [run_number]
#
# Identical to run_experiment.sh except each prompt is prefixed with
# the standardized domain context from context_prompt.txt.

set -euo pipefail

AGENT="${1:?Usage: run_control_a.sh <agent> <A|B> [iterations] [run_number]}"
PROMPT_SET="${2:?Usage: run_control_a.sh <agent> <A|B> [iterations] [run_number]}"
ITERATIONS="${3:-10}"
RUN_NUMBER="${4:-1}"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COLLECTING_SOCIETY="${PROJECT_ROOT}/collecting-society"
GLOSSARY="${COLLECTING_SOCIETY}/GLOSSARY.yaml"
SOURCE="${COLLECTING_SOCIETY}/src"
VENV="${PROJECT_ROOT}/.venv/bin/activate"
export PYTHONPATH="${PROJECT_ROOT}/experiment:${PYTHONPATH:-}"

# Load context and prompts
CONTEXT=$(cat "${PROJECT_ROOT}/experiment/context_prompt.txt")

if [ "$PROMPT_SET" == "A" ]; then
  PROMPT_FILE="${PROJECT_ROOT}/experiment/prompts_neutral.txt"
elif [ "$PROMPT_SET" == "B" ]; then
  PROMPT_FILE="${PROJECT_ROOT}/experiment/prompts_stress.txt"
else
  echo "ERROR: Unknown prompt set '${PROMPT_SET}'."
  exit 1
fi
mapfile -t BASE_PROMPTS < "$PROMPT_FILE"

# Output directories
AGENT_LABEL="control_a_${AGENT}_${PROMPT_SET}"
if [ "$RUN_NUMBER" -gt 1 ]; then
  RESULTS_DIR="${PROJECT_ROOT}/results/${AGENT_LABEL}/run-${RUN_NUMBER}"
else
  RESULTS_DIR="${PROJECT_ROOT}/results/${AGENT_LABEL}"
fi
LOG_DIR="${PROJECT_ROOT}/logs/${AGENT_LABEL}"
if [ "$RUN_NUMBER" -gt 1 ]; then
  LOG_DIR="${LOG_DIR}/run-${RUN_NUMBER}"
fi

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

BRANCH="experiment/${AGENT_LABEL}"
if [ "$RUN_NUMBER" -gt 1 ]; then
  BRANCH="${BRANCH}/run-${RUN_NUMBER}"
fi

echo "=== Semantic Erosion — Control A (with domain context) ==="
echo "Agent:      ${AGENT}"
echo "Prompt Set: ${PROMPT_SET}"
echo "Iterations: ${ITERATIONS}"
echo "Run:        ${RUN_NUMBER}"
echo "Branch:     ${BRANCH}"
echo "============================================================"

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

# Backup GLOSSARY
GLOSSARY_BACKUP="${PROJECT_ROOT}/.glossary_backup.yaml"
cp "$GLOSSARY" "$GLOSSARY_BACKUP"
GLOSSARY_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')

# Baseline measurement (iteration 0)
source "$VENV"
python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
  --glossary "$GLOSSARY" \
  --source "$SOURCE" \
  --agent "control_a_${AGENT}" \
  --prompt-set "$PROMPT_SET" \
  --iteration 0 \
  --run "$RUN_NUMBER" \
  --output "$RESULTS_DIR/iteration-0.json" \
  --no-distance

# Agent runner (same as run_experiment.sh)
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
    echo "ERROR: Unknown agent '${AGENT}'."
    return 1
  fi
}

for i in $(seq 1 "$ITERATIONS"); do
  BASE_PROMPT="${BASE_PROMPTS[$(( (i - 1) % ${#BASE_PROMPTS[@]} ))]}"
  PROMPT="${BASE_PROMPT}

${CONTEXT}"
  ITERATION_LOG="${LOG_DIR}/iteration-${i}.txt"
  ITERATION_RESULT="${RESULTS_DIR}/iteration-${i}.json"

  echo "--- Iteration ${i}/${ITERATIONS} ---"
  echo "Prompt: ${BASE_PROMPT} + [CONTEXT]"
  echo ""

  AGENT_EXIT=0
  run_agent "$PROMPT" "$ITERATION_LOG" || AGENT_EXIT=$?

  # Glossary tampering check
  GLOSSARY_TAMPERED=false
  CURRENT_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')
  if [ "$CURRENT_HASH" != "$GLOSSARY_HASH" ]; then
    GLOSSARY_TAMPERED=true
    cp "$GLOSSARY" "${LOG_DIR}/glossary-tampered-iteration-${i}.yaml"
    cp "$GLOSSARY_BACKUP" "$GLOSSARY"
    echo "WARNING: GLOSSARY.yaml tampered and restored."
  fi

  if git diff --quiet && git diff --cached --quiet; then
    echo "No changes in iteration ${i}. Skipping."
    echo '{"status": "no_changes", "iteration": '"${i}"'}' > "${RESULTS_DIR}/iteration-${i}-skipped.json"
    echo ""
    continue
  fi

  # Compilation gate (3 attempts)
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
      echo "Compilation failed. Fix attempt ${FIX_ATTEMPT}/${MAX_FIX_ATTEMPTS}..."

      FIX_PROMPT="The previous refactoring broke compilation. Fix these errors without reverting the renames: $(echo "$COMPILE_OUTPUT" | tail -30)"
      run_agent "$FIX_PROMPT" "${LOG_DIR}/fix-attempt-${i}-${FIX_ATTEMPT}.txt" || true

      COMPILE_OUTPUT=$(mvn compile 2>&1)
      if echo "$COMPILE_OUTPUT" | grep -q "BUILD SUCCESS"; then
        COMPILE_OK=true
        COMPILE_AUTOFIX="succeeded_attempt_${FIX_ATTEMPT}"
      else
        COMPILE_ERROR_COUNT=$(echo "$COMPILE_OUTPUT" | grep -c "^\[ERROR\]" || true)
      fi
    done

    if [ "$COMPILE_OK" == "false" ]; then
      COMPILE_AUTOFIX="failed_after_${MAX_FIX_ATTEMPTS}_attempts"
      cat > "${RESULTS_DIR}/iteration-${i}.json" << FEOF
{
  "agent": "control_a_${AGENT}",
  "prompt_set": "${PROMPT_SET}",
  "iteration": ${i},
  "run": ${RUN_NUMBER},
  "status": "compilation_failure",
  "compile_error_count": ${COMPILE_ERROR_COUNT},
  "compile_autofix": "${COMPILE_AUTOFIX}",
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

  git add -A
  git commit -m "iteration-${i}-control_a-${AGENT}-${PROMPT_SET}" || true

  # Verify GLOSSARY
  CURRENT_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')
  if [ "$CURRENT_HASH" != "$GLOSSARY_HASH" ]; then
    cp "$GLOSSARY_BACKUP" "$GLOSSARY"
  fi

  # Measure
  source "$VENV"
  python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
    --glossary "$GLOSSARY" \
    --source "$SOURCE" \
    --agent "control_a_${AGENT}" \
    --prompt-set "$PROMPT_SET" \
    --iteration "$i" \
    --run "$RUN_NUMBER" \
    --output "$ITERATION_RESULT"

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

echo "=== Control A complete ==="
echo "Results in: ${RESULTS_DIR}"
