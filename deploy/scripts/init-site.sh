#!/usr/bin/env bash
# =============================================================================
# init-site.sh — Sobe a stack e prepara o site SGC do zero (idempotente).
#
# Passos:
#   1. Valida .env e se o Docker está rodando.
#   2. Sobe os containers (docker compose up -d).
#   3. Cria o site (bench new-site) SOMENTE se ainda não existir.
#   4. Instala erpnext e coaph_contract_ops no site.
#   5. Roda migrate.
#
# É seguro rodar várias vezes: se o site já existe, não recria nem perde dados.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${DEPLOY_DIR}"

# --- 1. Validações --------------------------------------------------------
if [[ ! -f .env ]]; then
  echo "ERRO: arquivo .env não encontrado. Copie de .env.example e edite os valores."
  exit 1
fi
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${SITE_NAME:?defina SITE_NAME no .env}"
: "${ADMIN_PASSWORD:?defina ADMIN_PASSWORD no .env}"
: "${DB_ROOT_PASSWORD:?defina DB_ROOT_PASSWORD no .env}"

if [[ "${ADMIN_PASSWORD}" == "change-me" || "${DB_ROOT_PASSWORD}" == "change-me" ]]; then
  echo "ERRO: senhas ainda estão como 'change-me' no .env. Troque por senhas reais."
  exit 1
fi

echo "==> [init] Verificando se o Docker está em execução..."
if ! docker info >/dev/null 2>&1; then
  echo "ERRO: Docker não está acessível. Inicie o serviço Docker e tente novamente."
  exit 1
fi

COMPOSE=(docker compose -f compose.yaml --env-file .env)

# --- 2. Sobe a stack ------------------------------------------------------
echo "==> [init] Subindo containers..."
"${COMPOSE[@]}" up -d

echo "==> [init] Aguardando o serviço backend ficar disponível..."
# Espera o backend conseguir executar um comando bench simples.
for i in $(seq 1 30); do
  if "${COMPOSE[@]}" exec -T backend bench version >/dev/null 2>&1; then
    break
  fi
  echo "    ... aguardando backend (tentativa ${i}/30)"
  sleep 5
done

# --- 3. Cria o site (se não existir) -------------------------------------
echo "==> [init] Verificando se o site '${SITE_NAME}' já existe..."
if "${COMPOSE[@]}" exec -T backend test -f "sites/${SITE_NAME}/site_config.json"; then
  echo "==> [init] Site '${SITE_NAME}' já existe. Pulando criação."
else
  echo "==> [init] Criando site '${SITE_NAME}'..."
  "${COMPOSE[@]}" exec -T backend \
    bench new-site "${SITE_NAME}" \
      --admin-password "${ADMIN_PASSWORD}" \
      --mariadb-root-password "${DB_ROOT_PASSWORD}" \
      --no-mariadb-socket \
      --install-app erpnext
  echo "==> [init] Site criado com ERPNext instalado."
fi

# --- 4. Instala coaph_contract_ops (idempotente) -------------------------
echo "==> [init] Garantindo que erpnext e coaph_contract_ops estejam instalados..."
INSTALLED="$("${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" list-apps 2>/dev/null || true)"

if ! echo "${INSTALLED}" | grep -qw erpnext; then
  echo "==> [init] Instalando erpnext..."
  "${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" install-app erpnext
else
  echo "==> [init] erpnext já instalado."
fi

if ! echo "${INSTALLED}" | grep -qw coaph_contract_ops; then
  echo "==> [init] Instalando coaph_contract_ops..."
  "${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" install-app coaph_contract_ops
else
  echo "==> [init] coaph_contract_ops já instalado."
fi

# --- 5. Migrate -----------------------------------------------------------
echo "==> [init] Rodando migrate..."
"${COMPOSE[@]}" exec -T backend bench --site "${SITE_NAME}" migrate

echo "==> [init] Concluído. Acesse:  http://localhost:${HTTP_PORT:-8081}"
echo "==> [init] Usuário: Administrator  |  Senha: (a definida em ADMIN_PASSWORD)"
