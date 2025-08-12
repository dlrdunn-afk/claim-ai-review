import csv
import sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
input_file = f"out/estimate_xact.csv"
output_file = f"out/estimate_xact_with_notes.csv"


def get_unit(description):
    desc = description.lower()
    if (
        "sqft" in desc
        or "square foot" in desc
        or "per sf" in desc
        or "flooring" in desc
    ):
        return "SQFT"
    elif (
        "lf" in desc
        or "linear" in desc
        or "baseboard" in desc
        or "drywall removal up to" in desc
    ):
        return "LF"
    elif "ea" in desc or "each" in desc or "fixture" in desc or "appliance" in desc:
        return "EA"
    elif "paint" in desc:
        return "SQFT"
    else:
        return "EA"  # default if unsure


with open(input_file, newline="") as f:
    rows = list(csv.DictReader(f))

for row in rows:
    unit = get_unit(row["Description"])
    row["Quantity/Length"] = f'{row["Quantity/Length"]} {unit}'
    row["Justification"] = f"Added based on room dimensions and scope. Unit: {unit}."

# Save output
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Justified estimate saved to: {output_file}")
print(f"📦 Rows: {len(rows)}")
