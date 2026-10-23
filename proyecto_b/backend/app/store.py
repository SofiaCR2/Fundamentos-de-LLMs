"""Persistencia SQLite (etapa 07: DB)."""
import sqlite3, json, os, time, threading

_lock = threading.Lock()
_db = sqlite3.connect(os.getenv("DB_PATH", "pipeline.db"), check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("""CREATE TABLE IF NOT EXISTS articles(
  id TEXT PRIMARY KEY, status TEXT, created_at REAL,
  input TEXT, result TEXT, error TEXT, metrics TEXT)""")
_db.commit()

def _row(r):
    if not r: return None
    d = dict(r)
    for k in ("input", "result", "metrics"):
        d[k] = json.loads(d[k]) if d[k] else None
    return d

def create(aid, inp):
    with _lock:
        _db.execute("INSERT INTO articles VALUES(?,?,?,?,NULL,NULL,NULL)",
                    (aid, "queued", time.time(), json.dumps(inp, ensure_ascii=False)))
        _db.commit()

def update(aid, **f):
    for k, v in f.items():
        if isinstance(v, (dict, list)): f[k] = json.dumps(v, ensure_ascii=False)
    sets = ",".join(f"{k}=?" for k in f)
    with _lock:
        _db.execute(f"UPDATE articles SET {sets} WHERE id=?", (*f.values(), aid))
        _db.commit()

def get(aid):
    with _lock:
        return _row(_db.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone())

def list_(limit=50):
    with _lock:
        return [_row(r) for r in _db.execute(
            "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?", (limit,))]

def stats():
    rows = list_(1000)
    spans = [s for r in rows if r["metrics"] for s in r["metrics"]]
    n = len(rows)
    by = {}
    for r in rows: by[r["status"]] = by.get(r["status"], 0) + 1
    return {
        "articles": n, "by_status": by,
        "total_tokens": sum(s["tokens"] for s in spans),
        "total_cost_usd": round(sum(s["cost_usd"] for s in spans), 6),
        "avg_latency_ms_per_stage": {
            st: round(sum(s["latency_ms"] for s in spans if s["stage"] == st) /
                      max(1, sum(1 for s in spans if s["stage"] == st)))
            for st in {s["stage"] for s in spans}},
    }
