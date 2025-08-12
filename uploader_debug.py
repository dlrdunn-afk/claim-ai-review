from flask import Flask, request, render_template_string, jsonify
import os

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Upload test</title>
<h1>Upload a file</h1>
<form action="{{ url_for('upload') }}" method="post" enctype="multipart/form-data">
  <input type="file" name="files" multiple>
  <button type="submit">Upload</button>
</form>
<p>See <a href="{{ url_for('routes') }}">/routes</a> to verify registered endpoints.</p>
"""

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/upload")
def upload():
    if 'files' not in request.files:
        return "No file part", 400
    files = request.files.getlist('files')
    os.makedirs("out", exist_ok=True)
    saved = []
    for f in files:
        if not f or f.filename == '':
            continue
        path = os.path.join("out", f.filename)
        f.save(path)
        saved.append(path)
    if not saved:
        return "No files selected", 400
    return "Saved:\\n" + "\\n".join(saved) + "\\n", 200

@app.get("/routes")
def routes():
    data = []
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
        data.append({"rule": str(rule), "endpoint": rule.endpoint, "methods": methods})
    return jsonify(data)

if __name__ == "__main__":
    print("== Route map at startup ==")
    print(app.url_map)
    app.run(host="127.0.0.1", port=5002, debug=True)
