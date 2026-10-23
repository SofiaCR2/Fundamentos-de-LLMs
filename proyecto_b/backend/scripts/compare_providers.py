#!/usr/bin/env python3
"""Mismo prompt en Ollama vs API cloud. Genera results/compare.json y compare.md.
  --cloud vertex     requiere: gcloud auth, GCP_PROJECT, (GCP_LOCATION, VERTEX_MODEL)
  --cloud anthropic  requiere: ANTHROPIC_API_KEY, ANTHROPIC_MODEL
  --cloud none       solo Ollama (para probar sin cloud)
Precios (USD por 1M tokens) para el costo cloud: CLOUD_PRICE_IN / CLOUD_PRICE_OUT (sin ellos: n/d)."""
import argparse, os, subprocess, time, json
from _common import *

def cloud_call(provider, task, text, hint=""):
    msgs = messages(task, text, hint); system, user = msgs[0]["content"], msgs[1]["content"]
    t0 = time.perf_counter()
    if provider == "vertex":
        proj, loc, model = os.environ["GCP_PROJECT"], os.getenv("GCP_LOCATION", "us-central1"), os.environ["VERTEX_MODEL"]
        tok = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
        url = (f"https://{loc}-aiplatform.googleapis.com/v1/projects/{proj}/locations/{loc}"
               f"/publishers/google/models/{model}:generateContent")
        gc = {"temperature": 0}
        if task != "seo": gc["responseMimeType"] = "application/json"
        d = http_json(url, {"systemInstruction": {"parts": [{"text": system}]},
                            "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": gc},
                      {"Authorization": f"Bearer {tok}"})
        text_out = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
        u = d.get("usageMetadata", {}); i, o = u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0)
    else:
        d = http_json("https://api.anthropic.com/v1/messages",
                      {"model": os.environ["ANTHROPIC_MODEL"], "max_tokens": 400, "temperature": 0,
                       "system": system, "messages": [{"role": "user", "content": user}]},
                      {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
        text_out = "".join(b.get("text", "") for b in d["content"])
        i, o = d["usage"]["input_tokens"], d["usage"]["output_tokens"]
    return {"text": text_out, "latency_s": time.perf_counter() - t0, "in_tok": i, "out_tok": o}

ap = argparse.ArgumentParser(); ap.add_argument("--cloud", default="vertex", choices=["vertex", "anthropic", "none"])
a = ap.parse_args()
pin, pout = os.getenv("CLOUD_PRICE_IN"), os.getenv("CLOUD_PRICE_OUT")
samples = load_samples(); ollama_chat("classify", samples[0]["text"])  # calentamiento
provs = ["ollama"] + ([] if a.cloud == "none" else [a.cloud])
res = []
for s in samples:
    for task in ("classify", "enrich", "seo"):
        row = {"sample": s["id"], "task": task}
        for p in provs:
            r = ollama_chat(task, s["text"]) if p == "ollama" else cloud_call(p, task, s["text"])
            r["ok"], r["detail"] = score(task, r["text"], s)
            if p == "ollama": r["cost_usd"] = (r["in_tok"] + r["out_tok"]) / 1000 * COST_PER_1K_LOCAL
            elif pin and pout: r["cost_usd"] = (r["in_tok"] * float(pin) + r["out_tok"] * float(pout)) / 1e6
            else: r["cost_usd"] = None
            row[p] = r
        res.append(row)
json.dump(res, open(ROOT / "results" / "compare.json", "w"), ensure_ascii=False, indent=2)

def agg(p):
    rs = [r[p] for r in res]
    cs = [r["cost_usd"] for r in rs]
    return (f"{round(100 * sum(r['ok'] for r in rs) / len(rs))}%", f"{median([r['latency_s'] for r in rs]):.2f}",
            sum(r["in_tok"] + r["out_tok"] for r in rs), "n/d" if None in cs else f"{sum(cs):.5f}")
md = ["# Comparativa Ollama vs cloud (mismo prompt, temperatura 0)", "",
      "| Proveedor | Aciertos | Latencia p50 (s) | Tokens totales | Costo (USD)* |", "|---|---|---|---|---|"]
md += [f"| {p} | " + " | ".join(map(str, agg(p))) + " |" for p in provs]
md += ["", "*Ollama: estimacion por tokens (COST_PER_1K_TOKENS), no incluye costo fijo de la maquina.", "",
       "## Respuestas lado a lado", ""]
for r in res:
    md.append(f"### {r['sample']} / {r['task']}")
    for p in provs:
        x = r[p]; txt = x["text"].replace("\n", " ")[:300]
        md.append(f"- **{p}** ({x['latency_s']:.1f}s, {'OK' if x['ok'] else 'FALLA'}, {x['detail']}): `{txt}`")
    md.append("")
open(ROOT / "results" / "compare.md", "w").write("\n".join(md))
print("\n".join(md[:8]))
