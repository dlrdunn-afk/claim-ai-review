import csv
import sys
from pathlib import Path

"""
Generates estimate rows using either:
  out/<job_id>_room_data_merged.csv   (preferred)
  or falls back to
  out/<job_id>_room_data.csv

OUTPUT: out/estimate_xact.csv
"""

FIELDS_OUT = ["Room", "Line Item Code", "Description", "Quantity/Length"]


def load_rooms(app_root, job_id):
    out = app_root / "out"
    merged = out / f"{job_id}_room_data_merged.csv"
    base = out / f"{job_id}_room_data.csv"

    src = None
    if merged.exists():
        src = merged
    elif base.exists():
        src = base
    else:
        print(
            f"❌ No room data CSV found for {job_id}. Looked for:\n - {merged}\n - {base}"
        )
        return []

    rooms = []
    with src.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize names used downstream
            name = (row.get("Room") or row.get("Room Name") or "").strip()
            if not name:
                continue
            rooms.append({"Room": name})
    print(f"✅ Loaded {len(rooms)} rooms from {src.name}")
    return rooms


def main():
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
    app_root = Path(__file__).resolve().parents[1]
    out_dir = app_root / "out"
    out_dir.mkdir(exist_ok=True)
    out_csv = out_dir / "estimate_xact.csv"

    rooms = load_rooms(app_root, job_id)
    if not rooms:
        # Still write a header so later steps don't crash
        with out_csv.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS_OUT).writeheader()
        print("⚠️ No estimate rows generated.")
        return

    estimates = []
    for r in rooms:
        room = r["Room"]
        # Add a few sample items — adjust to your logic
        estimates.append(
            {
                "Room": room,
                "Line Item Code": "DRYBD",
                "Description": "Drywall base prep (LF)",
                "Quantity/Length": 10,
            }
        )
        estimates.append(
            {
                "Room": room,
                "Line Item Code": "FLRPLS",
                "Description": "Flooring - replace (SF)",
                "Quantity/Length": 50,
            }
        )
        estimates.append(
            {
                "Room": room,
                "Line Item Code": "PNTINT",
                "Description": "Paint interior walls (SF)",
                "Quantity/Length": 50,
            }
        )

    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_OUT)
        w.writeheader()
        w.writerows(estimates)

    print(f"✅ Generated estimate using room data → {out_csv}")


if __name__ == "__main__":
    main()
