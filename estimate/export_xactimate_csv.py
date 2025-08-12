import csv
import sys
from pathlib import Path

"""
Read:  out/estimate_xact_final.csv
Write: out/estimate_xact_import.csv

Output columns must be exactly:
  Line Item Code,Room,Quantity/Length

We also append a unit to the quantity if it's missing.
"""

FIELDNAMES_OUT = ["Line Item Code", "Room", "Quantity/Length"]


def detect_unit(code: str, desc: str) -> str:
    c = (code or "").upper()
    d = (desc or "").lower()

    # Heuristics for common items; adjust as needed
    if c in {"DRYBD", "DRYRM2", "BASEDEM", "BASEINST"} or "lf" in d or "linear" in d:
        return "LF"
    if (
        c in {"FLRPLS", "PNTINT", "PNTWALL", "PAINT"}
        or "sf" in d
        or "per sf" in d
        or "square" in d
    ):
        return "SF"
    # Default
    return "QTY"


def normalize_qty(q: str, unit: str) -> str:
    s = (q or "").strip()
    if not s:
        return ""  # caller will skip empty
    # If already includes letters (e.g., "25 SF"), don't double-append
    if any(ch.isalpha() for ch in s):
        return s
    # Try to format numeric nicely
    try:
        val = float(s)
        if abs(val - int(val)) < 1e-9:
            s = str(int(val))
        else:
            s = f"{val:.2f}".rstrip("0").rstrip(".")
    except Exception:
        # keep as-is if not numeric
        pass
    return f"{s} {unit}"


def main():
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
    app_root = Path(__file__).resolve().parents[1]
    out_dir = app_root / "out"
    src = out_dir / "estimate_xact_final.csv"
    dst = out_dir / "estimate_xact_import.csv"

    if not src.exists():
        print(f"❌ Missing input: {src}")
        # still write an empty header so caller doesn't explode
        with dst.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES_OUT).writeheader()
        return

    cleaned = []
    with src.open(newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            code = (row.get("Line Item Code") or "").strip()
            room = (row.get("Room") or row.get("Room Name") or "").strip()
            desc = (row.get("Description") or "").strip()
            qty = (row.get("Quantity/Length") or "").strip()

            if not code or not room or not qty:
                # skip incomplete rows
                continue

            unit = detect_unit(code, desc)
            qty_out = normalize_qty(qty, unit)

            cleaned.append(
                {"Line Item Code": code, "Room": room, "Quantity/Length": qty_out}
            )

    with dst.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES_OUT)
        w.writeheader()
        w.writerows(cleaned)

    print(f"✅ Exported for Xactimate: {dst}  (rows: {len(cleaned)})")


if __name__ == "__main__":
    main()
