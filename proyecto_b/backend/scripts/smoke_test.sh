#!/usr/bin/env bash
# Prueba extremo a extremo: health -> login -> ingesta (202) -> espera -> resultado
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f .env ]] && { set -a; . ./.env; set +a; }
API="${API:-http://localhost:8000}"
command -v curl >/dev/null && command -v python3 >/dev/null || { echo "Faltan curl o python3"; exit 1; }
jget() { python3 -c 'import sys,json;print(json.loads(sys.argv[1])[sys.argv[2]])' "$1" "$2"; }

echo "1) health"; curl -fsS "$API/health"; echo
TOKEN=$(jget "$(curl -fsS "$API/auth/token" -H 'content-type: application/json' \
  -d "{\"username\":\"${APP_USER:-admin}\",\"password\":\"${APP_PASSWORD:-admin}\"}")" access_token)
echo "2) login OK"

PAYLOAD=$(python3 - <<'PY'
import json
s = json.load(open("data/samples.json", encoding="utf-8"))[0]
print(json.dumps({"title": "Prueba smoke: " + s["id"], "body": s["text"]}))
PY
)
RESP=$(curl -sS -w '\n%{http_code} %{time_total}' "$API/webhook/articles" \
  -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' -d "$PAYLOAD")
META=${RESP##*$'\n'}; BODY=${RESP%$'\n'*}
echo "3) ingesta -> HTTP / segundos: $META"
[[ "${META%% *}" == 202 ]] || { echo "SMOKE FALLO: se esperaba 202"; echo "$BODY"; exit 1; }
ID=$(jget "$BODY" id)

ST=queued; R=""
for _ in $(seq 1 90); do
  R=$(curl -fsS "$API/articles/$ID" -H "Authorization: Bearer $TOKEN")
  ST=$(jget "$R" status); echo "   estado: $ST"
  [[ $ST == done || $ST == failed ]] && break
  sleep 3
done
python3 -c 'import sys,json;d=json.loads(sys.argv[1]);print(json.dumps(d.get("result") or d.get("error"),ensure_ascii=False,indent=2))' "$R"
[[ $ST == done ]] && echo "SMOKE OK" || { echo "SMOKE FALLO (estado: $ST)"; exit 1; }
