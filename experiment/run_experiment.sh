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
PROMPT_SET_EARLY="${2:-unknown}"
RUN_NUMBER_EARLY="${4:-1}"

# Global debug log for live debugging
MODEL_TAG=""
if [ -n "${MODEL:-}" ]; then MODEL_TAG="${MODEL}-"; fi
DEBUG_LOG="/tmp/semantic-erosion-${AGENT}-${MODEL_TAG}${PROMPT_SET_EARLY}-run${RUN_NUMBER_EARLY}-$(date +%Y%m%d_%H%M%S).log"
echo "Debug log: $DEBUG_LOG"
PROMPT_SET="${2:?Usage: run_experiment.sh <agent> <A|B> [iterations] [run_number]}"
ITERATIONS="${3:-10}"
RUN_NUMBER="${4:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
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

# Output directories — include MODEL in path for Phase 2
# Phase 1 (no MODEL): results/<agent>/<prompt_set>/run-<n>/
# Phase 2 (MODEL set): results/<agent>/<model>/<prompt_set>/run-<n>/
if [ -n "${MODEL:-}" ]; then
  RESULTS_DIR="${PROJECT_ROOT}/results/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
  LOG_DIR="${PROJECT_ROOT}/logs/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
  BRANCH="experiment/${AGENT}/${MODEL}/${PROMPT_SET}/run-${RUN_NUMBER}"
else
  RESULTS_DIR="${PROJECT_ROOT}/results/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
  LOG_DIR="${PROJECT_ROOT}/logs/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
  BRANCH="experiment/${AGENT}/${PROMPT_SET}/run-${RUN_NUMBER}"
fi

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

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

# Lockfile to prevent parallel runs on same repo
LOCKFILE="/tmp/semantic-erosion-collecting-society.lock"
if ! mkdir "$LOCKFILE" 2>/dev/null; then
  echo "ERROR: Another experiment is running (lockfile: $LOCKFILE). Wait or remove it."
  exit 1
fi
trap "rmdir '$LOCKFILE' 2>/dev/null" EXIT

# Load API keys from .env and persistent config
# Keys are loaded into shell vars but NOT exported globally —
# Claude Code must use Max subscription, not the API key.
for ENV_FILE in "${COLLECTING_SOCIETY}/.env" ~/.config/gemini.env ~/.config/api_keys.env; do
  if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
  fi
done
# Only export Gemini (needed by OpenCode config)
export GOOGLE_GENERATIVE_AI_API_KEY="${GEMINI_API_KEY:-}"
# ANTHROPIC_API_KEY and OPENAI_API_KEY are passed explicitly
# to OpenCode/OpenHands inside run_agent(), not exported globally.

# --- Resume support: check for existing results ---
LAST_COMPLETED=0
if [ -d "$RESULTS_DIR" ]; then
  # Read results using a helper to avoid spawning python per-file
  eval "$(python3 -c "
import json, glob, sys, os
results_dir = sys.argv[1]
last = 0
failed_at = -1
for f in sorted(glob.glob(os.path.join(results_dir, 'iteration-*.json')),
                key=lambda x: int(x.rsplit('iteration-')[1].split('.')[0])):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    it = d.get('iteration', -1)
    status = d.get('status', 'ok')
    if status in ('compilation_failure', 'skipped_due_to_prior_failure'):
        if failed_at < 0:
            failed_at = it
        continue
    if 'preservation_score' in d and it > last:
        last = it
print(f'LAST_COMPLETED={last}')
print(f'FAILED_AT={failed_at}')
" "$RESULTS_DIR" 2>/dev/null)"

  if [ "${FAILED_AT:--1}" -ge 0 ]; then
    echo "Previous run had compilation failure at iteration ${FAILED_AT}."
    echo "Cleaning failed iterations and retrying from iteration ${FAILED_AT}..."
    # Remove failed and skipped iteration files so we can retry
    for f in "$RESULTS_DIR"/iteration-*.json; do
      [ -f "$f" ] || continue
      iter_num=$(python3 -c "import json; print(json.load(open('$f')).get('iteration', -1))" 2>/dev/null)
      if [ "$iter_num" -ge "$FAILED_AT" ] 2>/dev/null; then
        rm -f "$f"
      fi
    done
    LAST_COMPLETED=$(( FAILED_AT - 1 ))
    [ "$LAST_COMPLETED" -lt 0 ] && LAST_COMPLETED=0
  fi
fi

