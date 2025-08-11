from __future__ import annotations
import os, time, hashlib, random, sys
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO

# DuckDuckGo (new package)
from ddgs import DDGS

SEARCH_TERM = "mold damage insurance claim"
NUM_IMAGES = 50
OUT_DIR = Path("data/label_inbox")
TIMEOUT = 15
MAX_ERRORS = 25
SLEEP_MIN, SLEEP_MAX = 0.6, 1.4  # polite throttling between downloads

UA_LIST = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def rand_headers():
    return {"User-Agent": random.choice(UA_LIST), "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}

def choose_ext(ct: str, url_path: str) -> str:
    if ct.startswith("image/jpeg"): return ".jpg"
    if ct.startswith("image/png"): return ".png"
    if ct.startswith("image/webp"): return ".webp"
    # fallback from URL path
    ext = os.path.splitext(url_path)[1].lower()
    return ext if ext in {".jpg",".jpeg",".png",".webp"} else ".jpg"

def dedupe_name(url: str, ext: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"mold_{h}{ext}"

def fetch_bytes(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=rand_headers(), timeout=TIMEOUT, stream=True)
        r.raise_for_status()
        # only keep small-ish files in memory
        content = r.content
        if len(content) < 10_000:  # skip tiny thumbs
            return None
        return content
    except Exception:
        return None

def verify_and_save(img_bytes: bytes, dest: Path) -> bool:
    try:
        im = Image.open(BytesIO(img_bytes))
        im.verify()  # quick check
        # re-open to save
        im = Image.open(BytesIO(img_bytes)).convert("RGB")
        # normalize to JPG to keep simple in labeler
        dest = dest.with_suffix(".jpg")
        im.save(dest, "JPEG", quality=90)
        return True
    except Exception:
        return False

def search_ddg(q: str, n: int) -> list[dict]:
    # use generator + brief sleep to avoid rate-limits
    out = []
    with DDGS() as ddgs:
        for i, res in enumerate(ddgs.images(q, max_results=n), 1):
            out.append(res)
            time.sleep(0.05)  # gentle
    return out

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else SEARCH_TERM
    target = int(sys.argv[2]) if len(sys.argv) > 2 else NUM_IMAGES
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🔎 Searching DuckDuckGo for '{query}' (target {target}) ...")
    results = search_ddg(query, target * 3)  # overfetch to account for failures
    print(f"🧾 Got {len(results)} result entries, starting downloads...")

    ok = 0
    errors = 0
    seen = set()
    for r in results:
        if ok >= target or errors >= MAX_ERRORS: break
        url = r.get("image") or r.get("url") or r.get("thumbnail")
        if not url or url in seen: 
            continue
        seen.add(url)

        # pick filename
        url_path = urlparse(url).path
        ext = choose_ext(r.get("source") or "", url_path)
        fname = dedupe_name(url, ext)
        dest = OUT_DIR / fname
        if dest.exists():
            continue

        # download and validate
        data = fetch_bytes(url)
        if not data:
            errors += 1
            continue
        if not verify_and_save(data, dest):
            errors += 1
            continue

        ok += 1
        print(f"✅ [{ok}/{target}] {dest.name}")
        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))  # be polite

    print(f"\n🎯 Done. Saved {ok} images to {OUT_DIR} (errors: {errors}).")

if __name__ == "__main__":
    main()
