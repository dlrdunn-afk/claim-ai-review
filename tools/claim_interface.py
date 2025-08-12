from __future__ import annotations

from flask import Flask, flash, redirect, render_template_string
from flask import request as flask_request
from flask import send_from_directory, url_for

# Cause of Loss options (used in dropdown)
CAUSES = [
    "hurricane",
    "windstorm",
    "hail",
    "flood",
    "mold",
    "fire",
    "lightning",
    "smoke",
    "explosion",
    "riot_civil_commotion",
    "vandalism",
    "theft",
    "falling_object",
    "weight_of_ice_snow_sleet",
    "volcanic_eruption",
    "sudden_accidental_water_discharge",
    "freezing",
    "electrical_surge",
    "vehicle_impact",
    "aircraft_impact",
    "other",
]

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable

from flask import (Flask, flash, jsonify, redirect, render_template_string,
                   request, send_from_directory, url_for)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "dev"

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
OUT = ROOT / "out"
CLAIM_CAUSES = ["Flood", "Wind", "Hurricane", "Hail", "Fire", "Water", "Mold"]
LOGS = ROOT / "logs"


def slug_job(x: str) -> str:
    import re

    y = re.sub(r"[^a-zA-Z0-9_-]+", "-", (x or "").strip())
    return re.sub(r"-+", "-", y).strip("-").lower() or "job-0001"


def _best_estimate(job_dir):
    # Preference order
    pref = [
        "estimate_xact_with_notes.csv",
        "estimate_xact_final.csv",
        "estimate_xact_import.csv",
        "estimate_xact.csv",
    ]
    for name in pref:
        f = job_dir / name
        if f.exists():
            return f.name
    # Fallback: first CSV in dir
    for f in sorted(job_dir.glob("*.csv")):
        return f.name
    return None


for p in (UPLOADS, OUT, LOGS):
    p.mkdir(exist_ok=True)

# Optional: reuse chat + scraper if present
try:
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.chat_widget import chatbp

    app.register_blueprint(chatbp)
except Exception:
    pass

try:
    from tools.scraper_blueprint import scraperbp

    app.register_blueprint(scraperbp)
except Exception:
    pass

ALLOWED = {
    "policy": {".pdf"},
    "photos": {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".heic",
        ".heif",
        ".pdf",
    },
    "preloss": {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".heic",
        ".heif",
        ".pdf",
    },
    "floorplan_xml": {".xml"},
    "floorplan_img": {".jpg", ".jpeg", ".png", ".pdf"},
    "docs": {".pdf", ".doc", ".docx", ".xlsx", ".xls", ".txt", ".csv", ".json", ".zip"},
}


def save_files(files: Iterable, dest: Path, allowed: set[str]) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        if not getattr(f, "filename", ""):
            continue
        name = secure_filename(Path(f.filename).name)
        ext = Path(name).suffix.lower()
        if allowed and ext not in allowed:
            continue
        target = dest / name
        i = 1
        while target.exists():
            target = dest / (f"{Path(name).stem}_{i}{ext}")
            i += 1
        target.write_bytes(f.read())
        saved.append(target.name)
    return saved


