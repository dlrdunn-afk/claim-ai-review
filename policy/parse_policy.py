import os
import json
import PyPDF2

job_id = "job-0001"
policy_path = f"data/{job_id}/policy.pdf"
output_path = f"data/{job_id}/policy_summary.json"

# Read the policy PDF
with open(policy_path, "rb") as file:
    reader = PyPDF2.PdfReader(file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()

# Extract basic coverage terms
summary = {
    "ALE_coverage": "yes" if "additional living expense" in full_text.lower() else "unknown",
    "ordinance_and_law": "yes" if "ordinance or law" in full_text.lower() else "unknown",
    "mold_limit_found": "yes" if "mold limit" in full_text.lower() else "unknown",
    "exclusions": [],
}

# Scan for common exclusions
for exclusion in ["flood", "earthquake", "wear and tear", "neglect"]:
    if exclusion in full_text.lower():
        summary["exclusions"].append(exclusion)

# Save results
os.makedirs(f"data/{job_id}", exist_ok=True)
with open(output_path, "w") as f:
    json.dump(summary, f, indent=2)

print(f"✅ Policy summary saved to: {output_path}")
