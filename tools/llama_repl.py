import requests, json
URL="http://127.0.0.1:11434/api/chat"; MODEL="llama3"
history=[{"role":"system","content":"You are a concise helper."}]
def ask(msg):
    history.append({"role":"user","content":msg})
    r=requests.post(URL,json={"model":MODEL,"messages":history,"stream":False},timeout=120)
    r.raise_for_status(); reply=r.json()["message"]["content"]
    history.append({"role":"assistant","content":reply}); return reply
print("✅ LLaMA REPL. Type 'exit' to quit.")
while True:
    try:
        u=input("You: ").strip()
        if not u: continue
        if u.lower() in ("exit","quit"): print("Bye!"); break
        print("Bot:", ask(u))
    except Exception as e:
        print("ERR:", e)
