#!/usr/bin/env python3
"""
Flask UI for CLAIM‑AI

Features:
- Home page with “New Claim” and “Existing Claim”
- Upload form for a new claim (files stored under data/<job-id>/)
- After upload the system creates a blank room‑CSV and shows a table
  where the user can confirm or edit dimensions.
- Saving the table writes the merged CSV, runs the full pipeline,
  and presents a download link for the final Xactimate CSV.
"""

from flask import Flask, request, render_template, redirect, url_for, send_file
import os
import uuid
import subprocess                     # to call other scripts
from pathlib import Path
import pandas as pd
from werkzeug.utils import secure_filename
# -----------------------------------------------------------------
# Relative import – works when this file is executed as a module
# -----------------------------------------------------------------
from .logger_helper import get_job_logger

app = Flask(__name__)

# -----------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]        # project root
UPLOAD_FOLDER = BASE_DIR / "data"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "xml"}

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)     # Flask expects a string
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MiB upload limit


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is one we accept."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------------------
# Helper: load the room CSV (merged if it exists, otherwise baseline)
# -----------------------------------------------------------------
def _load_room_csv(job_id: str) -> pd.DataFrame:
    out_dir = BASE_DIR / "out"

    merged_path = out_dir / f"{job_id}_room_data_merged.csv"
    if merged_path.is_file():
        return pd.read_csv(merged_path)

    baseline_path = out_dir / f"{job_id}_room_data.csv"
    if baseline_path.is_file():
        return pd.read_csv(baseline_path)

    # Empty placeholder – UI will still render a table (no rows)
    return pd.DataFrame(columns=["Room", "Width", "Length", "Height"])


# -----------------------------------------------------------------
# Home page – choose New Claim or Existing Claim
# -----------------------------------------------------------------
@app.route("/")
def home():
    """Landing page – simple two‑button menu."""
    return render_template("home.html")


# -----------------------------------------------------------------
# Existing Claim – list all job folders under data/
# -----------------------------------------------------------------
@app.route("/existing_claim")
def existing_claim():
    """
    Scan ./data for sub‑folders that look like job‑ids and list them.
    """
    data_root = BASE_DIR / "data"
    jobs = sorted([p.name for p in data_root.iterdir() if p.is_dir()])
    return render_template("existing_claims.html", jobs=jobs)


# -----------------------------------------------------------------
# New Claim – GET = show upload form, POST = handle files & jump to edit page
# -----------------------------------------------------------------
@app.route("/new_claim", methods=["GET", "POST"])
def new_claim():
    if request.method == "POST":
        # -------------------------------------------------------------
        # 1️⃣ Gather uploaded files and store them under data/<job_id>/
        # -------------------------------------------------------------
        job_id = request.form.get("job_id") or f"job-{uuid.uuid4().hex[:8]}"
        job_dir = BASE_DIR / "data" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save each uploaded file
        for key in request.files:
            f = request.files[key]
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = job_dir / filename
                f.save(save_path)

        # -------------------------------------------------------------
        # 2️⃣ Run the baseline room‑generation script.
        #    This creates out/<job_id>_manual_room_dims.csv (blank dimensions)
        # -------------------------------------------------------------
        subprocess.run(
            ["python3", "iguide/generate_room_name_form.py", job_id],
            cwd=BASE_DIR,
            check=True,
        )

        # -------------------------------------------------------------
        # 3️⃣ Redirect to the room‑edit page
        # -------------------------------------------------------------
        return redirect(url_for("review_rooms", job_id=job_id))

    # GET – show the upload form (template lives in tools/templates)
    return render_template("new_claim.html")


# -----------------------------------------------------------------
# Review rooms – editable table (edit_rooms.html)
# -----------------------------------------------------------------
@app.route("/job/<job_id>/review", methods=["GET"])
def review_rooms(job_id):
    """
    Load the CSV that contains the current room list (with any dimensions)
    and render the HTML table where the user can edit them.
    """
    try:
        df = _load_room_csv(job_id)
        df = df.fillna("")                     # blanks instead of NaN
        room_rows = df.to_dict(orient="records")
    except Exception as exc:
        return f"<h2>Error loading rooms for {job_id}: {exc}</h2>", 500

    return render_template(
        "edit_rooms.html",
        job_id=job_id,
        room_rows=room_rows,
        error=None,
    )


