"""Config, logging estructurado, tracing por etapa, auth JWT, rate limit y circuit breaker."""
import os, time, json, hmac, uuid, logging, contextlib
from collections import defaultdict, deque
import jwt
from fastapi import HTTPException, Header

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
APP_USER = os.getenv("APP_USER", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
COST_PER_1K = float(os.getenv("COST_PER_1K_TOKENS", "0.00005"))

# ---------- logging JSON ----------
class JsonFmt(logging.Formatter):
    def format(self, r):
        d = {"ts": round(r.created, 3), "level": r.levelname, "msg": r.getMessage()}
        d.update(getattr(r, "extra_data", {}))
        return json.dumps(d, ensure_ascii=False)

log = logging.getLogger("pipeline")
if not log.handlers:
    h = logging.StreamHandler(); h.setFormatter(JsonFmt())
    log.addHandler(h); log.setLevel(logging.INFO)

def event(name: str, **data):
    log.info(name, extra={"extra_data": {"event": name, **data}})

# ---------- tracing: un span por etapa ----------
@contextlib.contextmanager
def span(trace_id: str, stage: str, sink: list):
    s = {"stage": stage, "latency_ms": 0, "tokens": 0, "cost_usd": 0.0, "ok": True}
    t0 = time.perf_counter()
    try:
        yield s
    except Exception as e:
        s["ok"] = False; s["error"] = str(e)[:300]
        raise
    finally:
        s["latency_ms"] = round((time.perf_counter() - t0) * 1000)
        s["cost_usd"] = round(s["tokens"] / 1000 * COST_PER_1K, 8)
        sink.append(s)
        event("stage_span", trace_id=trace_id, **s)

def new_id() -> str:
    return uuid.uuid4().hex[:12]

# ---------- auth JWT ----------
def check_credentials(u: str, p: str) -> bool:
    return hmac.compare_digest(u, APP_USER) and hmac.compare_digest(p, APP_PASSWORD)

def make_token(user: str, ttl: int = 3600) -> str:
    return jwt.encode({"sub": user, "exp": int(time.time()) + ttl}, JWT_SECRET, algorithm="HS256")

_hits: dict[str, deque] = defaultdict(deque)

def current_user(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Falta token Bearer")
    try:
        user = jwt.decode(authorization[7:], JWT_SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Token invalido o expirado")
    # rate limiting: ventana deslizante de 60s por usuario
    now, q = time.time(), _hits[user]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        event("rate_limited", user=user)
        raise HTTPException(429, "Rate limit excedido", headers={"Retry-After": "60"})
    q.append(now)
    return user

# ---------- circuit breaker ----------
class CircuitBreaker:
    def __init__(self, threshold=3, reset_s=30):
        self.threshold, self.reset_s = threshold, reset_s
        self.fails, self.opened_at = 0, None

    @property
    def state(self):
        if self.opened_at is None: return "closed"
        return "half-open" if time.time() - self.opened_at >= self.reset_s else "open"

    def allow(self): return self.state != "open"

    def ok(self):
        self.fails, self.opened_at = 0, None

    def fail(self):
        self.fails += 1
        if self.fails >= self.threshold or self.state == "half-open":
            self.opened_at = time.time()
            event("circuit_opened", fails=self.fails)

breaker = CircuitBreaker()
