#!/usr/bin/env bash
# =============================================================================
# install-app.sh — Instala o app coaph_contract_ops no site + migrate + clear-cache.
#
# Útil quando o site já existe e você quer (re)instalar/atualizar o app custom.
# Idempotente: se o app já estiver instalado, apenas roda migrate e limpa cache.
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

COMPOSE=(docker compose -f compose.yaml --env-file .env)

echo "==> [install-app] Verificando se coaph_contract_ops já está instalado em '${SITE_NAME}'..."
if "${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" list-apps 2>/dev/null | grep -qw coaph_contract_ops; then
  echo "==> [install-app] App já instalado. Pulando install-app."
else
  echo "==> [install-app] Instalando coaph_contract_ops..."
  "${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" install-app coaph_contract_ops
fi

echo "==> [install-app] Rodando migrate..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" migrate

echo "==> [install-app] Limpando cache..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" clear-cache

echo "==> [install-app] Concluído."
