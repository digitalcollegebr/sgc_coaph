#!/usr/bin/env bash
# =============================================================================
# push.sh — Publica a imagem customizada no Docker Hub.
#
# Verifica se há login ativo no Docker Hub antes de empurrar.
# NÃO contém credenciais: o login deve ser feito previamente com `docker login`.
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

IMAGE="${CUSTOM_IMAGE:?defina CUSTOM_IMAGE no .env}:${CUSTOM_TAG:?defina CUSTOM_TAG no .env}"

echo "==> [push] Verificando login no Docker Hub..."
if ! docker info 2>/dev/null | grep -qi "Username"; then
  echo "AVISO: não foi possível confirmar login no Docker Hub."
  echo "       Se o push falhar, rode antes:  docker login"
fi

echo "==> [push] Enviando imagem: ${IMAGE}"
docker push "${IMAGE}"

# Também publica :latest (aponta para a mesma imagem do CUSTOM_TAG atual).
if [[ "${CUSTOM_TAG}" != "latest" ]]; then
  docker tag "${IMAGE}" "${CUSTOM_IMAGE}:latest"
  echo "==> [push] Enviando imagem: ${CUSTOM_IMAGE}:latest"
  docker push "${CUSTOM_IMAGE}:latest"
fi

echo "==> [push] Publicação concluída: ${IMAGE} (e :latest)"
echo "==> [push] No servidor, rode:  ./scripts/pull.sh  e depois  ./scripts/update.sh"
