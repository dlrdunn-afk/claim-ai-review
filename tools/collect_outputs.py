import argparse, pathlib, shutil, glob

p = argparse.ArgumentParser()
p.add_argument("--job", required=True)
a = p.parse_args()

job = pathlib.Path(a.job)
jobid = job.name
outdir = pathlib.Path("out")/jobid
outdir.mkdir(parents=True, exist_ok=True)

patterns = [
    "out/estimate_xact_import.csv",
    "out/estimate_xact_final.csv",
    "out/estimate_xact_merged.csv",
    "out/estimate_xact_with_notes.csv",
    "out/estimate_xact.csv",
    "out/*--job*_room_data*.csv",
    "out/*room_data*.csv",
]

moved = []
for pat in patterns:
    for f in glob.glob(pat):
        src = pathlib.Path(f)
        if not src.is_file():
            continue
        name = src.name
        if name.startswith("--job"):
            name = f"{jobid}_room_data.csv"
        dest = outdir/name
        if dest.exists():
            dest = outdir/f"{dest.stem}_dup{dest.suffix}"
        shutil.move(str(src), str(dest))
        moved.append(dest)

for f in glob.glob(f"out/{jobid}*"):
    src = pathlib.Path(f)
    if src.is_file():
        dest = outdir/src.name
        if str(dest) != str(src):
            if dest.exists():
                dest.unlink()
            shutil.move(str(src), str(dest))

print(f"Collected {len(moved)} files into {outdir}")
