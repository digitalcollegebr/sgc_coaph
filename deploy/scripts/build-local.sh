#!/usr/bin/env bash
# Builda a imagem customizada a partir do CÓDIGO LOCAL (sem Git remoto),
# assentando o app sobre a imagem oficial frappe/erpnext.
# Uso: deploy/scripts/build-local.sh [tag]   (tag padrão: local)
set -euo pipefail

TAG="${1:-local}"
IMAGE="${CUSTOM_IMAGE:-coaph/sgc-erpnext}"
ERPNEXT_BRANCH="${ERPNEXT_BRANCH:-version-15}"

# Vai para a raiz do repositório (contexto de build precisa ver ./apps).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

echo ">> Buildando ${IMAGE}:${TAG} (base: frappe/erpnext:${ERPNEXT_BRANCH})"
docker build \
  -f deploy/Containerfile.local \
  --build-arg ERPNEXT_BRANCH="${ERPNEXT_BRANCH}" \
  -t "${IMAGE}:${TAG}" \
  .
echo ">> Imagem pronta: ${IMAGE}:${TAG}"
