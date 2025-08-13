import subprocess
import sys
from pathlib import Path

from flask import Blueprint, current_app as app, jsonify, request

# Removed unused import
# from tools.chat_blueprint import chat_bp

claim_bp = Blueprint('claim', __name__)

@claim_bp.route('/new_claim', methods=['POST'])
def new_claim():
    """
    Handle new claim creation by running the generate_room_name_form.py script
    for the specified job directory.
    """
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "iguide" / "generate_room_name_form.py"
    job_rel = request.form.get("job", "data/job-0001")
    job_dir = (project_root / job_rel).resolve()

    # Prevent directory traversal: job_dir must be inside project_root / "data"
    data_dir = (project_root / "data").resolve()
    if not str(job_dir).startswith(str(data_dir)):
        return "Invalid job directory.", 400

    if not script_path.exists():
        return f"Script not found: {script_path}", 404
    if not job_dir.exists():
        return f"Job folder not found: {job_dir}", 400

    cmd = [
        sys.executable,
        str(script_path),
        "--job",
        str(job_dir),
        "--mode",
        "form",
    ]

    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)

    if result.returncode != 0:
        app.logger.error(
            "generate_room_name_form failed:\nSTDOUT:\n%s\nSTDERR:\n%s",
            result.stdout,
            result.stderr,
        )
        return (
            f"Form generation failed (exit {result.returncode}).\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        ), 500

    return jsonify(
        {"status": "ok", "job": str(job_dir), "stdout": result.stdout.strip()}
    )    import subprocess
    import sys
    from pathlib import Path
    
    from flask import Blueprint, current_app as app, jsonify, request
    
    # Removed unused import
    # from tools.chat_blueprint import chat_bp
    
    claim_bp = Blueprint('claim', __name__)
    
    @claim_bp.route('/new_claim', methods=['POST'])
    def new_claim():
        """
        Handle new claim creation by running the generate_room_name_form.py script
        for the specified job directory.
        """
        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "iguide" / "generate_room_name_form.py"
        job_rel = request.form.get("job", "data/job-0001")
        job_dir = (project_root / job_rel).resolve()
    
        # Prevent directory traversal: job_dir must be inside project_root / "data"
        data_dir = (project_root / "data").resolve()
        if not str(job_dir).startswith(str(data_dir)):
            return "Invalid job directory.", 400
    
        if not script_path.exists():
            return f"Script not found: {script_path}", 404
        if not job_dir.exists():
            return f"Job folder not found: {job_dir}", 400
    
        cmd = [
            sys.executable,
            str(script_path),
            "--job",
            str(job_dir),
            "--mode",
            "form",
        ]
    
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)
    
        if result.returncode != 0:
            app.logger.error(
                "generate_room_name_form failed:\nSTDOUT:\n%s\nSTDERR:\n%s",
                result.stdout,
                result.stderr,
            )
            return (
                f"Form generation failed (exit {result.returncode}).\n"
                f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            ), 500
    
        return jsonify(
            {"status": "ok", "job": str(job_dir), "stdout": result.stdout.strip()}
        )import subprocess
import sys
from pathlib import Path

from flask import current_app as app
from flask import jsonify, request

from tools.chat_blueprint import chat_bp


def new_claim():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "iguide" / "generate_room_name_form.py"
    job_rel = request.form.get("job", "data/job-0001")
    job_dir = (project_root / job_rel).resolve()

    if not script_path.exists():
        return f"Script not found: {script_path}", 500
    if not job_dir.exists():
        return f"Job folder not found: {job_dir}", 400

    cmd = [
        sys.executable,
        str(script_path),
        "--job",
        str(job_dir),
        "--mode",
        "form",  # remove if your script doesn’t support this
    ]

    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True)

    if result.returncode != 0:
        app.logger.error(
            "generate_room_name_form failed:\nSTDOUT:\n%s\nSTDERR:\n%s",
            result.stdout,
            result.stderr,
        )
        return (
            f"Form generation failed (exit {result.returncode}).\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        ), 500

    return jsonify(
        {"status": "ok", "job": str(job_dir), "stdout": result.stdout.strip()}
    )
