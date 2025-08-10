#!/usr/bin/env bash
set -eu

LOGFILE="logs/smoke_latest.log"
: > "$LOGFILE"

pause() {
  echo ""
  echo "──────────────────────────────────────────────"
  echo "Log saved to: $LOGFILE"
  echo "Press ENTER to close..."
  read -r
}

trap 'echo ""; echo "ERROR occurred. See $LOGFILE"; pause; exit 1' ERR

JOB="data/job-smoke-001"
mkdir -p "$JOB/photos"

{
  echo "==> Generating manual CSV for: $JOB"
  python3 run_pipeline.py --job "$JOB" --manual-dimensions
} 2>&1 | tee -a "$LOGFILE"

CSV="$JOB/manual_room_dimensions.csv"
if [ ! -f "$CSV" ]; then
  echo "Expected $CSV to be created but it wasn't." | tee -a "$LOGFILE"
  pause; exit 1
fi

echo "==> Edit $CSV (feet/inches only). Example rows:"         | tee -a "$LOGFILE"
echo "room_name,length_ft,length_in,width_ft,width_in,ceiling_ft,ceiling_in" | tee -a "$LOGFILE"
echo "Living Room,12,0,10,0,8,0"                               | tee -a "$LOGFILE"
echo "Kitchen,9,6,8,0,8,0"                                     | tee -a "$LOGFILE"
read -r -p "Press ENTER after you save the CSV..." _

{
  echo "==> Running pipeline with manual dimensions"
  python3 run_pipeline.py --job "$JOB" --use-manual
} 2>&1 | tee -a "$LOGFILE"

OUT1="out/job-smoke-001/xactimate_estimate.csv"
OUT2="out/job-smoke-001/estimate_xact_import.csv"
if [ -f "$OUT1" ]; then
  echo "PASS: Found $OUT1" | tee -a "$LOGFILE"
elif [ -f "$OUT2" ]; then
  echo "PASS: Found $OUT2" | tee -a "$LOGFILE"
else
  echo "FAIL: Expected output CSV not found in out/job-smoke-001/" | tee -a "$LOGFILE"
  pause; exit 1
fi

echo "Smoke test completed successfully." | tee -a "$LOGFILE"
pause
