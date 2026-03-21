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
PROMPT_SET_EARLY="${2:-unknown}"
RUN_NUMBER_EARLY="${4:-1}"

# Global debug log for live debugging
DEBUG_LOG="/tmp/semantic-erosion-${AGENT}-${PROMPT_SET_EARLY}-run${RUN_NUMBER_EARLY}-$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$DEBUG_LOG") 2>&1
echo "Debug log: $DEBUG_LOG"
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

# Output directories — include MODEL in path for Phase 2
if [ -n "${MODEL:-}" ]; then
  RESULTS_DIR="${PROJECT_ROOT}/results/control_a/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
  LOG_DIR="${PROJECT_ROOT}/logs/control_a/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
  BRANCH="experiment/control_a/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
else
  RESULTS_DIR="${PROJECT_ROOT}/results/control_a/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
  LOG_DIR="${PROJECT_ROOT}/logs/control_a/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
  BRANCH="experiment/control_a/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
fi

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

echo "=== Semantic Erosion — Control A (with domain context) ==="
echo "Agent:      ${AGENT}"
echo "Prompt Set: ${PROMPT_SET}"
echo "Iterations: ${ITERATIONS}"
echo "Run:        ${RUN_NUMBER}"
echo "Branch:     ${BRANCH}"
echo "============================================================"

cd "$COLLECTING_SOCIETY"

# Lockfile to prevent parallel runs on same repo
LOCKFILE="/tmp/semantic-erosion-collecting-society.lock"
if ! mkdir "$LOCKFILE" 2>/dev/null; then
  echo "ERROR: Another experiment is running (lockfile: $LOCKFILE). Wait or remove it."
  exit 1
fi
trap "rmdir '$LOCKFILE' 2>/dev/null" EXIT

# Load API keys (not exported globally — Claude Code must use Max subscription)
for ENV_FILE in "${COLLECTING_SOCIETY}/.env" ~/.config/gemini.env ~/.config/api_keys.env; do
  if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
  fi
done
export GOOGLE_GENERATIVE_AI_API_KEY="${GEMINI_API_KEY:-}"

# --- Resume support ---
LAST_COMPLETED=0
if [ -d "$RESULTS_DIR" ]; then
  for f in "$RESULTS_DIR"/iteration-*.json; do
    [ -f "$f" ] || continue
    iter_num=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('iteration', -1))" 2>/dev/null)
    status=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('status', 'ok'))" 2>/dev/null)
    if [ "$status" == "compilation_failure" ] || [ "$status" == "skipped_due_to_prior_failure" ]; then
      echo "Run previously terminated at iteration $iter_num (${status}). Cannot resume."
      exit 0
    fi
    has_ps=$(python3 -c "import json; d=json.load(open('$f')); print('yes' if 'preservation_score' in d else 'no')" 2>/dev/null)
    if [ "$has_ps" == "yes" ] && [ "$iter_num" -gt "$LAST_COMPLETED" ] 2>/dev/null; then
      LAST_COMPLETED=$iter_num
    fi
  done
fi

if [ "$LAST_COMPLETED" -gt 0 ]; then
  echo "RESUMING from iteration $((LAST_COMPLETED + 1))"
  if git rev-parse "$BRANCH" >/dev/null 2>&1; then
    if ! git checkout "$BRANCH" 2>/dev/null; then
      echo "WARNING: Could not checkout branch $BRANCH, starting fresh"
      LAST_COMPLETED=0
    fi
  else
    echo "WARNING: Branch $BRANCH not found, starting from baseline"
    LAST_COMPLETED=0
  fi
fi

if [ "$LAST_COMPLETED" -eq 0 ]; then
  if git rev-parse "v0" >/dev/null 2>&1; then
    git checkout -B "$BRANCH" v0 2>/dev/null || true
    rm -rf src/
    git checkout v0 -- src/ pom.xml
    git add -A && git reset HEAD --quiet
  else
    echo "ERROR: Tag 'v0' not found."
    exit 1
  fi
fi

echo ""

# Backup GLOSSARY
GLOSSARY_BACKUP="${PROJECT_ROOT}/.glossary_backup.yaml"
cp "$GLOSSARY" "$GLOSSARY_BACKUP"
GLOSSARY_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')

# Baseline measurement (iteration 0) — skip if resuming
if [ "$LAST_COMPLETED" -eq 0 ]; then
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
fi

# --- Model selection (same as run_experiment.sh) ---
MODEL="${MODEL:-claude-sonnet-4-6}"

# Agent runner (same as run_experiment.sh)
AGENT_TIMEOUT=1200  # 10 minutes max per iteration

