#!/usr/bin/env python3
"""
Generate a room-name + dimensions CSV form for a claim job.

Usage:
  python iguide/generate_room_name_form.py --job data/job-0001 --mode form
  # Optional: seed rooms from a simple list (comma-separated)
  python iguide/generate_room_name_form.py --job data/job-0001 --rooms "Living Room,Kitchen,Bedroom 1"

Behavior:
- Writes <job>/room_name_form.csv with columns:
    Room, Length (ft'in"), Width (ft'in"), Ceiling (ft'in"), Notes
- If seed files exist, it will try to pre-populate rooms from:
    <job>/rooms.csv   (expects header with 'room' or first column as room names)
    <job>/room_names.txt (one room per line)
- Otherwise it will use default placeholders.
- Prints the CSV path to STDOUT on success and exits 0.
- On error, prints a readable message to STDERR and exits 1.

Notes:
- Keep all measurements in feet & inches (e.g., 9'6") per project requirements.
"""

from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path

DEFAULT_ROOMS = [
    "Living Room",
    "Kitchen",
    "Bedroom 1",
    "Bedroom 2",
    "Bathroom",
    "Hallway",
    "Laundry",
    "Dining Room",
    "Primary Bedroom",
    "Primary Bathroom",
]

HEADER = ["Room", "Length (ft'in\")", "Width (ft'in\")", "Ceiling (ft'in\")", "Notes"]


def read_rooms_from_csv(csv_path: Path) -> list[str]:
    rooms: list[str] = []
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                return rooms
            header = [h.strip().lower() for h in rows[0]]
            # Try to find a 'room' column; else fall back to first column
            if "room" in header:
                idx = header.index("room")
                for r in rows[1:]:
                    if len(r) > idx and r[idx].strip():
                        rooms.append(r[idx].strip())
            else:
                for r in rows[1:]:
                    if r and r[0].strip():
                        rooms.append(r[0].strip())
    except Exception:
        # Quietly ignore; caller can decide to use defaults
        pass
    return rooms


def read_rooms_from_txt(txt_path: Path) -> list[str]:
    rooms: list[str] = []
    try:
        for line in txt_path.read_text(encoding="utf-8").splitlines():
            name = line.strip()
            if name:
                rooms.append(name)
    except Exception:
        pass
    return rooms


def discover_rooms(job_dir: Path, cli_rooms: list[str] | None) -> list[str]:
    # Priority: explicit --rooms > rooms.csv > room_names.txt > defaults
    if cli_rooms:
        seeded = [r.strip() for r in cli_rooms if r.strip()]
        if seeded:
            return seeded

    csv_candidate = job_dir / "rooms.csv"
    if csv_candidate.exists():
        rooms = read_rooms_from_csv(csv_candidate)
        if rooms:
            return rooms

    txt_candidate = job_dir / "room_names.txt"
    if txt_candidate.exists():
        rooms = read_rooms_from_txt(txt_candidate)
        if rooms:
            return rooms

    return DEFAULT_ROOMS[:]


def write_form_csv(out_path: Path, rooms: list[str]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for name in rooms:
            # Leave dimension cells blank for manual entry (feet & inches like 9'6")
            writer.writerow([name, "", "", "", ""])


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate room-name + dimensions form CSV.")
    parser.add_argument("--job", required=True, help="Path to job folder (e.g., data/job-0001)")
    parser.add_argument("--mode", default="form", choices=["form"], help="Operation mode (default: form)")
    parser.add_argument(
        "--rooms",
        default=None,
        help="Optional comma-separated list of room names to seed the form (overrides autodetect).",
    )
    args = parser.parse_args()

    job_dir = Path(args.job).expanduser().resolve()
    if not job_dir.exists() or not job_dir.is_dir():
        sys.stderr.write(f"[ERROR] Job folder not found: {job_dir}\n")
        return 1

    # Prepare room list
    cli_rooms = [r.strip() for r in args.rooms.split(",")] if args.rooms else None
    rooms = discover_rooms(job_dir, cli_rooms)
    if not rooms:
        sys.stderr.write("[ERROR] No rooms discovered or provided.\n")
        return 1

    # Output path lives inside the job folder
    out_csv = job_dir / "room_name_form.csv"
    try:
        write_form_csv(out_csv, rooms)
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to write CSV: {e}\n")
        return 1

    # Success: print the path for the Flask caller to capture
    sys.stdout.write(str(out_csv) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
