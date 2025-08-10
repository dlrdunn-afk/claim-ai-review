from flask import Flask, request, render_template_string
from pathlib import Path
import subprocess

app = Flask(__name__)
APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>CLAIM-AI — Upload Claim</title>
  <style>
    body { font:16px/1.5 -apple-system, BlinkMacSystemFont, Roboto, sans-serif; margin:36px; }
    label { display:block; margin-top:14px; font-weight:600; }
    input[type=text]{ padding:8px; width:260px; }
    input[type=file]{ margin-top:6px; }
    button { margin-top:18px; padding:10px 16px; cursor:pointer; }
    .muted { color:#666; }
    pre { background:#0b1022; color:#e9f1ff; padding:14px; border-radius:8px; overflow:auto; max-height:60vh; }
    a { text-decoration:none; }
  </style>
</head>
<body>
  <h1>Upload Claim</h1>
  <form method="post" enctype="multipart/form-data">
    <label>Job ID</label>
    <input type="text" name="job_id" placeholder="job-0005" required />

    <label>Policy (PDF)</label>
    <input type="file" name="policy" accept=".pdf,application/pdf" />

    <label>iGUIDE Floorplan (JPG/PNG)</label>
    <input type="file" name="floorplan" accept=".jpg,.jpeg,.png,image/jpeg,image/png" />

    <label>iGUIDE XML</label>
    <input type="file" name="xml" accept=".xml,text/xml" />

    <label>Damage Photos (multiple)</label>
    <input type="file" name="photos" accept=".jpg,.jpeg,.png,image/jpeg,image/png" multiple />

    <button type="submit">Upload & Process</button>
  </form>

  <p class="muted">Files will be saved to <code>data/&lt;job_id&gt;/</code>. After upload, the pipeline runs automatically.</p>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        job_id = (request.form.get("job_id") or "").strip()
        if not job_id:
            return "Job ID is required.", 400

        base = DATA_DIR / job_id
        ig_dir = base / "iguide"
        photos_dir = base / "photos"
        base.mkdir(parents=True, exist_ok=True)
        ig_dir.mkdir(parents=True, exist_ok=True)
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files
        policy = request.files.get("policy")
        floorplan = request.files.get("floorplan")
        xml = request.files.get("xml")
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

        # Auto-run pipeline
        try:
            result = subprocess.run(
                ["python3", str(APP_ROOT / "run_pipeline.py"), job_id],
                capture_output=True,
                text=True,
                check=False
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
        except Exception as e:
            stdout, stderr = "", f"Error running pipeline: {e}"

        return f"""
        <h2>✅ Claim {job_id} uploaded & processed</h2>
        <p>Outputs should be in <code>out/</code> and job data in <code>data/{job_id}/</code>.</p>
        <h3>Pipeline Output</h3>
        <pre>{stdout}</pre>
        {f"<h3 style='color:#b00;'>Errors</h3><pre style='background:#2a0d0d;color:#ffd6d6;'>{stderr}</pre>" if stderr.strip() else ""}
        <p><a href="/">⬅ Back to upload</a></p>
        """

    return render_template_string(HTML)

if __name__ == "__main__":
    print("🚀 Uploader running at http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
