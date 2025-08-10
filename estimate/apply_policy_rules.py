import csv, json, os, sys

print("🔊 apply_policy_rules.py: starting…")

MERGED_IN = "out/estimate_xact_merged.csv"
POLICY_JSON = "data/job-0001/policy_summary.json"
JOB_JSON = "data/job-0001/job_metadata.json"
OUT_CSV = "out/estimate_xact_final.csv"
QA_CSV = "out/estimate_policy_QA.csv"

def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Missing JSON: {path} (using defaults)")
        return {}
    with open(path) as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"❌ Could not parse JSON {path}: {e}")
            return {}

policy = load_json(POLICY_JSON)   # e.g., {"ALE": true, "MoldLimit": 10000}
job = load_json(JOB_JSON)         # e.g., {"cause_of_loss":"Flood","water_height_in":3}

cause = (job.get("cause_of_loss") or "").strip().lower()

def has_ale():
    return bool(policy.get("ALE", True))

def mold_cap():
    cap = policy.get("MoldLimit")
    try:
        return float(cap) if cap is not None else None
    except:
        return None

def is_flood():
    return "flood" in cause

def water_height_in():
    try:
        return float(job.get("water_height_in", 0))
    except:
        return 0.0

def adjust_for_peril(row):
    desc = (row.get("Description") or "").lower()
    notes = row.get("Notes", "")

    if is_flood():
        if "drywall" in desc and ("remove" in desc or "replace" in desc):
            h = water_height_in()
            if h > 0:
                target_in = max(12.0, min(24.0, h + 12.0))
                notes += f" | Flood: drywall addressed to ~{int(target_in)}\" above waterline."
        if "tile" in desc and ("replace" in desc or "new" in desc):
            notes += " | Flood: tile replacement often excluded; adjust to clean/regrout if salvageable."
        if "cabinet" in desc and ("base" in desc or "lower" in desc):
            notes += " | Flood: lower cabinets impacted by rising water commonly non-salvageable."

    row["Notes"] = notes
    return row

def covered(row):
    code = (row.get("Line Item Code") or "").upper().strip()
    if code == "ALE" and not has_ale():
        return False, "ALE removed (no ALE coverage)."
    return True, ""

def annotate_mold(row):
    cap = mold_cap()
    if cap is None:
        return row
    desc = (row.get("Description") or "").lower()
    if "mold" in desc:
        note = row.get("Notes", "")
        note += f" | Subject to mold sublimit (${int(cap):,})."
        row["Notes"] = note
    return row

if not os.path.exists(MERGED_IN):
    print(f"❌ Missing merged estimate: {MERGED_IN}")
    sys.exit(1)

with open(MERGED_IN, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

if not rows:
    print("❌ Merged estimate is empty.")
    sys.exit(1)

kept, removed = [], []
for r in rows:
    r = adjust_for_peril(r)
    r = annotate_mold(r)
    ok, why = covered(r)
    if ok:
        kept.append(r)
    else:
        r["_RemovedReason"] = why
        removed.append(r)

os.makedirs("out", exist_ok=True)

if kept:
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=kept[0].keys())
        writer.writeheader()
        writer.writerows(kept)
    print(f"✅ Final policy-aware estimate: {OUT_CSV} ({len(kept)} lines)")
else:
    print("⚠️ No lines kept—check rules/policy.")

if removed:
    with open(QA_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=removed[0].keys())
        writer.writeheader()
        writer.writerows(removed)
    print(f"🧪 QA (removed lines): {QA_CSV} ({len(removed)} lines)")
else:
    print("✅ No lines removed by policy rules.")
