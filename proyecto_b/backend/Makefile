SHELL := /bin/bash
.DEFAULT_GOAL := help

HOST ?= 127.0.0.1
PORT ?= 8000
CLOUD ?= none
RUNS ?= 3
VENV := .venv

.PHONY: help install venv run dev health smoke benchmark compare check clean distclean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-12s %s\n",$$1,$$2}'

.env:
	cp .env.example .env
	@echo ">> Se creo backend/.env. Edita JWT_SECRET, APP_USER y APP_PASSWORD antes de exponer la API."

install: ## Instala Ollama + llama3.2:3b + backend (Ubuntu 24.04, usa sudo)
	bash scripts/install_ollama.sh

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	@touch $@

venv: $(VENV)/bin/activate ## Crea el entorno virtual e instala dependencias

run: venv .env ## Arranca la API (HOST/PORT configurables)
	set -a; . ./.env; set +a; $(VENV)/bin/uvicorn app.main:app --host $(HOST) --port $(PORT)

dev: venv .env ## Arranca la API con recarga automatica
	set -a; . ./.env; set +a; $(VENV)/bin/uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

health: ## Consulta /health (API, Ollama, circuit breaker)
	@curl -fsS http://localhost:$(PORT)/health | python3 -m json.tool

smoke: ## Prueba extremo a extremo: login, ingesta 202, resultado
	API=http://localhost:$(PORT) bash scripts/smoke_test.sh

benchmark: ## Mide latencia, tokens/s y RAM de Ollama -> results/benchmark.md
	python3 scripts/benchmark_ollama.py --runs $(RUNS)

compare: ## Mismo prompt en Ollama vs cloud -> results/compare.md (CLOUD=vertex|anthropic|none)
	python3 scripts/compare_providers.py --cloud $(CLOUD)

check: ## Verifica la sintaxis del codigo Python y de los scripts de shell
	python3 -m py_compile app/*.py scripts/*.py
	bash -n scripts/install_ollama.sh scripts/smoke_test.sh
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + ; echo "backend OK"

clean: ## Borra caches de Python
	@find . -name __pycache__ -type d -prune -exec rm -rf {} +

distclean: clean ## Borra ademas .venv, pipeline.db y results/
	rm -rf $(VENV) pipeline.db results/*
