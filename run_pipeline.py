import argparse, subprocess, pathlib

parser = argparse.ArgumentParser()
parser.add_argument("--job", required=True, help="Path like data/job-0001")
args, extras = parser.parse_known_args()
job = args.job

def run_step(script):
    cmd = ["python3", script, "--job", job, *extras]
    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

run_step("iguide/export_room_data.py")
run_step("estimate/generate_room_estimates.py")
run_step("estimate/add_justifications.py")
run_step("estimate/merge_room_and_estimate.py")
run_step("estimate/apply_policy_rules.py")
run_step("estimate/export_xactimate_csv.py")

subprocess.run(["python3", "tools/collect_outputs.py", "--job", job], check=True)
print(f"All steps complete for {job}. See out/{pathlib.Path(job).name}/")
