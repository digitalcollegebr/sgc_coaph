#!/usr/bin/env bash
# =============================================================================
# SGC COAPH — Subida TURNKEY para DEMONSTRAÇÃO (local, Docker Desktop)
#
# Faz tudo em um comando:
#   1. cria .env (se não existir) com senhas de demo (admin) e CUSTOM_TAG=local
#   2. builda a imagem local (ERPNext oficial + coaph_contract_ops)
#   3. sobe a stack (compose.yaml + compose.local.yaml)
#   4. cria o site (se não existir) e instala o app
#   5. roda migrate + carrega dados de demonstração (idempotente)
#
# Uso (a partir da raiz do repositório ou de qualquer lugar):
#   deploy/scripts/demo-up.sh
#
# Funciona em macOS (Docker Desktop, Apple Silicon ou Intel) e Linux.
# A imagem base frappe/erpnext:version-15 é multi-arch (arm64/amd64).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

# ---------------------------------------------------------------- 1) .env
if [ ! -f .env ]; then
  echo ">> Criando .env de demonstração a partir de .env.example"
  cp .env.example .env
  # senhas de DEMO (troque para algo real em produção)
  sed -i.bak \
    -e 's/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=admin/' \
    -e 's/^DB_ROOT_PASSWORD=.*/DB_ROOT_PASSWORD=admin/' \
    -e 's/^DB_PASSWORD=.*/DB_PASSWORD=admin/' \
    -e 's/^CUSTOM_TAG=.*/CUSTOM_TAG=local/' \
    .env
  rm -f .env.bak
  echo "   (senhas de demo = 'admin' — apenas para demonstração local)"
fi

# carrega variáveis do .env para uso no script
set -a; . ./.env; set +a
: "${SITE_NAME:?defina SITE_NAME no .env}"
: "${CUSTOM_TAG:=local}"

COMPOSE=(docker compose -f compose.yaml -f compose.local.yaml --env-file .env)

# ---------------------------------------------------------------- 2) build
echo ">> Buildando a imagem local (${CUSTOM_IMAGE}:${CUSTOM_TAG})..."
"${SCRIPT_DIR}/build-local.sh" "${CUSTOM_TAG}"

# ---------------------------------------------------------------- 3) up
echo ">> Subindo a stack..."
"${COMPOSE[@]}" up -d

echo ">> Aguardando o backend ficar pronto..."
for i in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T backend bash -lc 'cd /home/frappe/frappe-bench && ls apps >/dev/null' 2>/dev/null; then
    break
  fi
  sleep 3
done

# ---------------------------------------------------------------- 4) site
if "${COMPOSE[@]}" exec -T backend bash -lc "test -d /home/frappe/frappe-bench/sites/${SITE_NAME}" 2>/dev/null; then
  echo ">> Site '${SITE_NAME}' já existe — pulando criação."
else
  echo ">> Criando site '${SITE_NAME}' e instalando o app..."
  "${COMPOSE[@]}" exec -T backend bench new-site "${SITE_NAME}" \
    --no-mariadb-socket \
    --admin-password "${ADMIN_PASSWORD}" \
    --db-root-password "${DB_ROOT_PASSWORD}" \
    --install-app coaph_contract_ops \
    --set-default
fi

# ---------------------------------------------------------------- 5) migrate + seed
echo ">> Rodando migrate..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" migrate

echo ">> Carregando dados de demonstração (idempotente)..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" \
  execute coaph_contract_ops.scripts.seed_demo_data.execute

echo
echo "============================================================"
echo " SGC COAPH no ar para demonstração!"
echo "   URL:    http://localhost:${HTTP_PORT}"
echo "   Login:  Administrator"
echo "   Senha:  ${ADMIN_PASSWORD}"
echo "   Workspace: SGC COAPH  (/app/sgc-coaph)"
echo "------------------------------------------------------------"
echo " Parar:    docker compose -f compose.yaml -f compose.local.yaml --env-file .env stop"
echo " Religar:  docker compose -f compose.yaml -f compose.local.yaml --env-file .env start"
echo " NUNCA use 'down -v' (apaga o banco/volumes)."
echo "============================================================"