if [ "$LAST_COMPLETED" -gt 0 ]; then
  echo "RESUMING from iteration $((LAST_COMPLETED + 1)) (found $LAST_COMPLETED completed iterations)"
  # Try to checkout the branch with previous work
  if git rev-parse "$BRANCH" >/dev/null 2>&1; then
    if ! git checkout "$BRANCH" 2>/dev/null; then
      echo "ERROR: Could not checkout branch $BRANCH. Clean working tree and retry."
      exit 1
    fi
  else
    echo "ERROR: Branch $BRANCH not found but results exist. Clean results dir to restart."
    exit 1
  fi
fi

if [ "$LAST_COMPLETED" -eq 0 ]; then
  # Fresh start from baseline
  if ! git rev-parse "v0" >/dev/null 2>&1; then
    echo "ERROR: Tag 'v0' not found."
    exit 1
  fi
  if ! git checkout -B "$BRANCH" v0; then
    echo "ERROR: Could not checkout baseline. Clean working tree first."
    exit 1
  fi
  git checkout v0 -- src/ pom.xml
  git add src/ pom.xml && git reset HEAD --quiet
  echo ""
  echo "Baseline checked out. Starting iterations..."
else
  echo "Resuming on branch $BRANCH..."
fi
echo ""

# --- Backup GLOSSARY.yaml (immutable ground truth from v0) ---
GLOSSARY_BACKUP="${PROJECT_ROOT}/.glossary_backup.yaml"
# Always restore from v0 tag to prevent using a previously tampered copy
git show v0:collecting-society/GLOSSARY.yaml > "$GLOSSARY_BACKUP" 2>/dev/null || cp "$GLOSSARY" "$GLOSSARY_BACKUP"
cp "$GLOSSARY_BACKUP" "$GLOSSARY"
GLOSSARY_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')

# --- Activate venv once ---
source "$VENV"

# --- Baseline measurement (iteration 0) — skip if resuming ---
if [ "$LAST_COMPLETED" -eq 0 ]; then
  python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
    --glossary "$GLOSSARY" \
    --source "$SOURCE" \
    --agent "$AGENT" \
    --prompt-set "$PROMPT_SET" \
    --iteration 0 \
    --run "$RUN_NUMBER" \
    --output "$RESULTS_DIR/iteration-0.json" \
    --no-distance
fi

# --- Model selection ---
# Default: Claude Sonnet (Phase 1 — same model across all agents)
# Override with MODEL env var for Phase 2 (vary model, fixed agent)
MODEL="${MODEL:-claude-sonnet-4-6}"

