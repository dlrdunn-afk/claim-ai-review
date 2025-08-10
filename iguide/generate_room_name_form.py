import csv
import os
import sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"

# This file contains all room names we've found (from OCR, XML, etc.)
room_file = f"out/{job_id}_room_data_validated.csv"
output_file = f"out/{job_id}_manual_room_dims.csv"

if not os.path.exists(room_file):
    print(f"❌ Cannot find source room file: {room_file}")
    sys.exit(1)

room_names = set()

# Collect unique room names
with open(room_file, newline='') as f:
    for row in csv.DictReader(f):
        name = row.get("Room Name") or row.get("Room") or row.get("Name")
        if name:
            room_names.add(name.strip().upper())

# Write form for manual input
with open(output_file, "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Room Name", "Width (ft)", "Length (ft)"])
    for name in sorted(room_names):
        writer.writerow([name, "", ""])

print(f"✅ Manual input form saved to: {output_file}")
print("✍️  Fill in width and length manually, then run the import step.")
