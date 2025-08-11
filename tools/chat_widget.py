from __future__ import annotations
import os, json, textwrap, time
from typing import List, Dict, Any
from flask import Blueprint, request, jsonify, Response

# --- Optional OpenAI (Responses API) ---
OPENAI_OK = False
try:
    from openai import OpenAI
    _client = OpenAI()
    OPENAI_OK = bool(os.getenv("OPENAI_API_KEY"))
except Exception:
    _client = None
    OPENAI_OK = False

# --- DuckDuckGo search via ddgs (no API key) ---
SEARCH_OK = False
try:
    from ddgs import DDGS
    SEARCH_OK = True
except Exception:
    DDGS = None
    SEARCH_OK = False

chatbp = Blueprint("chatbp", __name__)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIME_BUDGET_MS = 2500
MAX_RESULTS = 3

def web_search(query: str, max_results: int = MAX_RESULTS) -> List[Dict[str, Any]]:
    if not SEARCH_OK:
        return []
    results: List[Dict[str, Any]] = []
    start = time.time()
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body"),
            })
            # time-box the loop
            if (time.time() - start) * 1000 > TIME_BUDGET_MS:
                break
    return results

def render_search_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No web results."
    lines = ["Web search results:"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title') or '(no title)'}\nURL: {r.get('url') or ''}\n{r.get('snippet') or ''}")
    out = "\n\n".join(lines)
    return out[:2000]

def call_llm(prompt: str) -> str:
    if OPENAI_OK and _client:
        resp = _client.responses.create(model=DEFAULT_MODEL, input=prompt)
        try:
            return (resp.output_text or "").strip()
        except Exception:
            return json.dumps(resp.model_dump(), indent=2)[:3000]
    return "AI offline (no OPENAI_API_KEY). Prompt echo:\n\n" + textwrap.shorten(prompt, 1500)

@chatbp.route("/chat", methods=["POST"])
def chat_api():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    use_web = bool(data.get("web"))
    if not msg:
        return jsonify({"error": "message required"}), 400
    search_results = web_search(msg) if use_web else []
    prefix = render_search_context(search_results) + "\n\nTask: Using the above when relevant, answer succinctly.\n\n" if use_web else ""
    reply = call_llm(prefix + msg)
    out = {"reply": reply, "used_web": use_web}
    if search_results:
        out["sources"] = search_results
    return jsonify(out)

@chatbp.route("/chat-ui")
def chat_ui():
    html = """
<!doctype html>
<title>Claim AI – Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body{font-family:system-ui,Arial,sans-serif;margin:0;background:#fafafa}
  .wrap{max-width:840px;margin:20px auto;padding:12px}
  .card{background:#fff;border:1px solid #eee;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.05);padding:16px}
  textarea,input,button,label{font-size:16px}
  textarea{width:100%;height:110px;padding:10px;border:1px solid #ccc;border-radius:12px}
  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px}
  button{padding:10px 14px;border-radius:12px;border:1px solid #bbb;background:#f5f5f5;cursor:pointer}
  .out{white-space:pre-wrap;background:#fcfcfc;border:1px solid #eee;border-radius:12px;padding:12px;margin-top:12px}
  .srcs{font-size:13px;color:#444;margin-top:6px}
  .srcs a{color:#0645ad;text-decoration:none}
</style>
<div class="wrap">
  <div class="card">
    <h2 style="margin:0 0 10px">Claim AI – Chat</h2>
    <textarea id="msg" placeholder="Ask about perils, building codes, materials, etc."></textarea>
    <div class="row">
      <label><input type="checkbox" id="web"> Use web search (slower)</label>
      <button id="send">Send</button>
    </div>
    <div id="reply" class="out" style="display:none"></div>
    <div id="sources" class="srcs"></div>
  </div>
</div>
<script>
async function send() {
  const msg = document.getElementById('msg').value.trim();
  const web = document.getElementById('web').checked;
  if (!msg) return;
  const replyEl = document.getElementById('reply');
  const srcEl = document.getElementById('sources');
  replyEl.style.display='block';
  replyEl.textContent='Thinking...';
  srcEl.innerHTML='';
  const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg, web})});
  const data = await res.json();
  replyEl.textContent = data.reply || data.error || 'No reply';
  if (data.sources) {
    srcEl.innerHTML = '<b>Sources:</b> ' + data.sources.map(s => '<div>• <a href="'+(s.url||'#')+'" target="_blank">'+(s.title||s.url||'source')+'</a></div>').join('');
  }
}
document.getElementById('send').addEventListener('click', send);
</script>
"""
    return Response(html, mimetype="text/html")
