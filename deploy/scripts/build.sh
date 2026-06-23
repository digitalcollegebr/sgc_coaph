#!/usr/bin/env bash
# =============================================================================
# build.sh — Constrói a imagem Docker customizada (ERPNext + coaph_contract_ops).
#
# Gera o APPS_JSON_BASE64 a partir do apps.json e roda o `docker build` usando
# o Containerfile. Deve rodar FORA do servidor de produção (CI ou máquina local).
#
# Uso:
#   ./build.sh                  # usa deploy/apps.example.json (renomeie p/ apps.json)
#   APPS_JSON=apps.json ./build.sh
# =============================================================================
set -euo pipefail

# Diretório raiz do deploy (pai da pasta scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

echo "==> [build] Diretório de deploy: ${DEPLOY_DIR}"

# Carrega variáveis do .env (CUSTOM_IMAGE, CUSTOM_TAG, branches).
if [[ ! -f .env ]]; then
  echo "ERRO: arquivo .env não encontrado em ${DEPLOY_DIR}."
  echo "      Copie o exemplo:  cp .env.example .env  e edite os valores."
  exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a

# Define qual apps.json usar.
APPS_JSON="${APPS_JSON:-apps.json}"
if [[ ! -f "${APPS_JSON}" ]]; then
  echo "AVISO: '${APPS_JSON}' não encontrado; usando 'apps.example.json' como base."
  APPS_JSON="apps.example.json"
fi
echo "==> [build] Lista de apps: ${APPS_JSON}"

# Gera o base64 do apps.json (sem quebras de linha).
APPS_JSON_BASE64="$(base64 -w0 "${APPS_JSON}" 2>/dev/null || base64 "${APPS_JSON}" | tr -d '\n')"

IMAGE="${CUSTOM_IMAGE:?defina CUSTOM_IMAGE no .env}:${CUSTOM_TAG:?defina CUSTOM_TAG no .env}"
echo "==> [build] Construindo imagem: ${IMAGE}"
echo "==> [build] FRAPPE_BRANCH=${FRAPPE_BRANCH}  ERPNEXT_BRANCH=${ERPNEXT_BRANCH}  COAPH_APP_BRANCH=${COAPH_APP_BRANCH}"

docker build \
  --file Containerfile \
  --tag "${IMAGE}" \
  --build-arg FRAPPE_BRANCH="${FRAPPE_BRANCH}" \
  --build-arg ERPNEXT_BRANCH="${ERPNEXT_BRANCH}" \
  --build-arg COAPH_APP_BRANCH="${COAPH_APP_BRANCH}" \
  --build-arg APPS_JSON_BASE64="${APPS_JSON_BASE64}" \
  .

echo "==> [build] Imagem construída com sucesso: ${IMAGE}"
echo "==> [build] Próximo passo: ./scripts/push.sh para publicar no Docker Hub."
