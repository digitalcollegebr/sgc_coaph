#!/usr/bin/env bash
# =============================================================================
# pull.sh — Baixa a imagem customizada publicada (servidor de produção).
#
# Roda `docker compose pull` para atualizar a imagem local a partir do Docker Hub.
# Não recria containers (use update.sh para aplicar a nova imagem).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

if [[ ! -f .env ]]; then
  echo "ERRO: arquivo .env não encontrado. Copie de .env.example e edite."
  exit 1
fi

echo "==> [pull] Baixando imagens da stack a partir do Docker Hub..."
docker compose -f compose.yaml --env-file .env pull

echo "==> [pull] Imagens atualizadas. Para aplicar, rode:  ./scripts/update.sh"
