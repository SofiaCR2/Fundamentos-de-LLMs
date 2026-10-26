# ============================================================
# Sesión 3 · LLM Security Lab — Makefile
# ============================================================
# Uso:
#   make setup      → configurar entorno por primera vez
#   make backend    → levantar FastAPI en http://localhost:8000/docs
#   make frontend   → levantar React en http://localhost:5173
#   make test       → correr pruebas (sin Ollama)
#   make labs       → ejecutar todos los labs en secuencia
#   make simulado   → Ollama simulado (sin GPU)
#   make docker     → levantar todo con Docker
#   make clean      → limpiar archivos temporales
# ============================================================
#
# NOTA TÉCNICA: cada línea de receta Make corre en un subshell independiente,
# por lo que "source .venv/bin/activate" NO persiste entre líneas.
# La solución es llamar a los ejecutables del venv por su ruta completa.
# ============================================================

PYTHON   := python3.12
VENV     := .venv
VENV_BIN := $(VENV)/bin

# Ejecutables del entorno virtual (ruta relativa al directorio del proyecto)
VENV_PIP    := $(VENV_BIN)/pip
VENV_PYTHON := $(VENV_BIN)/python
VENV_PYTEST := $(VENV_BIN)/pytest
VENV_UVICORN := $(VENV_BIN)/uvicorn

.PHONY: setup backend frontend test labs lab09 lab10 lab11 lab12 lab13 lab14 \
        simulado docker docker-down clean help

# ─── Configuración inicial ───────────────────────────────────────────────────

setup:
	@echo "── Creando entorno virtual con Python 3.12 ──"
	$(PYTHON) -m venv $(VENV)
	@echo "── Instalando dependencias del backend ──"
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "── Creando backend/.env desde .env.example ──"
	@test -f backend/.env || cp backend/.env.example backend/.env
	@echo "── Instalando dependencias del frontend ──"
	@command -v node >/dev/null 2>&1 || (echo "⚠️  Node.js no encontrado. Instala Node 22+" && exit 1)
	cd frontend && npm install
	@echo ""
	@echo "✅ Setup completo. Ahora puedes:"
	@echo "   make backend    → terminal 1"
	@echo "   make frontend   → terminal 2"

# ─── Servicios ───────────────────────────────────────────────────────────────

backend:
	@echo "── Iniciando FastAPI en http://localhost:8000/docs ──"
	@test -f $(VENV_BIN)/uvicorn || (echo "⚠️  Ejecuta 'make setup' primero" && exit 1)
	cd backend && ../$(VENV_UVICORN) app.main:app --reload --port 8000

frontend:
	@echo "── Iniciando React en http://localhost:5173 ──"
	@test -d frontend/node_modules || (echo "⚠️  Ejecuta 'make setup' primero" && exit 1)
	cd frontend && npm run dev

# ─── Ayuda ───────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Sesión 3 · LLM Security Lab"
	@echo "════════════════════════════"
	@echo "  make setup     Configurar entorno (primera vez)"
	@echo "  make backend   Levantar FastAPI (puerto 8000)"
	@echo "  make frontend  Levantar React (puerto 5173)"
	@echo ""
