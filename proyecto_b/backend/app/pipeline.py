"""Pipeline de 7 etapas: ingest > validar > limpiar > analizar > enriquecer > resumen SEO > exportar."""
import re, html, httpx
from fastapi import HTTPException
from . import llm, store
from .core import span, event

from .prompts import CATEGORIES, SEO_HINTS, messages  # prompts compartidos con scripts/

def validate(p: dict):                       # 02 Validar (schema ya validado por pydantic)
    if len(p["body"].strip()) < 50:
        raise ValueError("El cuerpo del articulo es demasiado corto (<50 chars)")

def clean(text: str) -> str:                 # 03 Limpiar -> texto plano
    text = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()

async def classify(text: str):               # 04 Analizar (LLM call)
    msg = messages("classify", text)
    out, tok = await llm.chat(msg, json_mode=True, temperature=0)
    cat = str(llm.parse_json(out).get("category", "otros")).lower()
    return (cat if cat in CATEGORIES else "otros"), tok

async def enrich(text: str):                 # 05 Enriquecer: NER + sentimiento
    msg = messages("enrich", text)
    out, tok = await llm.chat(msg, json_mode=True, temperature=0)
    d = llm.parse_json(out)
    sent = d.get("sentiment") if d.get("sentiment") in ("positivo", "neutral", "negativo") else "neutral"
    ents = [e for e in d.get("entities", []) if isinstance(e, dict) and e.get("text")][:15]
    return {"entities": ents, "sentiment": sent, "sentiment_score": d.get("sentiment_score", 0)}, tok

async def seo_summary(text: str):            # 06 Resumen SEO < 160 chars
    tokens, summary = 0, ""
    for hint in SEO_HINTS:
        msg = messages("seo", text, hint)
        out, tok = await llm.chat(msg, temperature=0.3)
        tokens += tok; summary = out.strip().strip('"')
        if len(summary) < 160: return summary, tokens
    cut = summary[:157].rsplit(" ", 1)[0]    # garantia dura
    return cut + "...", tokens

async def export(aid: str, result: dict, callback_url: str | None):   # 07 DB + Webhook
    store.update(aid, status="done", result=result)
    if callback_url:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.post(callback_url, json={"id": aid, **result})
            return True
        except Exception as e:
            event("webhook_failed", id=aid, error=str(e)[:200])
    return False

async def run(aid: str, payload: dict):
    spans: list = []
    store.update(aid, status="processing")
    result: dict = {"title": payload["title"], "url": payload.get("url")}
    try:
        with span(aid, "02_validate", spans): validate(payload)
        with span(aid, "03_clean", spans): text = clean(payload["body"])
        with span(aid, "04_analyze", spans) as s:
            result["category"], s["tokens"] = await classify(text)
        with span(aid, "05_enrich", spans) as s:
            data, s["tokens"] = await enrich(text); result.update(data)
        with span(aid, "06_seo_summary", spans) as s:
            result["seo_summary"], s["tokens"] = await seo_summary(text)
        with span(aid, "07_export", spans):
            result["webhook_delivered"] = await export(aid, result, payload.get("callback_url"))
        store.update(aid, metrics=spans)
        event("pipeline_done", id=aid, total_ms=sum(x["latency_ms"] for x in spans))
    except (HTTPException, Exception) as e:
        store.update(aid, status="failed", error=str(getattr(e, "detail", e)), metrics=spans)
        event("pipeline_failed", id=aid, error=str(getattr(e, "detail", e)))
