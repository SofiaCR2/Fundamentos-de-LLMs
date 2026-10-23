#!/usr/bin/env bash
# Instalacion reproducible: Ollama + llama3.2:3b + backend en Ubuntu 24.04
set -euo pipefail

[[ "$(. /etc/os-release; echo "$VERSION_ID")" == "24.04" ]] || echo "AVISO: probado solo en Ubuntu 24.04"
RAM_GB=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
(( RAM_GB >= 6 )) || echo "AVISO: ${RAM_GB} GB RAM; se recomiendan >= 8 GB para llama3.2:3b"

sudo apt-get update -y
sudo apt-get install -y curl python3-venv python3-pip

command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama

for i in {1..30}; do curl -fs http://localhost:11434/api/tags >/dev/null && break || sleep 1; done
ollama pull llama3.2:3b

# Prueba de humo del modelo
curl -s http://localhost:11434/api/generate \
  -d '{"model":"llama3.2:3b","prompt":"Di hola en una palabra","stream":false}' | head -c 300; echo

# Backend
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
[[ -f .env ]] || cp .env.example .env
echo "Listo. Desde la raiz del proyecto ejecuta: make run"
