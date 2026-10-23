"""Cliente Ollama local (llama3.2:3b) con circuit breaker, timeout y reintento."""
import json, re, httpx
from fastapi import HTTPException
from .core import OLLAMA_URL, OLLAMA_MODEL, breaker, event

async def chat(messages: list[dict], json_mode=False, temperature=0.2) -> tuple[str, int]:
    """Devuelve (texto, tokens_totales)."""
    if not breaker.allow():
        raise HTTPException(503, "Circuit breaker abierto: Ollama no disponible")
    body = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature}}
    if json_mode:
        body["format"] = "json"
    last = None
    for attempt in (1, 2):
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(f"{OLLAMA_URL}/api/chat", json=body)
                r.raise_for_status()
            d = r.json()
            breaker.ok()
            tokens = d.get("prompt_eval_count", 0) + d.get("eval_count", 0)
            return d["message"]["content"], tokens
        except Exception as e:
            last = e
            event("llm_error", attempt=attempt, error=str(e)[:200])
    breaker.fail()
    raise HTTPException(502, f"Fallo Ollama: {last}")

def parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}

async def health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            return (await c.get(f"{OLLAMA_URL}/api/tags")).status_code == 200
    except Exception:
        return False
