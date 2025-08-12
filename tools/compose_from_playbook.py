#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

# Args: --job <jobdir> --out <outdir> --cause <cause>
jobdir = None
outdir = None
cause = None
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == "--job":
        jobdir = Path(args[i + 1])
    if a == "--out":
        outdir = Path(args[i + 1])
    if a == "--cause":
        cause = (args[i + 1] or "").lower()

ROOT = Path(__file__).resolve().parents[1]
PLAYDIR = ROOT / "tools" / "playbooks"
outdir = outdir or (ROOT / "out")
outdir.mkdir(parents=True, exist_ok=True)

# choose playbook by cause (fallback to flood)
name = (cause or "flood").lower().replace(" ", "_")
pb_path = PLAYDIR / f"{name}.json"
if not pb_path.exists():
    pb_path = PLAYDIR / "flood.json"

with open(pb_path, "r", encoding="utf-8") as f:
    pb = json.load(f)

rows = []
# global items first
for it in pb.get("global_items", []):
    if isinstance(it, dict):
        desc = it.get("item") or it.get("description") or it.get("code") or "Scope Item"
        qty = it.get("qty") or it.get("quantity") or it.get("weight") or 1
    else:
        desc = str(it)
        qty = 1
    rows.append(["General", desc, qty, f"Cause: {pb.get('cause_of_loss','unknown')}"])

# then per-room packages
for room, items in (pb.get("rooms") or {}).items():
    for it in items:
        if isinstance(it, dict):
            desc = (
                it.get("item")
                or it.get("description")
                or it.get("code")
                or "Scope Item"
            )
            qty = it.get("qty") or it.get("quantity") or it.get("weight") or 1
        else:
            desc = str(it)
            qty = 1
        rows.append([room, desc, qty, ""])

# Always write with headers Xact-style
csv_path = outdir / "estimate_xact_with_notes.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["room", "item", "qty", "notes"])
    w.writerows(rows if rows else [["General", "(empty draft)", 1, ""]])
print(str(csv_path))