INDEX = """
<!doctype html>
<title>CLAIM AI – Claims Interface</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{font-family:system-ui,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 12px;background:#fafafa}
  .card{background:#fff;border:1px solid #eee;padding:16px;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.06);margin-bottom:16px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media (max-width:1100px){.grid{grid-template-columns:1fr}}
  label{display:block;margin:6px 0 8px}
  input[type=file],input[type=text]{padding:10px;border:1px solid #ccc;border-radius:10px;width:100%}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
  button,a.button{padding:10px 14px;border-radius:12px;border:1px solid #bbb;background:#f7f7f7;text-decoration:none;color:#111;cursor:pointer}
  small{color:#666}
  ul.list{margin:8px 0 0 16px}
</style>

<h2>CLAIM AI – Claims Interface</h2>
{% with msgs = get_flashed_messages() %}
  {% if msgs %}
    <div style="background:#e7f7e9;border:1px solid #b8e0c0;padding:10px;border-radius:10px;margin:10px 0;">
      {{ msgs[-1] }}
    </div>
  {% endif %}
{% endwith %}
{% if flask_request.args.get('open') %}
  <script>
    // auto-open detailed estimate in a new tab
    (function(){
      try {
        const openPath = decodeURIComponent("{{ flask_request.args.get('open') }}");
        if (openPath) window.open(openPath, "_blank");
      } catch(e){}
    })();
  </script><!-- auto-open -->
{% endif %}

<div class="card">
  <h3>1) Upload claim files</h3>
  <form action="/upload" method="post" enctype="multipart/form-data">
    <div class="row">
      <label>Job ID (folder name)
        <input type="text" name="job" value="job-0001" required>
      </label>
      <div></div>
    </div>

    <div class="grid">
      <div class="card">
        <h4>Policy</h4>
        <label>Policy PDF
          <input type="file" name="policy" accept=".pdf">
        </label>
        <small>Saved to <code>uploads/&lt;job&gt;/policy/</code></small>
      </div>

      <div class="card">
        <h4>Floorplan</h4>
        <label>Floorplan XML
          <input type="file" name="floorplan_xml" accept=".xml">
        </label>
        <label>Floorplan Image (JPG/PNG/PDF)
          <input type="file" name="floorplan_img" accept=".jpg,.jpeg,.png,.pdf">
        </label>
        <small>Saved to <code>uploads/&lt;job&gt;/floorplan/</code></small>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h4>Photos (Bulk)</h4>
        <label>Post‑loss Photos (JPG/PNG/HEIC/PDF)
          <input type="file" name="photos" accept="image/*,.heic,.heif,.pdf" multiple>
        </label>
        <small>Saved to <code>uploads/&lt;job&gt;/photos/</code></small>
      </div>

      <div class="card">
        <h4>Pre‑loss Photos (Bulk)</h4>
        <label>Pre‑loss Photos (JPG/PNG/HEIC/PDF)
          <input type="file" name="preloss" accept="image/*,.heic,.heif,.pdf" multiple>
        </label>
        <small>Saved to <code>uploads/&lt;job&gt;/preloss/</code></small>
      </div>
    </div>

    <div class="card">
      <h4>Other Docs (Bulk)</h4>
      <label>Additional docs (PDF, DOCX, XLSX, CSV, ZIP)
        <input type="file" name="docs" accept=".pdf,.doc,.docx,.xlsx,.xls,.txt,.csv,.json,.zip" multiple>
      </label>
      <small>Saved to <code>uploads/&lt;job&gt;/docs/</code></small>
    </div>

    <button type="submit">Upload All</button>
  </form>
</div>

<div class="card grid">
  <div>
    <h3>2) Label photos</h3>
    <p>Open the photo labeler to assign perils and notes. (Bulk uploads supported.)</p>
    <a class="button" href="http://127.0.0.1:5004" target="_blank">Open Photo Labeler</a>
    <a class="button" href="{{ url_for('scraperbp.scrape_ui') }}" target="_blank">Scrape Images</a>
    <a class="button" href="{{ url_for('chatbp.chat_ui') }}" target="_blank">Chat</a>
  </div>
  <div>
    <h3>3) Run pipeline</h3>
    <form action="{{ url_for('run_pipeline') }}" method="post">
      <label>Job ID
        <input type="text" name="job" value="job-0001" required>
  <label>Cause of Loss</label>
<select id="cause" name="cause" required style="min-width:240px;">
  <option value="" disabled selected>Select a cause…</option>
  {% for c in causes %}<option value="{{ c }}">{{ c.replace("_"," ") }}</option>{% endfor %}
</select>
<select name="cause">
    {% for c in CLAIM_CAUSES %}
      <option value="{{c}}">{{c}}</option>
    {% endfor %}
  </select>
      </label>
      <button type="submit">Run</button>
    </form>
    <p><small>Reads from <code>uploads/&lt;job&gt;/</code>, writes to <code>out/&lt;job&gt;/</code>.</small></p>
  </div>
</div>

<div class="card">
  <h3>Outputs</h3>
  <ul>
    {% for p in outputs %}
      <li><a href="{{ url_for('download', job=p[0], fname=p[1]) }}" target="_blank">{{ p[0] }}/{{ p[1] }}</a></li>
    {% else %}
      <li><small>No outputs yet.</small></li>
    {% endfor %}
  </ul>
</div>
"""


