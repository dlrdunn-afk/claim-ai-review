import csv
import os


def _room_data_path(job):
    slug = os.path.basename(job.rstrip("/")) if job else "job-0001"

    # Prefer job-specific CSV; fall back to legacy names
    for cand in (
        f"out/{slug}_room_data.csv",
        "_room_data_path(args.job)",
        "out/--job_room_data.csv",
    ):
        if os.path.exists(cand):
            return cand
    return f"out/{slug}_room_data.csv"


room_data_path = "_room_data_path(args.job)"
estimate_path = "out/estimate_xact.csv"
merged_path = "out/estimate_xact_merged.csv"

if not os.path.exists(room_data_path):
    print(f"❌ Missing room data file: {room_data_path}")
    exit()

if not os.path.exists(estimate_path):
    print(f"❌ Missing estimate file: {estimate_path}")
    exit()

# Load room data into a dictionary
room_data = {}
with open(room_data_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        room_data[row["Room Name"].strip().lower()] = row

# Merge estimate with room data
merged_rows = []
with open(estimate_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        room_name = row["Room"].strip().lower()
        room_info = room_data.get(room_name, {})
        merged_row = {**row, **room_info}
        merged_rows.append(merged_row)

# Write merged file
if merged_rows:
    with open(merged_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=merged_rows[0].keys())
        writer.writeheader()
        writer.writerows(merged_rows)
    print(f"✅ Merged estimate saved to: {merged_path}")
else:
    print("⚠️ No rows merged — check room names in both files.")
