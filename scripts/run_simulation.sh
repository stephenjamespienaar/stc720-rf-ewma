#!/usr/bin/env bash
# Run one experiment with resource accounting, logs and provenance.
#
#   scripts/run_simulation.sh {smoke|pilot|production|verify}
#
# Creates results/runs/<mode>_<timestamp>_<pid>/ containing:
#   provenance.txt   host, CPUs, memory, Python, Git commit (read-only), thread limits
#   time.txt         full GNU /usr/bin/time -v report
#   resources.txt    wall clock, CPU time, CPU %, peak RSS, exit status
#   stdout.log / stderr.log, exit_status.txt, pip_freeze.txt, git_status.txt
#   config.json, results.json, tables.md, figures (written by run.py)
#
# Git use is read-only (rev-parse, branch --show-current, status, diff --stat).
# Logs are preserved when the run fails; the script exits with the run's status.
set -uo pipefail

MODE="${1:?usage: scripts/run_simulation.sh MODE (smoke, pilot, production or verify)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
PY="$ROOT/.venv/bin/python"
TIME=/usr/bin/time
[ -x "$TIME" ] || { echo "GNU time not found at $TIME" >&2; exit 1; }

RUN_DIR="results/runs/${MODE}_$(date +%Y%m%dT%H%M%S)_$$"
mkdir -p "$RUN_DIR"

# One controlled level of parallelism: numerical libraries single-threaded;
# the forest uses the n_jobs threads set in run.py.
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0

{
  echo "mode: $MODE"
  echo "run_dir: $RUN_DIR"
  echo "started: $(date -Iseconds)"
  echo "host: $(hostname)"
  echo "kernel: $(uname -srm)"
  echo "cpus_online: $(nproc --all)"
  echo "memory_total_kb: $(awk '/MemTotal/ {print $2}' /proc/meminfo)"
  echo "python: $("$PY" -VV 2>&1)"
  echo "git_commit: $(git rev-parse HEAD 2>/dev/null || echo unavailable)"
  echo "git_branch: $(git branch --show-current 2>/dev/null || echo unavailable)"
  echo "git_worktree_dirty: $([ -n "$(git status --porcelain 2>/dev/null)" ] && echo yes || echo no)"
  echo "threads: OMP=$OMP_NUM_THREADS MKL=$MKL_NUM_THREADS OPENBLAS=$OPENBLAS_NUM_THREADS"
} > "$RUN_DIR/provenance.txt"
git status --porcelain > "$RUN_DIR/git_status.txt" 2>&1
git diff --stat > "$RUN_DIR/git_diff_stat.txt" 2>&1
"$PY" -m pip freeze > "$RUN_DIR/pip_freeze.txt" 2>&1

echo "[run_simulation] $MODE -> $RUN_DIR"
"$TIME" -v -o "$RUN_DIR/time.txt" "$PY" run.py "$MODE" --out "$RUN_DIR" \
  > "$RUN_DIR/stdout.log" 2> "$RUN_DIR/stderr.log"
STATUS=$?

echo "$STATUS" > "$RUN_DIR/exit_status.txt"
echo "finished: $(date -Iseconds)" >> "$RUN_DIR/provenance.txt"
grep -E "Elapsed \(wall clock\)|User time|System time|Percent of CPU|Maximum resident set size|Exit status" \
  "$RUN_DIR/time.txt" > "$RUN_DIR/resources.txt"
cat "$RUN_DIR/resources.txt"

if [ "$STATUS" -ne 0 ]; then
  echo "[run_simulation] FAILED with status $STATUS; logs preserved in $RUN_DIR" >&2
  tail -n 20 "$RUN_DIR/stderr.log" >&2
fi
exit "$STATUS"
