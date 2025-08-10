#!/usr/bin/env python3
import requests, subprocess, os, time, json, textwrap
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = APP_ROOT / "data"
MEM_DIR  = APP_ROOT / "memory"; MEM_DIR.mkdir(exist_ok=True)
MEM_FILE = MEM_DIR / "assistant_memory.jsonl"

URL   = os.environ.get("OLLAMA_CHAT_URL","http://127.0.0.1:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL","llama3")

SYSTEM = ("You are a local terminal assistant for the CLAIM-AI project. "
          "You help run pipelines, inspect files, and explain steps clearly.")

def mem_write(role, content):
    with MEM_FILE.open("a") as f: f.write(json.dumps({"ts":time.time(),"role":role,"content":content})+"\n")

def list_jobs():
    if not DATA_DIR.exists(): return []
    return sorted([p.name for p in DATA_DIR.iterdir() if p.is_dir()])

def ask(messages):
    r=requests.post(URL,json={"model":MODEL,"messages":messages,"stream":False},timeout=120)
    r.raise_for_status()
    return r.json().get("message",{}).get("content","").strip()

def run_pipeline(job_id):
    steps = [
        f"python3 {APP_ROOT/'iguide/export_room_data.py'} {job_id}",
        f"python3 {APP_ROOT/'estimate/generate_room_estimates.py'} {job_id}",
        f"python3 {APP_ROOT/'estimate/add_justifications.py'} {job_id}",
        f"python3 {APP_ROOT/'estimate/merge_room_and_estimate.py'} {job_id}",
        f"python3 {APP_ROOT/'estimate/apply_policy_rules.py'} {job_id}",
        f"python3 {APP_ROOT/'estimate/export_xactimate_csv.py'} {job_id}",
    ]
    print(f"\n=== Running pipeline for {job_id} ===")
    out_all=[]
    for cmd in steps:
        print("->", cmd)
        p=subprocess.run(cmd,shell=True,capture_output=True,text=True)
        if p.stdout: print(p.stdout)
        if p.returncode!=0:
            if p.stderr: print(p.stderr)
            print("⛔ Step failed:", cmd); break
        out_all.append(p.stdout or "")
    mem_write("system", f"Pipeline {job_id} complete/failed. Logs:\n{''.join(out_all)[:5000]}")
    print("=== Done ===\n")

def show_path(path):
    p = (APP_ROOT / path).resolve() if not path.startswith("/") else Path(path)
    if not p.exists(): print("❌ Not found:", p); return
    if p.is_dir():
        print("📁", p)
        for c in sorted(p.iterdir()):
            print(" -", c.name + ("/" if c.is_dir() else ""))
        return
    try:
        txt=p.read_text(errors="ignore")
        lines=txt.splitlines()
        print(f"--- {p} (showing {min(len(lines),300)} of {len(lines)}) ---")
        print("\n".join(lines[:300]))
        if len(lines)>300: print("\n... (truncated)")
    except Exception as e:
        print("⚠️ cannot display file:", e)

def help_text():
    return textwrap.dedent("""\
    Commands:
      /help                Show help
      /jobs                List job folders under data/
      /run <job-id>        Run pipeline for a job (e.g., /run job-0001)
      /show <path>         Show a file or folder (e.g., /show out/estimate_xact_import.csv)
      /clear               Clear chat memory
      /exit                Quit
    Type anything else to chat with the model.
    """)

def main():
    print("CLAIM-AI Terminal Assistant (LLaMA 3 via Ollama)")
    print(help_text())
    history=[{"role":"system","content":SYSTEM}]
    while True:
        try:
            u=input("🧑‍💻 You: ").strip()
        except (EOFError,KeyboardInterrupt):
            print("\n👋 Bye."); break
        if not u: continue
        if u == "/exit": print("👋 Bye."); break
        if u == "/help": print(help_text()); continue
        if u == "/clear":
            open(MEM_FILE,"w").close() if MEM_FILE.exists() else None
            history=[{"role":"system","content":SYSTEM}]
            print("✅ Cleared memory."); continue
        if u == "/jobs":
            js=list_jobs()
            print("📂 Jobs:\n " + ("\n ".join(f"- {j}" for j in js) if js else "(none)"))
            continue
        if u.startswith("/run "):
            run_pipeline(u.split(None,1)[1]); continue
        if u.startswith("/show "):
            show_path(u.split(None,1)[1]); continue

        # normal chat
        try:
            history.append({"role":"user","content":u})
            mem_write("user", u)
            reply=ask(history)
            print("🤖 Bot:", reply)
            history.append({"role":"assistant","content":reply})
            mem_write("assistant", reply)
        except Exception as e:
            print("❌ Chat error:", e)

if __name__=="__main__":
    main()
