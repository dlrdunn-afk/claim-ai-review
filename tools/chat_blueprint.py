import requests
from duckduckgo_search import DDGS
from flask import Blueprint, jsonify, render_template_string, request

chat_bp = Blueprint("chat_bp", __name__)

HTML = """
<!doctype html><title>AI Chat</title>
<h2>AI Chat with Web Search</h2>
<form method=post>
<textarea name=msg rows=4 cols=60>{{msg}}</textarea><br>
<input type=submit value="Send">
</form>
{% if resp %}<pre>{{resp}}</pre>{% endif %}
"""


def ai_reply(prompt):
    if "search:" in prompt.lower():
        q = prompt.split("search:", 1)[1].strip()
        results = list(DDGS().text(q, max_results=3))
        return "\n".join(f"{r['title']} – {r['href']}" for r in results)
    return f"[Local AI Stub Reply] You said: {prompt}"


@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
    msg = ""
    resp = ""
    if request.method == "POST":
        msg = request.form.get("msg", "")
        resp = ai_reply(msg)
    return render_template_string(HTML, msg=msg, resp=resp)