# --- Write agent config before iterations ---
# OpenCode needs opencode.json in project dir; write it once after checkout
if [ "$AGENT" == "opencode" ]; then
  OC_MODEL_INIT=""
  case "$MODEL" in
    claude-sonnet*|anthropic*)  OC_MODEL_INIT="anthropic/claude-sonnet-4-6" ;;
    gpt-5.4*|openai*)          OC_MODEL_INIT="openai/gpt-5.4" ;;
    qwen*|ollama*)             OC_MODEL_INIT="ollama/qwen3-coder-experiment" ;;
    gemini*)                   OC_MODEL_INIT="google/gemini-2.5-flash" ;;
    *)                         OC_MODEL_INIT="anthropic/claude-sonnet-4-6" ;;
  esac
  if [[ "$OC_MODEL_INIT" == ollama/* ]]; then
    OLLAMA_MODEL_INIT="${OC_MODEL_INIT#ollama/}"
    cat > "${COLLECTING_SOCIETY}/opencode.json" << OCINIT
{
  "\$schema": "https://opencode.ai/config.json",
  "model": "$OC_MODEL_INIT",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama",
      "options": {"baseURL": "http://localhost:11434/v1", "timeout": 600000},
      "models": {"$OLLAMA_MODEL_INIT": {"name": "$OLLAMA_MODEL_INIT"}}
    }
  }
}
OCINIT
  else
    cat > "${COLLECTING_SOCIETY}/opencode.json" << OCINIT
{"\$schema": "https://opencode.ai/config.json", "model": "$OC_MODEL_INIT"}
OCINIT
  fi
fi

# --- Agent runner function ---
AGENT_TIMEOUT=1200  # 20 minutes max per iteration

BATCH_SUFFIX="Do not ask questions or request clarification. Apply all changes directly to the files."

run_agent() {
  local PROMPT="$1"
  local LOG_FILE="$2"

  # For non-interactive agents, append instruction to not ask questions
  if [ "$AGENT" != "claude_code" ]; then
    PROMPT="${PROMPT} ${BATCH_SUFFIX}"
  fi

  if [ "$AGENT" == "claude_code" ]; then
    # Claude Code uses Max subscription — ensure API key is NOT in env
    env -u ANTHROPIC_API_KEY timeout "$AGENT_TIMEOUT" claude --dangerously-skip-permissions -p "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "opencode" ]; then
    # Fix: reset global config to prevent "Unrecognized key" errors
    echo '{"$schema": "https://opencode.ai/config.json"}' > ~/.config/opencode/opencode.json 2>/dev/null || true
    # OpenCode: pass API key and model explicitly
    local OC_MODEL OC_KEY
    case "$MODEL" in
      claude-sonnet*|anthropic*)  OC_MODEL="anthropic/claude-sonnet-4-6"; OC_KEY="$ANTHROPIC_API_KEY" ;;
      gpt-5.4*|openai*)            OC_MODEL="openai/gpt-5.4"; OC_KEY="$OPENAI_API_KEY" ;;
      qwen*|ollama*)              OC_MODEL="ollama/qwen3-coder-experiment"; OC_KEY="none" ;;
      gemini*)                    OC_MODEL="google/gemini-2.5-flash"; OC_KEY="$GEMINI_API_KEY" ;;
      *)                          OC_MODEL="anthropic/claude-sonnet-4-6"; OC_KEY="$ANTHROPIC_API_KEY" ;;
    esac
    # Write project-level opencode.json to override global config
    if [[ "$OC_MODEL" == ollama/* ]]; then
      local OLLAMA_MODEL_NAME="${OC_MODEL#ollama/}"
      cat > "${COLLECTING_SOCIETY}/opencode.json" << OCEOF
{
  "\$schema": "https://opencode.ai/config.json",
  "model": "$OC_MODEL",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama",
      "options": {"baseURL": "http://localhost:11434/v1", "timeout": 600000},
      "models": {"$OLLAMA_MODEL_NAME": {"name": "$OLLAMA_MODEL_NAME"}}
    }
  }
}
OCEOF
    else
      cat > "${COLLECTING_SOCIETY}/opencode.json" << OCEOF
{"\$schema": "https://opencode.ai/config.json", "model": "$OC_MODEL"}
OCEOF
    fi
    ANTHROPIC_API_KEY="$OC_KEY" OPENAI_API_KEY="$OC_KEY" \
    timeout "$AGENT_TIMEOUT" opencode run "$PROMPT" \
      2>&1 | tee "$LOG_FILE" || return $?

  elif [ "$AGENT" == "openhands" ]; then
    # OpenHands: pass API key and model via env
    local OH_MODEL OH_KEY
    case "$MODEL" in
      claude-sonnet*|anthropic*)  OH_MODEL="anthropic/claude-sonnet-4-6"; OH_KEY="$ANTHROPIC_API_KEY" ;;
      gpt-5.4*|openai*)            OH_MODEL="openai/gpt-5.4"; OH_KEY="$OPENAI_API_KEY" ;;
      qwen*|ollama*)              OH_MODEL="ollama_chat/qwen3-coder-experiment"; OH_KEY="none" ;;
      gemini*)                    OH_MODEL="gemini/gemini-2.5-flash"; OH_KEY="$GEMINI_API_KEY" ;;
      *)                          OH_MODEL="anthropic/claude-sonnet-4-6"; OH_KEY="$ANTHROPIC_API_KEY" ;;
    esac
    # OpenHands needs explicit directory context — it doesn't explore the filesystem by default
    local OH_PROMPT="The Java project is in the current working directory ($(pwd)). The source code is in src/main/java/. ${PROMPT}"
    LLM_API_KEY="$OH_KEY" \
    LLM_MODEL="$OH_MODEL" \
    timeout "$AGENT_TIMEOUT" openhands --headless --override-with-envs -t "$OH_PROMPT" \
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

  # Skip already-completed iterations (resume support)
  if [ "$i" -le "$LAST_COMPLETED" ]; then
    echo "--- Iteration ${i}/${ITERATIONS} --- SKIPPING (already completed)"
    continue
  fi

  echo "--- Iteration ${i}/${ITERATIONS} ---"
  echo "Prompt: ${PROMPT}"
  echo ""

  # --- Clean agent state to prevent session accumulation ---
  rm -rf "${COLLECTING_SOCIETY}/.opencode/" 2>/dev/null

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
    echo "No changes in iteration ${i}. Measuring current state."
    # Agent ran but decided no changes needed — still measure PS/ES
    python "${PROJECT_ROOT}/experiment/measure_fidelity.py" \
      --glossary "$GLOSSARY" \
      --source "$SOURCE" \
      --agent "$AGENT" \
      --prompt-set "$PROMPT_SET" \
      --iteration "$i" \
      --run "$RUN_NUMBER" \
      --output "$ITERATION_RESULT"
    python3 -c "
import json, sys
result_file, tampered = sys.argv[1], sys.argv[2] == 'true'
with open(result_file) as f:
    data = json.load(f)
data['changes_applied'] = 0
data['compile_error_count'] = 0
data['compile_autofix'] = 'none'
data['glossary_tampered'] = tampered
with open(result_file, 'w') as f:
    json.dump(data, f, indent=2)
" "$ITERATION_RESULT" "$GLOSSARY_TAMPERED"
    echo ""
    continue
  fi

  # --- Compilation gate (3 attempts) ---
  COMPILE_OK=false
  COMPILE_ERROR_COUNT=0
  COMPILE_AUTOFIX="none"
  MAX_FIX_ATTEMPTS=3
  FIX_ATTEMPT=0

  COMPILE_OUTPUT=$(mvn compile 2>&1) || true
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

      COMPILE_OUTPUT=$(mvn compile 2>&1) || true
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
  git add src/ pom.xml
  git commit -m "iteration-${i}-${AGENT}-${PROMPT_SET}-run${RUN_NUMBER}" || true

  # --- Analyze changes made by the agent ---
  CHANGE_ANALYSIS="${LOG_DIR}/changes-iteration-${i}.json"
  python3 -c "
import subprocess, json

# Check if HEAD~1 exists (first iteration may not have a parent)
has_parent = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD~1'], capture_output=True).returncode == 0
if not has_parent:
    # First iteration: diff against v0 tag instead
    diff_ref = 'v0'
else:
    diff_ref = 'HEAD~1'

diff_stat = subprocess.run(['git', 'diff', '--stat', diff_ref, 'HEAD'], capture_output=True, text=True).stdout.strip()
name_status = subprocess.run(['git', 'diff', '--name-status', diff_ref, 'HEAD'], capture_output=True, text=True).stdout.strip()
diff_numstat = subprocess.run(['git', 'diff', '--numstat', diff_ref, 'HEAD'], capture_output=True, text=True).stdout.strip()

files_added = []
files_deleted = []
files_modified = []
files_renamed = []
insertions = 0
deletions = 0

for line in name_status.split('\n'):
    if not line.strip(): continue
    parts = line.split('\t')
    status = parts[0]
    if status.startswith('A'): files_added.append(parts[1])
    elif status.startswith('D'): files_deleted.append(parts[1])
    elif status.startswith('M'): files_modified.append(parts[1])
    elif status.startswith('R'): files_renamed.append({'from': parts[1], 'to': parts[2]})

for line in diff_numstat.split('\n'):
    if not line.strip(): continue
    parts = line.split('\t')
    try:
        insertions += int(parts[0])
        deletions += int(parts[1])
    except ValueError:
        pass

analysis = {
    'iteration': $i,
    'files_added': files_added,
    'files_deleted': files_deleted,
    'files_modified': files_modified,
    'files_renamed': files_renamed,
    'total_files_changed': len(files_added) + len(files_deleted) + len(files_modified) + len(files_renamed),
    'insertions': insertions,
    'deletions': deletions,
}

with open('$CHANGE_ANALYSIS', 'w') as f:
    json.dump(analysis, f, indent=2)

print(f'  Changes: +{insertions}/-{deletions} in {analysis[\"total_files_changed\"]} files | Added: {len(files_added)} Deleted: {len(files_deleted)} Renamed: {len(files_renamed)}')
" 2>/dev/null || echo "  (change analysis skipped)"

  # --- Verify GLOSSARY before measurement ---
  CURRENT_HASH=$(sha256sum "$GLOSSARY" | awk '{print $1}')
  if [ "$CURRENT_HASH" != "$GLOSSARY_HASH" ]; then
    echo "ERROR: GLOSSARY.yaml checksum mismatch before measurement!"
    cp "$GLOSSARY_BACKUP" "$GLOSSARY"
  fi

  # --- Measure ---
  echo "Measuring..."
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
import json, sys, os
result_file = sys.argv[1]
compile_errors = int(sys.argv[2])
compile_autofix = sys.argv[3]
tampered = sys.argv[4] == 'true'
change_file = sys.argv[5]
with open(result_file) as f:
    data = json.load(f)
data['compile_error_count'] = compile_errors
data['compile_autofix'] = compile_autofix
data['glossary_tampered'] = tampered
data['changes_applied'] = 1
if os.path.exists(change_file):
    with open(change_file) as cf:
        data['change_analysis'] = json.load(cf)
with open(result_file, 'w') as f:
    json.dump(data, f, indent=2)
" "$ITERATION_RESULT" "$COMPILE_ERROR_COUNT" "$COMPILE_AUTOFIX" "$GLOSSARY_TAMPERED" "$CHANGE_ANALYSIS"

  echo ""
done

echo "=== Experiment complete ==="
echo "Results in: ${RESULTS_DIR}"
echo "Logs in:    ${LOG_DIR}"
