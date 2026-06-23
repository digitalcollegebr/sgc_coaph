#!/usr/bin/env bash
# =============================================================================
# seed-demo.sh — Carrega dados de demonstração no site.
#
# Executa o método Python do app:
#   coaph_contract_ops.scripts.seed_demo_data.execute
#
# ATENÇÃO: destinado a ambientes de POC/demo. Não rode em produção real.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

if [[ ! -f .env ]]; then
  echo "ERRO: arquivo .env não encontrado. Copie de .env.example e edite."
  exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${SITE_NAME:?defina SITE_NAME no .env}"

echo "==> [seed-demo] Carregando dados de demonstração no site '${SITE_NAME}'..."
docker compose -f compose.yaml --env-file .env exec -T backend \
  bench --site "${SITE_NAME}" execute coaph_contract_ops.scripts.seed_demo_data.execute

echo "==> [seed-demo] Dados de demonstração carregados."
