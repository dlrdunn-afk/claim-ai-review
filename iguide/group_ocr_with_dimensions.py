import csv
import re
import sys
from collections import defaultdict

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
input_file = f"out/{job_id}_ocr_rooms.csv"
output_file = f"out/{job_id}_ocr_grouped_with_dimensions.csv"


def extract_feet_inches(text):
    match = re.search(r"(\d+)[^\d]+(\d+)?", text)
    if not match:
        return None
    feet = int(match.group(1))
    inches = int(match.group(2)) if match.group(2) else 0
    return feet + inches / 12.0


# Load OCR lines
lines = []
with open(input_file, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        txt = row["Room Name"].strip().replace("°", "'").replace('"', '"')
        lines.append(
            {
                "text": txt,
                "x": int(row["X"]),
                "y": int(row["Y"]),
            }
        )

# Group lines that are near each other (y distance < 40)
lines.sort(key=lambda r: r["y"])
groups = []
current = []
for i, row in enumerate(lines):
    if not current:
        current.append(row)
        continue
    if abs(row["y"] - current[-1]["y"]) < 40:
        current.append(row)
    else:
        groups.append(current)
        current = [row]
if current:
    groups.append(current)

# Parse each group
parsed_rooms = []
for g in groups:
    texts = [r["text"] for r in g]
    combined = " ".join(texts)
    name_match = re.search(
        r"(BEDROOM|LIVING|PRIMARY|KITCHEN|BATH|ENSUITE|GARAGE|STORAGE|CLOSET|3PC|4PC|PANTRY)",
        combined.upper(),
    )
    dim_match = re.findall(r"(\d+[\'’][^\dx]+[\d\"]{1,3})", combined)

    if name_match:
        room_name = name_match.group(1)
        width = length = None
        if len(dim_match) >= 1:
            width = extract_feet_inches(dim_match[0])
        if len(dim_match) >= 2:
            length = extract_feet_inches(dim_match[1])
        parsed_rooms.append(
            {
                "Room Name": room_name,
                "Width (ft)": round(width, 2) if width else "",
                "Length (ft)": round(length, 2) if length else "",
                "Y": g[0]["y"],
            }
        )

# Save
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=parsed_rooms[0].keys())
    writer.writeheader()
    writer.writerows(parsed_rooms)

print(f"✅ Parsed {len(parsed_rooms)} rooms with dimensions.")
print(f"📄 Saved to: {output_file}")