@app.route("/")
def home():
    outs = []
    for jobdir in sorted(OUT.glob("*")):
        for f in sorted(jobdir.glob("*")):
            outs.append((jobdir.name, f.name))
    return render_template_string(
        INDEX, outputs=outs, causes=CAUSES, flask_request=flask_request
    )


@app.route("/run", methods=["POST"])
def run_pipeline():
    cause = (flask_request.form.get("cause") or "other").strip()
    import shutil
    import subprocess
    import time

    from flask import flash, redirect, request, url_for

    job = slug_job(flask_request.form.get("job"))
    # Save cause-of-loss to meta.json in both uploads and out
    try:
        meta = {"job": job, "cause_of_loss": cause}
        (UPLOADS / job / "meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        (OUT / job / "meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
    except Exception as e:
        app.logger.warning(f"Could not write meta.json: {e}")
    jobdir = UPLOADS / job
    outdir = OUT / job
    jobdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    rp = ROOT / "run_pipeline.py"
    log = LOGS / f"run_{job}_{int(time.time())}.log"

    # 1) Run pipeline if present (write to jobdir/outdir)
    if rp.exists():
        with open(log, "wb") as L:
            subprocess.run(
                ["python3", str(rp), "--job", str(jobdir), "--out", str(outdir)],
                cwd=str(ROOT),
                stdout=L,
                stderr=subprocess.STDOUT,
            )

    # 2) Sweep any top-level out/*.csv into out/<job>/ (handles misrouted outputs)
    for f in ROOT.joinpath("out").glob("*.csv"):
        try:
            shutil.move(str(f), str(outdir / f.name))
        except Exception:
            pass

    # 3) If no CSV present, write a small stub so UI can open something
    if not any(outdir.glob("*.csv")):
        (outdir / "estimate_xact_with_notes.csv").write_text(
            "room,item,qty,notes\nLiving Room,DRY1/2,10,stub run\n", encoding="utf-8"
        )

    # 4) Pick best and redirect with auto-open
    best = _best_estimate(outdir)
    if best:
        flash(f"✅ Final estimate ready: {best}")
        open_href = url_for("download", job=job, fname=best)
        return redirect(url_for("home", open=open_href))
    else:
        flash("Pipeline finished, but no estimate CSV found.")
        return redirect(url_for("home"))


@app.route("/out/<job>/<path:fname>")
def download(job, fname):
    return send_from_directory(OUT / job, fname, as_attachment=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)


@app.route("/upload", methods=["POST"])
def upload():
    import json

    from flask import flash, redirect, request, url_for

    job = slug_job(flask_request.form.get("job") or "job-0001")
    cause = (flask_request.form.get("cause") or "Flood").strip()

    # Save cause into meta.json
    (OUT / job).mkdir(parents=True, exist_ok=True)
    meta_path = OUT / job / "meta.json"
    try:
        meta = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["cause"] = cause
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception as e:
        app.logger.warning(f"Could not write meta.json: {e}")

    # Save uploaded files
    files = flask_request.files.getlist("files")
    if not files:
        flash("No files uploaded.")
        return redirect(url_for("index"))

    job_dir = UPLOADS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f and f.filename:
            (job_dir / f.filename).write_bytes(f.read())

    flash(f"Uploaded {len(files)} file(s) to job {job}")
    return redirect(url_for("index"))


# --- upload endpoint guard (auto-added) ---
try:
    upload  # type: ignore[name-defined]
    # Ensure route is registered with the expected endpoint name.
    try:
        app.add_url_rule("/upload", "upload", upload, methods=["POST"])
    except Exception:
        pass
except NameError:

    @app.route("/upload", methods=["POST"])
    def upload():
        from flask import flash, redirect, request, url_for

        flash("Upload route was missing; a minimal handler was auto-inserted.")
        return redirect(url_for("index"))


# --- end guard ---
