from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
import os
from . import llm, store, pipeline
from .core import (check_credentials, make_token, current_user, new_id,
                   breaker, event, OLLAMA_MODEL)

app = FastAPI(title="Pipeline de Analisis Inteligente (Ollama local)")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])

class Login(BaseModel):
    username: str
    password: str

class ArticleIn(BaseModel):                  # 02 Validar: schema JSON
    title: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=1, max_length=100_000)
    url: HttpUrl | None = None
    callback_url: HttpUrl | None = None

class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

@app.post("/auth/token")
def login(c: Login):
    if not check_credentials(c.username, c.password):
        event("login_failed", user=c.username)
        raise HTTPException(401, "Credenciales invalidas")
    event("login_ok", user=c.username)
    return {"access_token": make_token(c.username), "token_type": "bearer"}

@app.post("/webhook/articles", status_code=202)       # 01 Ingest: responde < 200ms
async def ingest(a: ArticleIn, bg: BackgroundTasks, user: str = Depends(current_user)):
    aid = new_id()
    payload = {k: (str(v) if v is not None else None) for k, v in a.model_dump().items()}
    store.create(aid, payload)
    bg.add_task(pipeline.run, aid, payload)
    event("article_ingested", id=aid, user=user)
    return {"id": aid, "status": "queued"}

@app.get("/articles")
def articles(limit: int = 50, user: str = Depends(current_user)):
    return store.list_(min(limit, 200))

@app.get("/articles/{aid}")
def article(aid: str, user: str = Depends(current_user)):
    r = store.get(aid)
    if not r: raise HTTPException(404, "No encontrado")
    return r

@app.post("/chat")
async def chat(c: ChatIn, user: str = Depends(current_user)):
    text, tokens = await llm.chat([
        {"role": "system", "content": "Eres un asistente editorial para MediaGroup LATAM. Responde en espanol."},
        {"role": "user", "content": c.message}], temperature=0.5)
    event("chat", user=user, tokens=tokens)
    return {"reply": text, "tokens": tokens, "model": OLLAMA_MODEL}

@app.get("/dashboard")
def dashboard(user: str = Depends(current_user)):
    return {**store.stats(), "circuit": breaker.state, "model": OLLAMA_MODEL}

@app.get("/health")
async def health():
    ok = await llm.health()
    return {"api": "ok", "ollama": "ok" if ok else "down", "circuit": breaker.state}
