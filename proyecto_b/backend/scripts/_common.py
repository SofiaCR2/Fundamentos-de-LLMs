import json, os, sys, time, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.prompts import messages, CATEGORIES, SEO_HINTS   # noqa

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
COST_PER_1K_LOCAL = float(os.getenv("COST_PER_1K_TOKENS", "0.00005"))

def load_samples():
    return json.load(open(ROOT / "data" / "samples.json", encoding="utf-8"))

def http_json(url, body=None, headers=None, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def ollama_chat(task, text, hint=""):
    body = {"model": OLLAMA_MODEL, "messages": messages(task, text, hint), "stream": False,
            "options": {"temperature": 0}}
    if task != "seo": body["format"] = "json"
    t0 = time.perf_counter()
    d = http_json(f"{OLLAMA_URL}/api/chat", body)
    wall = time.perf_counter() - t0
    ns = lambda k: d.get(k, 0) / 1e9
    return {"text": d["message"]["content"], "latency_s": wall,
            "in_tok": d.get("prompt_eval_count", 0), "out_tok": d.get("eval_count", 0),
            "load_s": ns("load_duration"), "prompt_s": ns("prompt_eval_duration"), "gen_s": ns("eval_duration")}

def parse_json(t):
    try: return json.loads(t)
    except Exception:
        import re
        m = re.search(r"\{.*\}", t, re.S)
        try: return json.loads(m.group(0)) if m else None
        except Exception: return None

def score(task, text, sample):
    """Devuelve (ok:bool, detalle) segun el criterio de cada tarea."""
    if task == "classify":
        d = parse_json(text) or {}
        c = str(d.get("category", "")).lower()
        return c == sample["expected_category"], c or "JSON invalido"
    if task == "enrich":
        d = parse_json(text)
        if not d: return False, "JSON invalido"
        ents = " ".join(str(e.get("text", "")) for e in d.get("entities", []) if isinstance(e, dict)).lower()
        found = [e for e in sample["expected_entities"] if e.lower() in ents]
        sent_ok = d.get("sentiment") == sample["expected_sentiment"]
        return sent_ok, f"sent={d.get('sentiment')} ents={len(found)}/{len(sample['expected_entities'])}"
    s = text.strip().strip('"')
    return len(s) < 160, f"{len(s)} chars"

def ram_info():
    try:
        m = http_json(f"{OLLAMA_URL}/api/ps", timeout=5).get("models", [])
        return {"size_mb": round(m[0]["size"] / 2**20), "vram_mb": round(m[0].get("size_vram", 0) / 2**20)} if m else {}
    except Exception: return {}

def median(xs):
    xs = sorted(xs); n = len(xs)
    return 0 if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)
