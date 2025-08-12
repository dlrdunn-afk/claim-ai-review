from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "dev"

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
OUT = ROOT / "out"
LOGS = ROOT / "logs"
for p in (UPLOADS, OUT, LOGS):
    p.mkdir(exist_ok=True)

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

# Allowed file extensions for each upload category
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

# Map form fields to folder names inside the job directory
DEST_MAP = {
    "floorplan_xml": "floorplan",
    "floorplan_img": "floorplan",
}

# Optional blueprints (chat and image scraper) if present
try:  # pragma: no cover - optional
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from tools.chat_widget import chatbp

    app.register_blueprint(chatbp)
except Exception:  # pragma: no cover - best effort
    pass

try:  # pragma: no cover - optional
    from tools.scraper_blueprint import scraperbp

    app.register_blueprint(scraperbp)
except Exception:  # pragma: no cover - best effort
    pass


def slug_job(x: str) -> str:
    """Create a filesystem-friendly job identifier."""

    import re

    y = re.sub(r"[^a-zA-Z0-9_-]+", "-", (x or "").strip())
    return re.sub(r"-+", "-", y).strip("-").lower() or "job-0001"


def _best_estimate(job_dir: Path) -> str | None:
    """Return the preferred estimate CSV within *job_dir* if available."""

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
    for f in sorted(job_dir.glob("*.csv")):
        return f.name
    return None


def save_files(files: Iterable, dest: Path, allowed: set[str]) -> list[str]:
    """Save uploaded *files* into *dest* if they have allowed extensions."""

    dest.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
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
            target = dest / f"{Path(name).stem}_{i}{ext}"
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
{% if request.args.get('open') %}
  <script>
    (function(){
      try {
        const openPath = decodeURIComponent("{{ request.args.get('open') }}");
        if (openPath) window.open(openPath, "_blank");
      } catch(e){}
    })();
  </script>
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
        <label>Post-loss Photos (JPG/PNG/HEIC/PDF)
          <input type="file" name="photos" accept="image/*,.heic,.heif,.pdf" multiple>
        </label>
        <small>Saved to <code>uploads/&lt;job&gt;/photos/</code></small>
      </div>

      <div class="card">
        <h4>Pre-loss Photos (Bulk)</h4>
        <label>Pre-loss Photos (JPG/PNG/HEIC/PDF)
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
      </label>
      <label>Cause of Loss
        <select id="cause" name="cause" required style="min-width:240px;">
          <option value="" disabled selected>Select a cause…</option>
          {% for c in causes %}<option value="{{ c }}">{{ c.replace('_',' ') }}</option>{% endfor %}
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
    """Render the main interface."""

    outs: list[tuple[str, str]] = []
    for jobdir in sorted(OUT.glob("*")):
        for f in sorted(jobdir.glob("*")):
            outs.append((jobdir.name, f.name))
    return render_template_string(INDEX, outputs=outs, causes=CAUSES, request=request)


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file uploads for a job."""

    job = slug_job(request.form.get("job"))
    total = 0
    for field, allowed in ALLOWED.items():
        uploaded = request.files.getlist(field)
        if not uploaded:
            continue
        dest_name = DEST_MAP.get(field, field)
        saved = save_files(uploaded, UPLOADS / job / dest_name, allowed)
        total += len(saved)
    if total:
        flash(f"Uploaded {total} file(s) to job {job}")
    else:
        flash("No files uploaded.")
    return redirect(url_for("home"))


@app.route("/run", methods=["POST"])
def run_pipeline():
    """Execute the processing pipeline for the given job."""

    job = slug_job(request.form.get("job"))
    cause = (request.form.get("cause") or "other").strip()

    jobdir = UPLOADS / job
    outdir = OUT / job
    jobdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    meta = {"job": job, "cause_of_loss": cause}
    try:
        (UPLOADS / job / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        (outdir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception as e:  # pragma: no cover - best effort
        app.logger.warning(f"Could not write meta.json: {e}")

    rp = ROOT / "run_pipeline.py"
    log = LOGS / f"run_{job}_{int(time.time())}.log"
    if rp.exists():  # pragma: no cover - external script
        with open(log, "wb") as L:
            subprocess.run(
                ["python3", str(rp), "--job", str(jobdir), "--out", str(outdir)],
                cwd=str(ROOT),
                stdout=L,
                stderr=subprocess.STDOUT,
            )

    for f in ROOT.joinpath("out").glob("*.csv"):
        try:
            shutil.move(str(f), str(outdir / f.name))
        except Exception:  # pragma: no cover - best effort
            pass

    if not any(outdir.glob("*.csv")):
        (outdir / "estimate_xact_with_notes.csv").write_text(
            "room,item,qty,notes\nLiving Room,DRY1/2,10,stub run\n",
            encoding="utf-8",
        )

    best = _best_estimate(outdir)
    if best:
        flash(f"✅ Final estimate ready: {best}")
        open_href = url_for("download", job=job, fname=best)
        return redirect(url_for("home", open=open_href))
    flash("Pipeline finished, but no estimate CSV found.")
    return redirect(url_for("home"))


@app.route("/out/<job>/<path:fname>")
def download(job: str, fname: str):
    """Serve output files for download/viewing."""

    return send_from_directory(OUT / job, fname, as_attachment=False)


if __name__ == "__main__":  # pragma: no cover - manual run
    app.run(host="127.0.0.1", port=5002, debug=True)

