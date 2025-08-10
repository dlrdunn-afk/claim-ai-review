import os
import xml.etree.ElementTree as ET

# === Setup ===
iguide_folder = "data/job-0001/iguide"
xml_file = None

# Find the XML file
for f in os.listdir(iguide_folder):
    if f.lower().endswith(".xml"):
        xml_file = os.path.join(iguide_folder, f)
        break

if not xml_file:
    print("❌ No iGUIDE XML file found.")
    exit()

# Parse the XML
tree = ET.parse(xml_file)
root = tree.getroot()

rooms = []

# Look for SKETCHROOM tags
for room in root.findall(".//SKETCHROOM"):
    room_id = room.get("id", "Unknown")
    ceiling = room.get("ceilingHeight", "Unknown")
    wall_ids = room.get("wallIDs", "")

    label = room.find(".//SKETCHCDATACHILD")
    name = label.text.strip() if label is not None and label.text else "Unnamed"

    rooms.append({
        "id": room_id,
        "name": name,
        "ceiling": ceiling,
        "walls": wall_ids
    })

# Display the parsed results
print(f"\n🧾 Parsed {len(rooms)} rooms:\n")

for r in rooms:
    print(f"🏠 Room: {r['name']} | ID: {r['id']} | Ceiling: {r['ceiling']} | Walls: {r['walls']}")
