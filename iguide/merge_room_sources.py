import csv
import os
import sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
xml_file = f"out/{job_id}_room_data.csv"
ocr_file = f"out/{job_id}_ocr_rooms.csv"
output_file = f"out/{job_id}_room_data_validated.csv"

# Load OCR room names
ocr_rooms = []
with open(ocr_file, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row["Room Name"].strip().upper()
        if name and any(c.isalpha() for c in name):
            ocr_rooms.append(name)

ocr_set = set(ocr_rooms)
print(f"📦 Rooms detected in OCR: {len(ocr_set)}")

# Load XML room data
with open(xml_file, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Try to validate XML room names
for row in rows:
    original = row["Room Name"].upper()
    row["Validated"] = "✅" if original in ocr_set else "❌"

# Save result
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Room validation output saved to: {output_file}")
