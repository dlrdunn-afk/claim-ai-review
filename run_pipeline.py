import subprocess
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent

STEPS = [
    ["python3", str(APP_ROOT / "iguide" / "export_room_data.py")],
    ["python3", str(APP_ROOT / "estimate" / "generate_room_estimates.py")],
    ["python3", str(APP_ROOT / "estimate" / "add_justifications.py")],
    ["python3", str(APP_ROOT / "estimate" / "merge_room_and_estimate.py")],
    ["python3", str(APP_ROOT / "estimate" / "apply_policy_rules.py")],
    ["python3", str(APP_ROOT / "estimate" / "export_xactimate_csv.py")],
]


def run_step(cmd, job_id):
    print(f"\n🔹 Running: {' '.join(cmd)} {job_id}")
    try:
        result = subprocess.run(
            cmd + [job_id], capture_output=True, text=True, check=False
        )
        if result.stdout:
            print(result.stdout.rstrip())
        if result.returncode != 0:
            print(f"❌ Step failed: {' '.join(cmd)}")
            if result.stderr:
                print(result.stderr.rstrip())
            return False
        print(f"✅ Done: {Path(cmd[1]).relative_to(APP_ROOT)}")
        return True
    except Exception as e:
        print(f"❌ Exception running {' '.join(cmd)}: {e}")
        return False


def main():
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job-0001"
    for cmd in STEPS:
        ok = run_step(cmd, job_id)
        if not ok:
            print("\n⛔ Pipeline stopped due to error above.")
            break
    else:
        print("\n🎉 All steps complete for", job_id, ". Check the /out folder.")


if __name__ == "__main__":
    main()
