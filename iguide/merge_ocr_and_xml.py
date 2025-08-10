import csv
import sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
xml_file = f"out/{job_id}_room_data.csv"
ocr_file = f"out/{job_id}_ocr_grouped_with_dimensions.csv"
out_file = f"out/{job_id}_room_data_merged.csv"

# Load XML rooms
with open(xml_file, newline='') as f:
    xml_rooms = list(csv.DictReader(f))

# Load OCR room dimensions
ocr_map = {}
with open(ocr_file, newline='') as f:
    for row in csv.DictReader(f):
        name = row["Room Name"].strip().upper()
        ocr_map[name] = {
            "Width (ft)": row["Width (ft)"],
            "Length (ft)": row["Length (ft)"]
        }

# Merge: use OCR width/length only if missing in XML
for r in xml_rooms:
    name = r["Room Name"].strip().upper()
    ocr = ocr_map.get(name)
    if ocr:
        r["Width (ft)"] = r.get("Width (ft)") or ocr["Width (ft)"]
        r["Length (ft)"] = r.get("Length (ft)") or ocr["Length (ft)"]
        try:
            r["Area (ft²)"] = round(float(r["Width (ft)"]) * float(r["Length (ft)"]), 2)
        except:
            r["Area (ft²)"] = ""

# Write output
with open(out_file, "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=xml_rooms[0].keys() | {"Width (ft)", "Length (ft)", "Area (ft²)"})
    writer.writeheader()
    writer.writerows(xml_rooms)

print(f"✅ Merged XML + OCR room data → {out_file}")
