#!/usr/bin/env bash
# =============================================================================
# migrate.sh — Roda as migrações do banco do site (bench migrate).
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

echo "==> [migrate] Executando migrate no site '${SITE_NAME}'..."
docker compose -f compose.yaml --env-file .env exec -T backend \
  bench --site "${SITE_NAME}" migrate

echo "==> [migrate] Concluído."
