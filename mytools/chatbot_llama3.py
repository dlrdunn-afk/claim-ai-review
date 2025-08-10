from flask import Flask, request, render_template
from pathlib import Path
import subprocess

app = Flask(__name__)

# Paths
APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_claim", methods=["GET", "POST"])
def new_claim():
    if request.method == "POST":
        job_id = (request.form.get("job_id") or "").strip()
        if not job_id:
            return "Job ID required", 400

        base = DATA_DIR / job_id
        ig_dir = base / "iguide"
        photos_dir = base / "photos"
        base.mkdir(parents=True, exist_ok=True)
        ig_dir.mkdir(parents=True, exist_ok=True)
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Single-file fields
        policy = request.files.get("policy")
        floorplan = request.files.get("floorplan")
        xml = request.files.get("xml")
        # Multi-file field
        photos = request.files.getlist("photos")

        if policy and policy.filename:
            (base / "policy.pdf").write_bytes(policy.read())
        if floorplan and floorplan.filename:
            (ig_dir / floorplan.filename).write_bytes(floorplan.read())
        if xml and xml.filename:
            (ig_dir / xml.filename).write_bytes(xml.read())
        for p in photos:
            if p and p.filename:
                (photos_dir / p.filename).write_bytes(p.read())

        # --- Auto run pipeline ---
        try:
            result = subprocess.run(
                ["python3", str(APP_ROOT / "run_pipeline.py"), job_id],
                capture_output=True,
                text=True,
                check=False
            )
            output_html = f"<pre>{result.stdout}</pre>"
            if result.stderr:
                output_html += f"<pre style='color:red;'>{result.stderr}</pre>"
        except Exception as e:
            output_html = f"<p style='color:red;'>Error running pipeline: {e}</p>"

        return f"""
        <h3 class='ok'>✅ Claim {job_id} uploaded & processed!</h3>
        <div>{output_html}</div>
        <p><a href="/">Back to Home</a></p>
        """

    return render_template("new_claim.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)

