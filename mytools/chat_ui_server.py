#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

APP_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = APP_ROOT / "templates"
MEM_FILE = APP_ROOT / "memory" / "chat_memory.jsonl"
(MEM_FILE.parent).mkdir(exist_ok=True)

OLLAMA_URL = os.environ.get("OLLAMA_CHAT_URL", "http://127.0.0.1:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = (
    "You are a helpful project assistant for the CLAIM-AI tool. "
    "Answer concisely. You can explain the pipeline, files, and next steps."
)

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))
CHAT_HISTORY = [{"role": "system", "content": SYSTEM_PROMPT}]


def save_mem(role, content):
    with open(MEM_FILE, "a") as f:
        f.write(
            json.dumps({"ts": time.time(), "role": role, "content": content}) + "\n"
        )


@app.route("/chat")
def chat_page():
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400

    CHAT_HISTORY.append({"role": "user", "content": message})
    save_mem("user", message)

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "messages": CHAT_HISTORY, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        reply = (r.json().get("message") or {}).get(
            "content", ""
        ).strip() or "(no response)"
    except Exception as e:
        reply = f"Error talking to Ollama: {e}"

    CHAT_HISTORY.append({"role": "assistant", "content": reply})
    save_mem("assistant", reply)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    # Runs on http://127.0.0.1:5003/chat
    app.run(host="127.0.0.1", port=5003, debug=False)
