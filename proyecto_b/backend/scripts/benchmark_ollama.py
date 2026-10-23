#!/usr/bin/env python3
"""Mide latencia, tokens/s y RAM de Ollama con los prompts reales del pipeline.
Uso: python scripts/benchmark_ollama.py [--runs 3]   -> results/benchmark.json y .md"""
import argparse, json, platform, os
from _common import *

ap = argparse.ArgumentParser(); ap.add_argument("--runs", type=int, default=3); a = ap.parse_args()
samples = load_samples()
ollama_chat("classify", samples[0]["text"])            # calentamiento (carga del modelo)
rows = {"classify": [], "enrich": [], "seo": []}
for run in range(a.runs):
    for s in samples:
        for task in rows:
            r = ollama_chat(task, s["text"]); r["ok"], r["detail"] = score(task, r["text"], s)
            rows[task].append(r)
ram = ram_info()
cpu = next((l.split(":")[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), platform.processor()) \
    if os.path.exists("/proc/cpuinfo") else platform.processor()
mem_gb = round(int(next(l.split()[1] for l in open("/proc/meminfo") if l.startswith("MemTotal"))) / 1048576, 1) \
    if os.path.exists("/proc/meminfo") else "n/d"

summary = {}
for t, rs in rows.items():
    gen_tps = [r["out_tok"] / r["gen_s"] for r in rs if r["gen_s"] > 0]
    pr_tps = [r["in_tok"] / r["prompt_s"] for r in rs if r["prompt_s"] > 0]
    summary[t] = {"n": len(rs), "lat_p50_s": round(median([r["latency_s"] for r in rs]), 2),
                  "lat_max_s": round(max(r["latency_s"] for r in rs), 2),
                  "in_tok_avg": round(sum(r["in_tok"] for r in rs) / len(rs)),
                  "out_tok_avg": round(sum(r["out_tok"] for r in rs) / len(rs)),
                  "gen_tok_s": round(median(gen_tps), 1), "prompt_tok_s": round(median(pr_tps), 1),
                  "ok_pct": round(100 * sum(r["ok"] for r in rs) / len(rs))}
per_article = round(sum(v["lat_p50_s"] for v in summary.values()), 1)
out = {"model": OLLAMA_MODEL, "cpu": cpu, "ram_gb_total": mem_gb, "ollama_ps": ram,
       "runs": a.runs, "summary": summary, "pipeline_latency_p50_s": per_article}
json.dump(out, open(ROOT / "results" / "benchmark.json", "w"), indent=2)
md = [f"# Benchmark {OLLAMA_MODEL}", f"CPU: {cpu} | RAM total: {mem_gb} GB | Ollama ps: {ram or 'n/d'} | corridas: {a.runs}", "",
      "| Tarea | p50 (s) | max (s) | tok in | tok out | gen tok/s | prompt tok/s | aciertos % |", "|---|---|---|---|---|---|---|---|"]
for t, v in summary.items():
    md.append(f"| {t} | {v['lat_p50_s']} | {v['lat_max_s']} | {v['in_tok_avg']} | {v['out_tok_avg']} | {v['gen_tok_s']} | {v['prompt_tok_s']} | {v['ok_pct']} |")
md += ["", f"**Latencia estimada por articulo (suma de p50): {per_article} s**"]
open(ROOT / "results" / "benchmark.md", "w").write("\n".join(md) + "\n")
print("\n".join(md))
