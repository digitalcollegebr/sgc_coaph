#!/usr/bin/env bash
# =============================================================================
# restore.sh — Restaura um backup para o site (OPERAÇÃO DESTRUTIVA).
#
# ATENÇÃO: a restauração SOBRESCREVE o banco de dados atual do site.
# Por isso o script EXIGE confirmação explícita (digitar "sim").
#
# Uso:
#   ./restore.sh <caminho-do-arquivo-sql-ou-gz-DENTRO-do-container>
#   Ex.: ./restore.sh sites/sgc.localhost/private/backups/20260101_000000-sgc_database.sql.gz
#
# Dica: para listar backups disponíveis dentro do container:
#   docker compose -f compose.yaml --env-file .env exec backend \
#     ls -lh sites/${SITE_NAME}/private/backups/
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
: "${DB_ROOT_PASSWORD:?defina DB_ROOT_PASSWORD no .env}"

if [[ $# -lt 1 ]]; then
  echo "ERRO: informe o caminho do arquivo de backup (dentro do container)."
  echo "Uso:  ./restore.sh <caminho-do-backup.sql.gz>"
  exit 1
fi
BACKUP_FILE="$1"

echo "============================================================"
echo " OPERAÇÃO DESTRUTIVA — RESTAURAÇÃO DE BACKUP"
echo "============================================================"
echo " Site alvo .....: ${SITE_NAME}"
echo " Backup ........: ${BACKUP_FILE}"
echo ""
echo " Isto VAI SOBRESCREVER o banco de dados atual do site."
echo " Todos os dados atuais não salvos em backup SERÃO PERDIDOS."
echo "============================================================"
read -r -p "Tem certeza? Digite exatamente 'sim' para continuar: " CONFIRM

if [[ "${CONFIRM}" != "sim" ]]; then
  echo "==> [restore] Cancelado pelo usuário. Nada foi alterado."
  exit 0
fi

echo "==> [restore] Restaurando backup no site '${SITE_NAME}'..."
docker compose -f compose.yaml --env-file .env exec -T backend \
  bench --site "${SITE_NAME}" restore "${BACKUP_FILE}" \
    --mariadb-root-password "${DB_ROOT_PASSWORD}"

echo "==> [restore] Rodando migrate pós-restauração..."
docker compose -f compose.yaml --env-file .env exec -T backend \
  bench --site "${SITE_NAME}" migrate

echo "==> [restore] Restauração concluída."
