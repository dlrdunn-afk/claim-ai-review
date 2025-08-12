import csv
import os
import sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"

manual_file = f"out/{job_id}_manual_room_dims.csv"
output_file = f"out/{job_id}_room_data_merged.csv"

if not os.path.exists(manual_file):
    print(f"❌ Cannot find manual input file: {manual_file}")
    sys.exit(1)

rows = []
with open(manual_file, newline="") as f:
    for row in csv.DictReader(f):
        try:
            name = row["Room Name"].strip().upper()
            width = float(row["Width (ft)"])
            length = float(row["Length (ft)"])
            area = round(width * length, 2)
            rows.append(
                {
                    "Room": name,
                    "Width (ft)": width,
                    "Length (ft)": length,
                    "Area (ft²)": area,
                }
            )
        except Exception as e:
            print(f"⚠️ Skipping row: {row} → {e}")

if not rows:
    print("❌ No valid rows imported. Please check your CSV.")
    sys.exit(1)

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["Room", "Width (ft)", "Length (ft)", "Area (ft²)"]
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Imported manual room dimensions → {output_file}")
