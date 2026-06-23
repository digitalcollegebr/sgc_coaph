#!/usr/bin/env bash
# =============================================================================
# logs.sh — Exibe logs dos containers da stack.
#
# Uso:
#   ./logs.sh                 # logs de todos os serviços (segue em tempo real)
#   ./logs.sh backend         # logs apenas do serviço informado
#   ./logs.sh frontend        # idem para o frontend (nginx)
#
# Serviços disponíveis: backend, frontend, websocket, scheduler,
#                       queue-short, queue-long, db, redis-cache, redis-queue
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

if [[ ! -f .env ]]; then
  echo "ERRO: arquivo .env não encontrado. Copie de .env.example e edite."
  exit 1
fi

SERVICE="${1:-}"

if [[ -n "${SERVICE}" ]]; then
  echo "==> [logs] Exibindo logs do serviço '${SERVICE}' (Ctrl+C para sair)..."
  docker compose -f compose.yaml --env-file .env logs -f --tail=200 "${SERVICE}"
else
  echo "==> [logs] Exibindo logs de TODOS os serviços (Ctrl+C para sair)..."
  docker compose -f compose.yaml --env-file .env logs -f --tail=100
fi