# -----------------------------------------------------------------
# Save edited dimensions, run the pipeline, then show “done” page
# -----------------------------------------------------------------
@app.route("/job/<job_id>/save_rooms", methods=["POST"])
def save_rooms(job_id):
    """
    1️⃣ Grab the edited Width/Length/Height values from the form.
    2️⃣ Write a new merged‑room CSV that the rest of the pipeline expects.
    3️⃣ Call the existing pipeline runner (tools/run_pipeline.py).
    4️⃣ Redirect to a small “finished” page with a download link.
    """
    try:
        out_dir = BASE_DIR / "out"

        # Load the original list of rooms so we keep the names
        base_df = _load_room_csv(job_id).fillna("")
        # How many rows were submitted? (count width_* fields)
        n_rows = sum(1 for k in request.form.keys() if k.startswith("width_"))

        rows = []
        for i in range(n_rows):
            width  = request.form.get(f"width_{i}", "").strip()
            length = request.form.get(f"length_{i}", "").strip()
            height = request.form.get(f"height_{i}", "").strip()

            # Preserve the room name if we already have it; otherwise a placeholder
            room_name = base_df.iloc[i]["Room"] if i < len(base_df) else f"Room_{i+1}"
            rows.append({
                "Room":   room_name,
                "Width":  width,
                "Length": length,
                "Height": height,
            })

        merged_df = pd.DataFrame(rows)
        merged_path = out_dir / f"{job_id}_room_data_merged.csv"
        merged_df.to_csv(merged_path, index=False)

    except Exception as exc:
        # Re‑render the edit page with an error message
        df = _load_room_csv(job_id).fillna("")
        return render_template(
            "edit_rooms.html",
            job_id=job_id,
            room_rows=df.to_dict(orient="records"),
            error=f"Failed to save dimensions: {exc}",
        ), 500

    # -------------------------------------------------------------
    # Run the pipeline (the script you already have)
    # -------------------------------------------------------------
    try:
        from tools.run_pipeline import main as run_main
        import sys
        sys.argv = ["run_pipeline.py", job_id]   # mimic CLI args
        run_main()
    except Exception as exc:
        return f"<h2>Pipeline failed after saving dimensions: {exc}</h2>", 500

    # -------------------------------------------------------------
    # Show a tiny “finished” page with a download link
    # -------------------------------------------------------------
    return redirect(url_for("pipeline_done", job_id=job_id))


# -----------------------------------------------------------------
# Finished page – tells the user the pipeline is done and offers download
# -----------------------------------------------------------------
@app.route("/job/<job_id>/done", methods=["GET"])
def pipeline_done(job_id):
    out_dir = BASE_DIR / "out"
    final_csv = out_dir / f"{job_id}_estimate_xact_import.csv"

    if final_csv.is_file():
        link = f"<a href='/download/{job_id}'>Download final CSV</a>"
        msg = f"✅ Pipeline finished! {link}"
    else:
        msg = "⚠️ Pipeline finished, but the final CSV was not found."

    return f"<h2>{msg}</h2><p><a href='{url_for('home')}'>← Back to Home</a></p>"


# -----------------------------------------------------------------
# Download route – serves the final Xactimate CSV as an attachment
# -----------------------------------------------------------------
@app.route("/download/<job_id>", methods=["GET"])
def download_csv(job_id):
    out_dir = BASE_DIR / "out"
    csv_path = out_dir / f"{job_id}_estimate_xact_import.csv"
    if not csv_path.is_file():
        return "File not found", 404
    return send_file(csv_path, as_attachment=True)


# -----------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------
if __name__ == "__main__":
    # Ensure the upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(port=5002, debug=True)
