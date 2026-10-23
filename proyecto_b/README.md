# Proyecto B - Pipeline de Analisis Inteligente (Modalidad 2.3: Ollama local)

Cliente: MediaGroup LATAM. Pipeline de 7 etapas (ingest, validar, limpiar, analizar, enriquecer, resumen SEO, exportar) con FastAPI y llama3.2:3b sobre Ollama.

## Estructura
```
proyecto_b/
  Makefile            comandos desde la raiz (make help)
  backend/            API FastAPI, pipeline, scripts, datos de muestra
    app/  scripts/  data/  results/  requirements.txt  .env.example  Makefile
  frontend/           React + Vite (login, articulos, chat, dashboard)
  docs/               E1 diagrama C4, E2 RFC, E6 costos, ficha del modelo, indice de entregables
```

## Inicio rapido (desde la raiz)
```bash
make help        # lista todos los comandos
make install     # Ollama + llama3.2:3b + backend (Ubuntu 24.04)
make run         # API en http://127.0.0.1:8000  (primera vez: crea backend/.env; editalo)
make smoke       # en otra terminal: prueba extremo a extremo
make frontend-install && make frontend-dev   # interfaz en http://localhost:5173
make zip         # empaqueta en dist/proyecto_b.zip
```
Indice de entregables y estado: `docs/ENTREGABLES.md`.

## Arranque manual del backend
```bash
cd backend
bash scripts/install_ollama.sh
set -a; source .env; set +a
.venv/bin/uvicorn app.main:app --port 8000
```

## Prueba con curl
```bash
TOKEN=$(curl -s localhost:8000/auth/token -H 'content-type: application/json' \
  -d '{"username":"admin","password":"TU_CLAVE"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -s localhost:8000/webhook/articles -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"title":"Banco central sube tasas","body":"El Banco Central anuncio este martes un alza de 25 puntos base en la tasa de politica monetaria, citando presiones inflacionarias persistentes y la volatilidad del dolar."}'

curl -s localhost:8000/articles/<id> -H "Authorization: Bearer $TOKEN"
```

## Endpoints
POST /auth/token | POST /webhook/articles (202) | GET /articles | GET /articles/{id} | POST /chat | GET /dashboard | GET /health

## Criterios de la modalidad 2.3
- `docs/MODELO_OLLAMA.md`: ficha GGUF, RAM requerida, plantilla de benchmarks y limitaciones vs Vertex AI.
- `make benchmark`: latencia, tokens/s y memoria con los prompts reales (`backend/app/prompts.py`).
- `make compare CLOUD=vertex`: mismo prompt en Ollama vs API cloud.
- `backend/data/samples.json`: 5 articulos de muestra con etiquetas esperadas (entidades ficticias).
