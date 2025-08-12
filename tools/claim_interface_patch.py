from pathlib import Path
import fileinput

target_file = Path("tools/claim_interface.py")

# Lines to insert after the flask import line
insert_block = """from flask import Flask, request, render_template_string, send_from_directory, flash, redirect, url_for

# Cause of Loss options (used in dropdown)
CAUSES = [
    "hurricane", "windstorm", "hail", "flood", "mold", "fire", "lightning", "smoke", "explosion",
    "riot_civil_commotion", "vandalism", "theft", "falling_object", "weight_of_ice_snow_sleet",
    "volcanic_eruption", "sudden_accidental_water_discharge", "freezing", "electrical_surge",
    "vehicle_impact", "aircraft_impact", "other"
]
"""

lines = target_file.read_text().splitlines()
for i, line in enumerate(lines):
    if line.strip().startswith("from flask import"):
        lines[i] = insert_block
        break

target_file.write_text("\n".join(lines))
print("✓ Added CAUSES list to claim_interface.py")
