#!/usr/bin/env bash
set -euo pipefail

# --- Config ---
JOB="data/job-smoke-001"
OUTDIR="out/job-smoke-001"
LOG="logs/run_smoke.log"

mkdir -p "$JOB/photos" "$OUTDIR" logs

# Optional: copy sample inputs if you have them in these locations
copy_if() { [ -f "$1" ] && cp -f "$1" "$2"; }
for SRC in "data/job-0001" "samples" "."; do
  copy_if "$SRC/floorplan.jpg" "$JOB/floorplan.jpg"
  copy_if "$SRC/floorplan.jpeg" "$JOB/floorplan.jpg"
  copy_if "$SRC/floorplan.xml" "$JOB/floorplan.xml"
  copy_if "$SRC/policy.pdf"    "$JOB/policy.pdf"
  copy_if "$SRC/photo1.jpg"    "$JOB/photos/photo1.jpg"
done

echo "[1/5] Starting Flask interface on :5002"
python3 tools/claim_interface.py >/dev/null 2>&1 &
SERVER_PID=$!
cleanup() {
  if ps -p "$SERVER_PID" >/dev/null 2>&1; then
    echo "[*] Stopping Flask (PID $SERVER_PID)"
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Wait for server
echo "[2/5] Waiting for server..."
for i in {1..30}; do
  if curl -sS http://127.0.0.1:5002/ >/dev/null; then
    echo "[2/5] Flask is up."
    break
  fi
  sleep 0.5
done

# Route check (ok if missing)
echo "[3/5] Route check:"
if ! curl -sS http://127.0.0.1:5002/routes; then
  echo "(no /routes endpoint, continuing)"
fi

# Run pipeline
echo
echo "[4/5] Running pipeline on $JOB (logging to $LOG)"
set +e
python3 run_pipeline.py --job "$JOB" 2>&1 | tee "$LOG"
PIPE_STATUS=${PIPESTATUS[0]}
set -e

# Gather outputs
for f in out/estimate_xact*.csv out/*--job*_room_data*.csv; do
  [ -f "$f" ] && mv -f "$f" "$OUTDIR/$(basename "$f")"
done

echo
echo "[5/5] Outputs in $OUTDIR (if any):"
ls -l "$OUTDIR" || true

if [ "$PIPE_STATUS" -ne 0 ]; then
  echo
  echo "[!] Pipeline exited with status $PIPE_STATUS — check $LOG"
  exit "$PIPE_STATUS"
fi

echo
echo "[✓] Smoke test complete. Log at $LOG"

