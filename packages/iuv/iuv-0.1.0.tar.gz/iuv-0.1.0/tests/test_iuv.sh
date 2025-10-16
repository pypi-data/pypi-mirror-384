#!/usr/bin/env bash
set -euo pipefail

# Integration test for iuv run ...
# All temporary artifacts (script, log, trigger file) live in a mktemp dir under /tmp.

# Install via install.sh (ensures uv + iuv tool)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
(
  cd "$REPO_ROOT"
  bash ./install.sh
)
export PATH="$HOME/.local/bin:$PATH"

# Work entirely in isolated temp dir so repo stays clean
WORKDIR="$(mktemp -d)"
cd "$WORKDIR"

TARGET=watch_target.py
LOG=test_output.log

cat > "$TARGET" <<'PY'
print('HELLO')
PY

# Start watcher (background) using installed tool
iuv run "$TARGET" > "$LOG" 2>&1 &
PID=$!

echo "Started iuv watcher PID=$PID (workdir=$WORKDIR)"
trap 'echo "Cleaning up"; pkill -f "iuv run $TARGET" || true; rm -rf "$WORKDIR" || true' EXIT

# Wait for first occurrence
TIMEOUT=20
start=$(date +%s)
while true; do
  if grep -q HELLO "$LOG"; then
    echo "Initial run detected"
    break
  fi
  now=$(date +%s)
  if (( now - start > TIMEOUT )); then
    echo "FAIL: did not see initial HELLO within $TIMEOUT s" >&2
    exit 1
  fi
  sleep 0.5
done

# Trigger a change
sleep 1
echo '# change' > trigger_file.py

echo "Waiting for rerun after change..."
start=$(date +%s)
while true; do
  count=$(grep -c HELLO "$LOG" || true)
  if (( count >= 2 )); then
    echo "Rerun detected (HELLO count=$count)"
    break
  fi
  now=$(date +%s)
  if (( now - start > TIMEOUT )); then
    echo "FAIL: no rerun detected within $TIMEOUT s" >&2
    echo "--- LOG ---"; cat "$LOG"; echo "-----------"
    exit 1
  fi
  sleep 0.5
done

pkill -f "iuv run $TARGET" || true

# Test Enter-to-rerun
( # Wrap in subshell to avoid messing with parent shell job control
  if [ -t 1 ]; then stty -echoctl; fi # hide ^C in output
  FIFO_FILE="$WORKDIR/iuv_fifo"
  mkfifo "$FIFO_FILE"

  # iuv's stdin is the pipe
  iuv run "$TARGET" < "$FIFO_FILE" > "$LOG" 2>&1 &
  PID=$!
  echo "Started iuv watcher for rerun test PID=$PID"

  # This keeps the pipe open for writing
  exec 3>"$FIFO_FILE"

  sleep 2 # Wait for initial run
  count1=$(grep -c HELLO "$LOG" || true)
  echo "Count before Enter: $count1"

  kill -s INT $PID
  sleep 1
  # Simulate pressing enter by sending a newline to the pipe
  echo "simulating enter" >&3

  echo "Waiting for rerun after Enter..."
  start=$(date +%s)
  while true; do
    count2=$(grep -c HELLO "$LOG" || true)
    if (( count2 > count1 )); then
      echo "Rerun after Enter detected (count=$count2)"
      break
    fi
    now=$(date +%s)
    if (( now - start > TIMEOUT )); then
      echo "FAIL: no rerun detected after Enter within $TIMEOUT s" >&2
      echo "--- LOG --- "; cat "$LOG"; echo "-----------"
      exit 1
    fi
    sleep 0.5
  done
  if [ -t 1 ]; then stty echoctl; fi
  exec 3>&- # close the pipe
  rm "$FIFO_FILE"
)

echo "--- FINAL LOG ---"
cat "$LOG" || true
echo "-------------------"
echo "Test passed"
