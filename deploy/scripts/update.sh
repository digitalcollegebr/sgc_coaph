#!/usr/bin/env bash
# =============================================================================
# update.sh — Atualiza a stack para a nova imagem publicada (sem perder dados).
#
# Passos:
#   1. Baixa a imagem nova (docker compose pull).
#   2. Recria os containers com a nova imagem (up -d).
#   3. Roda migrate.
#   4. Limpa cache.
#
# Os volumes nomeados (sites, db, redis) são PRESERVADOS — nada de `down -v`.
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

echo "==> [update] Baixando imagem ${CUSTOM_IMAGE:-?}:${CUSTOM_TAG:-?}..."
"${COMPOSE[@]}" pull

echo "==> [update] Recriando containers com a nova imagem..."
"${COMPOSE[@]}" up -d

echo "==> [update] Aguardando backend ficar disponível..."
for i in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T backend bench version >/dev/null 2>&1; then
    break
  fi
  echo "    ... aguardando backend (tentativa ${i}/30)"
  sleep 5
done

echo "==> [update] Rodando migrate..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" migrate

echo "==> [update] Limpando cache..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" clear-cache

echo "==> [update] Atualização concluída. Volumes preservados."
