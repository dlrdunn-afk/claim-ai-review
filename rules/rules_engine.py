import json
import os

job_id = "job-0001"
job_meta_path = f"data/{job_id}/job_metadata.json"
output_path = f"data/{job_id}/claim_assumptions.json"

# Load job intake data
with open(job_meta_path, "r") as f:
    metadata = json.load(f)

assumptions = {}

# Apply peril-specific rules
cause = metadata.get("cause", "").lower()


if cause == "flood":
    height = metadata.get("flood_water_height_in", 0)
    assumptions["flood_covered_height_ft"] = 2
    assumptions["drywall_replacement_needed"] = height >= 24
    assumptions["tile_can_be_cleaned_only"] = True
    assumptions["cabinet_base_covered"] = height >= 6
    assumptions["full_kitchen_replace"] = height >= 36

elif cause == "fire":
    smoke_all = metadata.get("smoke_whole_home", False)
    assumptions["smoke_damage_contents"] = smoke_all
    assumptions["clean_vs_replace"] = "replace" if smoke_all else "clean"
    assumptions["structure_damaged"] = True
    assumptions["possible_code_upgrades"] = True

elif cause == "wind":
    assumptions["tree_on_house"] = True
    assumptions["roof_replacement_needed"] = metadata.get("roof_damage", False)
    assumptions["interior_ceiling_affected"] = metadata.get("interior_damage", False)
    assumptions["tarp_charge_applicable"] = True

elif cause == "storm":
    assumptions["shingle_loss_expected"] = True
    assumptions["roof_damaged"] = metadata.get("roof_damage", False)
    assumptions["interior_ceiling_damage"] = metadata.get("interior_damage", False)

elif cause == "water":
    assumptions["category_3_water"] = True
    assumptions["remove_all_affected_materials"] = True
    assumptions["drying_equipment_needed"] = True

# Save output
os.makedirs(f"data/{job_id}", exist_ok=True)
with open(output_path, "w") as f:
    json.dump(assumptions, f, indent=2)

print(f"✅ Claim logic saved to: {output_path}")

