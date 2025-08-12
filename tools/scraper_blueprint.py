from __future__ import annotations

import hashlib
import os
import random
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from flask import (Blueprint, flash, redirect, render_template_string, request,
                   url_for)
from PIL import Image

# DDG search (new package)
try:
    from ddgs import DDGS
except Exception:
    DDGS = None

scraperbp = Blueprint("scraperbp", __name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
INBOX = REPO_ROOT / "data" / "label_inbox"
CAUSE_PATH = REPO_ROOT / "data" / "current_cause.txt"
INBOX.mkdir(parents=True, exist_ok=True)

# Keep peril list aligned with your app
CLAIM_CAUSES = [
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

UA_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]


def set_current_cause(cause: str):
    cause = (cause or "other").strip().lower().replace(" ", "_")
    if cause not in CLAIM_CAUSES:
        cause = "other"
    CAUSE_PATH.write_text(cause, encoding="utf-8")
    return cause


def _headers() -> Dict[str, str]:
    import random

    return {
        "User-Agent": random.choice(UA_LIST),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _name_from_url(url: str, prefix: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{h}.jpg"


def _download_and_save(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=_headers(), timeout=15, stream=True)
        r.raise_for_status()
        data = r.content
        if len(data) < 12_000:  # skip tiny thumbs
            return False
        im = Image.open(BytesIO(data))
        im.verify()
        im = Image.open(BytesIO(data)).convert("RGB")
        im.save(dest, "JPEG", quality=90)
        return True
    except Exception:
        return False


def ddg_images(query: str, max_results: int) -> List[str]:
    """Return list of image URLs from DDG."""
    urls = []
    if DDGS is None:
        return urls
    with DDGS() as ddgs:
        for res in ddgs.images(query, max_results=max_results):
            url = res.get("image") or res.get("url") or res.get("thumbnail")
            if url:
                urls.append(url)
            time.sleep(0.05)  # be gentle
    return urls


TEMPLATE = """
<!doctype html>
<title>Scrape Images</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui,Arial,sans-serif;max-width:880px;margin:22px auto;padding:0 12px}
.card{background:#fff;border:1px solid #eee;border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,.06);padding:16px}
input,select,button{font-size:16px;padding:8px 10px;border-radius:10px;border:1px solid #bbb}
button{cursor:pointer;background:#f7f7f7}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media (max-width:880px){.row{grid-template-columns:1fr}}
small{color:#666}
</style>
<div class="card">
  <h2>Scrape images (DuckDuckGo)</h2>
  <form method="post">
    <div class="row">
      <label>Peril / Claim Cause<br>
        <select name="cause">
          {% for c in causes %}
            <option value="{{c}}" {% if c==current_cause %}selected{% endif %}>{{c}}</option>
          {% endfor %}
        </select>
      </label>
      <label>How many images?<br>
        <input type="number" name="count" min="5" max="200" value="50">
      </label>
      <label>Search phrase<br>
        <input type="text" name="query" value="{{ default_q }}" placeholder="e.g. hurricane roof damage shingles">
      </label>
      <label title="If checked, the upload/labeling batch cause is set to this peril for new labels">
        <input type="checkbox" name="set_cause" value="1" checked> Set as current claim cause
      </label>
    </div>
    <br>
    <button type="submit">Start scraping</button>
    <a href="{{ url_for('next_image') }}" style="margin-left:12px">Back to Labeler</a>
    <p><small>Images save to <code>data/label_inbox/</code> as JPG. You can label them immediately.</small></p>
  </form>

  {% if started %}
    <hr>
    <p><b>Scraping '{{ query }}' ...</b></p>
    <p>Saved: {{ saved }} / Errors: {{ errors }}</p>
    <p><a href="{{ url_for('next_image') }}">Open Labeler</a></p>
  {% endif %}
</div>
"""


@scraperbp.route("/scrape", methods=["GET", "POST"])
def scrape_ui():
    started = False
    saved = errors = 0
    current_cause = (
        CAUSE_PATH.read_text(encoding="utf-8").strip()
        if CAUSE_PATH.exists()
        else "other"
    )

    if request.method == "POST":
        cause = (request.form.get("cause") or "other").strip().lower()
        count = max(5, min(200, int(request.form.get("count") or 50)))
        query = (
            request.form.get("query") or ""
        ).strip() or f"{cause} damage insurance claim"
        if request.form.get("set_cause") == "1":
            current_cause = set_current_cause(cause)
        else:
            # still normalize display if user typed weird casing
            current_cause = cause if cause in CLAIM_CAUSES else "other"

        # fetch URLs (overfetch to offset failures)
        urls = ddg_images(query, max_results=count * 3)
        random.shuffle(urls)
        started = True

        seen = set()
        for url in urls:
            if saved >= count:
                break
            if url in seen:
                continue
            seen.add(url)
            name = _name_from_url(url, prefix=cause)
            dest = INBOX / name
            if dest.exists():
                continue
            if _download_and_save(url, dest):
                saved += 1
                time.sleep(random.uniform(0.6, 1.4))  # polite
            else:
                errors += 1
                if errors > 40:
                    break  # bail if too many failures

        return render_template_string(
            TEMPLATE,
            causes=CLAIM_CAUSES,
            current_cause=current_cause,
            default_q=f"{cause} damage insurance claim",
            started=True,
            saved=saved,
            errors=errors,
            query=query,
        )

    # GET
    return render_template_string(
        TEMPLATE,
        causes=CLAIM_CAUSES,
        current_cause=current_cause,
        default_q="mold damage insurance claim",
        started=False,
        saved=saved,
        errors=errors,
        query="",
    )
