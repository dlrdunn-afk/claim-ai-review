import json
import os
import csv

job_id = "job-0001"
job_dir = f"data/{job_id}"

# Load input data
with open(f"{job_dir}/job_metadata.json") as f:
    metadata = json.load(f)

with open(f"{job_dir}/claim_assumptions.json") as f:
    assumptions = json.load(f)

with open(f"{job_dir}/policy_summary.json") as f:
    policy = json.load(f)

os.makedirs("out", exist_ok=True)
csv_file = "out/estimate_xact.csv"

with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)

    # Header format: Room, Line Item Code, Description, Quantity
    writer.writerow(["Room", "Line Item Code", "Description", "Quantity/Length"])

    cause = metadata.get("cause", "").lower()

    # 🔹 Flood
    if cause == "flood":
        height = metadata.get("flood_water_height_in", 0)
        if height > 0:
            writer.writerow(["Living Room", "DRYRM2", "Drywall removal up to 2ft", 120])
            writer.writerow(["Kitchen", "CABLOW", "Clean and regrout lower cabinets", 10])
            writer.writerow(["Hallway", "BSBRD", "Baseboard removal & replacement", 40])

    # 🔹 Wind
    elif cause == "wind":
        if "tree on house" in assumptions.get("notes", "").lower():
            writer.writerow(["Roof", "ROFDEM", "Remove damaged roof decking", 30])
            writer.writerow(["Interior", "TRPLCL", "Tarp or temporary cover", 50])

    # 🔹 Fire
    elif cause == "fire":
        writer.writerow(["Kitchen", "FIRCLN", "Fire damage cleanup", 100])
        writer.writerow(["Entire Home", "ODRRM", "Odor removal / ozone treatment", 200])

    # 🔹 Mold remediation
    if assumptions.get("mold_remediation_needed"):
        writer.writerow(["Bathroom", "MOLDCLN", "Mold remediation", 100])

    # 🔹 ALE (Additional Living Expenses)
    if policy.get("ALE_coverage") == "yes":
        writer.writerow(["N/A", "ALE", "Temporary housing allowance (7 days)", 7])

    # 🔹 Ordinance & Law (code upgrade)
    if policy.get("ordinance_and_law") == "yes":
        writer.writerow(["Electrical", "CODEUP", "Electrical code upgrades", 25])

print(f"✅ Estimate (Xactimate-ready) created: {csv_file}")