BATCH_SUFFIX="Do not ask questions or request clarification. Apply all changes directly to the files."

run_agent() {
  local PROMPT="$1"
  local LOG_FILE="$2"

  if [ "$AGENT" != "claude_code" ]; then
    PROMPT="${PROMPT} ${BATCH_SUFFIX}"
  fi

  if [ "$AGENT" == "claude_code" ]; then
    env -u ANTHROPIC_API_KEY timeout "$AGENT_TIMEOUT" claude --dangerously-skip-permissions -p "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "opencode" ]; then
    local OC_MODEL OC_KEY
    case "$MODEL" in
      claude-sonnet*|anthropic*)  OC_MODEL="anthropic/claude-sonnet-4-6"; OC_KEY="$ANTHROPIC_API_KEY" ;;
      gpt-5.4*|openai*)            OC_MODEL="openai/gpt-5.4"; OC_KEY="$OPENAI_API_KEY" ;;
      qwen*|ollama*)              OC_MODEL="ollama/qwen3-coder-experiment"; OC_KEY="none" ;;
      gemini*)                    OC_MODEL="google/gemini-2.5-flash"; OC_KEY="$GEMINI_API_KEY" ;;
      *)                          OC_MODEL="anthropic/claude-sonnet-4-6"; OC_KEY="$ANTHROPIC_API_KEY" ;;
    esac
    if [[ "$OC_MODEL" == ollama/* ]]; then
      local OLLAMA_MODEL_NAME="${OC_MODEL#ollama/}"
      cat > "${COLLECTING_SOCIETY}/opencode.json" << OCEOF
{
  "model": "$OC_MODEL",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama",
      "options": {"baseURL": "http://localhost:11434/v1"},
      "models": {"$OLLAMA_MODEL_NAME": {"name": "$OLLAMA_MODEL_NAME"}}
    }
  }
}
OCEOF
    else
      cat > "${COLLECTING_SOCIETY}/opencode.json" << OCEOF
{"model": "$OC_MODEL"}
OCEOF
    fi
    ANTHROPIC_API_KEY="$OC_KEY" OPENAI_API_KEY="$OC_KEY" \
    timeout "$AGENT_TIMEOUT" opencode run "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "openhands" ]; then
    local OH_MODEL OH_KEY
    case "$MODEL" in
      claude-sonnet*|anthropic*)  OH_MODEL="anthropic/claude-sonnet-4-6"; OH_KEY="$ANTHROPIC_API_KEY" ;;
      gpt-5.4*|openai*)            OH_MODEL="openai/gpt-5.4"; OH_KEY="$OPENAI_API_KEY" ;;
      qwen*|ollama*)              OH_MODEL="ollama_chat/qwen3-coder-experiment"; OH_KEY="none" ;;
      gemini*)                    OH_MODEL="gemini/gemini-2.5-flash"; OH_KEY="$GEMINI_API_KEY" ;;
      *)                          OH_MODEL="anthropic/claude-sonnet-4-6"; OH_KEY="$ANTHROPIC_API_KEY" ;;
    esac
    LLM_API_KEY="$OH_KEY" \
    LLM_MODEL="$OH_MODEL" \
    local OH_PROMPT="The Java project is in the current working directory ($(pwd)). The source code is in src/main/java/. ${PROMPT}"
    timeout "$AGENT_TIMEOUT" openhands --headless --override-with-envs -t "$OH_PROMPT" \
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

  # Skip already-completed iterations (resume support)
  if [ "$i" -le "$LAST_COMPLETED" ]; then
    echo "--- Iteration ${i}/${ITERATIONS} --- SKIPPING (already completed)"
    continue
  fi

  echo "--- Iteration ${i}/${ITERATIONS} ---"
  echo "Prompt: ${BASE_PROMPT} + [CONTEXT]"
  echo ""

  # Clean agent state to prevent session accumulation
  rm -rf "${COLLECTING_SOCIETY}/.opencode/" 2>/dev/null

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
    echo "No changes in iteration ${i}. Measuring current state."
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
data['changes_applied'] = 0
data['compile_error_count'] = 0
data['compile_autofix'] = 'none'
data['glossary_tampered'] = True if '${GLOSSARY_TAMPERED}' == 'true' else False
with open('${ITERATION_RESULT}', 'w') as f:
    json.dump(data, f, indent=2)
"
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

  git add src/ pom.xml
  git commit -m "iteration-${i}-control_a-${AGENT}-${PROMPT_SET}-run${RUN_NUMBER}" || true

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
