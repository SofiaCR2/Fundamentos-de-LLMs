import { useState, useEffect, useCallback } from "react";
import { api } from "./api.js";

function Login({ onToken }) {
  const [u, setU] = useState("admin");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");
  const submit = async () => {
    try {
      const r = await api("/auth/token", { method: "POST", body: { username: u, password: p } });
      onToken(r.access_token);
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="card login">
      <h1>Iniciar sesión</h1>
      <input value={u} onChange={(e) => setU(e.target.value)} placeholder="Usuario" />
      <input type="password" value={p} onChange={(e) => setP(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()} placeholder="Contraseña" />
      <button onClick={submit}>Entrar</button>
      {err && <p className="err">{err}</p>}
    </div>
  );
}

function Articles({ call }) {
  const [list, setList] = useState([]);
  const [form, setForm] = useState({ title: "", body: "" });
  const [msg, setMsg] = useState("");
  const load = useCallback(() => call("/articles").then(setList).catch(() => {}), [call]);
  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t); }, [load]);

  const send = async () => {
    try {
      const r = await call("/webhook/articles", { method: "POST", body: form });
      setMsg(`Encolado: ${r.id}`); setForm({ title: "", body: "" }); load();
    } catch (e) { setMsg(e.message); }
  };
  return (
    <>
      <div className="card">
        <h2>Enviar artículo</h2>
        <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Título" />
        <textarea rows={5} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} placeholder="Cuerpo (HTML o texto)" />
        <button onClick={send}>Analizar</button>
        {msg && <p className="muted">{msg}</p>}
      </div>
      {list.map((a) => (
        <div className="card" key={a.id}>
          <div className="row">
            <strong>{a.input?.title}</strong>
            <span className={`badge ${a.status}`}>{a.status}</span>
          </div>
          {a.result && (
            <>
              <p className="muted">{a.result.seo_summary}</p>
              <p>
                <span className="tag">{a.result.category}</span>
                <span className="tag">{a.result.sentiment}</span>
                {a.result.entities?.map((e, i) => <span className="tag ent" key={i}>{e.text} · {e.type}</span>)}
              </p>
            </>
          )}
          {a.error && <p className="err">{a.error}</p>}
        </div>
      ))}
    </>
  );
}

function Chat({ call }) {
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const send = async () => {
    if (!text.trim() || busy) return;
    const m = text; setText(""); setBusy(true);
    setMsgs((x) => [...x, { role: "user", text: m }]);
    try {
      const r = await call("/chat", { method: "POST", body: { message: m } });
      setMsgs((x) => [...x, { role: "bot", text: r.reply, meta: `${r.tokens} tokens · ${r.model}` }]);
    } catch (e) { setMsgs((x) => [...x, { role: "bot", text: e.message, error: true }]); }
    setBusy(false);
  };
  return (
    <div className="card">
      <div className="chat">
        {msgs.map((m, i) => (
          <div key={i} className={`bubble ${m.role} ${m.error ? "err" : ""}`}>
            {m.text}{m.meta && <small>{m.meta}</small>}
          </div>
        ))}
        {busy && <div className="bubble bot muted">Pensando…</div>}
      </div>
      <div className="row">
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Pregunta algo…" />
        <button onClick={send} disabled={busy}>Enviar</button>
      </div>
    </div>
  );
}

function Dashboard({ call }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    const load = () => call("/dashboard").then(setD).catch(() => {});
    load(); const t = setInterval(load, 5000); return () => clearInterval(t);
  }, [call]);
  if (!d) return <p className="muted">Cargando…</p>;
  const max = Math.max(1, ...Object.values(d.avg_latency_ms_per_stage));
  return (
    <>
      <div className="grid">
        <div className="card kpi"><b>{d.articles}</b>artículos</div>
        <div className="card kpi"><b>{d.total_tokens}</b>tokens</div>
        <div className="card kpi"><b>${d.total_cost_usd}</b>costo est.</div>
        <div className="card kpi"><b>{d.circuit}</b>circuit breaker</div>
      </div>
      <div className="card">
        <h2>Latencia media por etapa (ms)</h2>
        {Object.entries(d.avg_latency_ms_per_stage).sort().map(([k, v]) => (
          <div className="bar" key={k}>
            <span>{k}</span>
            <div><i style={{ width: `${(v / max) * 100}%` }} /></div>
            <em>{v}</em>
          </div>
        ))}
      </div>
    </>
  );
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token") || "");
  const [tab, setTab] = useState("articles");
  const logout = useCallback(() => { localStorage.removeItem("token"); setToken(""); }, []);
  const save = (t) => { localStorage.setItem("token", t); setToken(t); };
  const call = useCallback((path, opts = {}) => api(path, { ...opts, token, onUnauthorized: logout }), [token, logout]);

  if (!token) return <Login onToken={save} />;
  return (
    <div className="app">
      <header>
        <h1>Pipeline de Análisis</h1>
        <nav>
          {[["articles", "Artículos"], ["chat", "Chat"], ["dash", "Dashboard"]].map(([k, l]) => (
            <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>
          ))}
          <button onClick={logout}>Salir</button>
        </nav>
      </header>
      {tab === "articles" && <Articles call={call} />}
      {tab === "chat" && <Chat call={call} />}
      {tab === "dash" && <Dashboard call={call} />}
    </div>
  );
}
