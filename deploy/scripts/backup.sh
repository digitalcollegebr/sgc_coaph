#!/usr/bin/env bash
# =============================================================================
# backup.sh — Gera backup completo do site (banco + arquivos).
#
# Roda `bench backup --with-files`. NÃO apaga backups antigos.
#
# ONDE FICAM OS BACKUPS:
#   Dentro do volume nomeado 'sites', no caminho:
#     sites/${SITE_NAME}/private/backups/
#   Para copiar para o host, veja a dica no final da execução.
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

echo "==> [backup] Gerando backup (com arquivos) do site '${SITE_NAME}'..."
"${COMPOSE[@]}" exec -T backend \
  bench --site "${SITE_NAME}" backup --with-files

BACKUP_PATH="sites/${SITE_NAME}/private/backups/"
echo "==> [backup] Backup concluído."
echo "==> [backup] Local (dentro do volume 'sites'): ${BACKUP_PATH}"
echo "==> [backup] Backups antigos NÃO foram removidos."
echo ""
echo "    Para listar os backups gerados:"
echo "      docker compose -f compose.yaml --env-file .env exec backend ls -lh ${BACKUP_PATH}"
echo ""
echo "    Para copiar os backups para o host (ex.: pasta ./backups-export):"
echo "      CID=\$(docker compose -f compose.yaml --env-file .env ps -q backend)"
echo "      docker cp \"\$CID:/home/frappe/frappe-bench/${BACKUP_PATH}\" ./backups-export"
