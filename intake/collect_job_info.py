import json
import os

job_id = "job-0001"
metadata = {"job_id": job_id}

print("📝 Claim Intake – Cause of Loss")
cause = input("Cause of loss [Flood, Fire, Storm, Water, Wind]: ").strip().lower()

metadata["cause"] = cause

if cause == "flood":
    height = input("How high did the water rise? (in inches): ").strip()
    metadata["flood_water_height_in"] = int(height)
    has_photos = input("Were photos taken before mitigation? (yes/no): ").strip().lower()
    metadata["pre_mitigation_photos"] = has_photos == "yes"

elif cause == "fire":
    fire_type = input("Was it a kitchen fire, electrical, lightning, or unknown?: ").strip().lower()
    smoke_spread = input("Did smoke affect the entire home? (yes/no): ").strip().lower()
    metadata["fire_type"] = fire_type
    metadata["smoke_whole_home"] = smoke_spread == "yes"

elif cause in ["storm", "water", "wind"]:
    roof_damage = input("Was there roof damage? (yes/no): ").strip().lower()
    interior_damage = input("Was there interior water damage? (yes/no): ").strip().lower()
    metadata["roof_damage"] = roof_damage == "yes"
    metadata["interior_damage"] = interior_damage == "yes"

# Save to JSON
save_path = f"data/{job_id}/job_metadata.json"
os.makedirs(f"data/{job_id}", exist_ok=True)
with open(save_path, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Intake saved to: {save_path}")
