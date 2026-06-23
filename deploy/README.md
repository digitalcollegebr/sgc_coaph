# SGC COAPH — Gestão 360 de Contratos — Deploy Docker

Infraestrutura de deploy do **SGC COAPH**, baseada em **ERPNext/Frappe oficial
(version-15)** + app customizado **`coaph_contract_ops`**.

> **Estratégia:** a imagem Docker customizada é construída **FORA** do servidor
> (CI ou máquina local), publicada no **Docker Hub** e o servidor de produção
> apenas faz `docker compose pull` + `docker compose up -d`. O servidor **não
> compila nada**. **Não** há fork do core nem alteração do código do
> Frappe/ERPNext — o app custom é instalado por cima da imagem oficial.

---

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Estrutura de arquivos](#estrutura-de-arquivos)
- [Configuração do `.env`](#configuração-do-env)
- [Tabela de portas](#tabela-de-portas)
- [Modo A — POC / Local](#modo-a--poc--local)
- [Modo B — Imagem customizada (produção)](#modo-b--imagem-customizada-produção)
- [Operações do dia a dia](#operações-do-dia-a-dia)
- [Avisos de segurança](#avisos-de-segurança)

---

## Pré-requisitos

- **Servidor:** Ubuntu com Docker Engine e o plugin **Docker Compose v2**
  (comando `docker compose`, **não** `docker-compose`).
- **Build (CI/local):** Docker com `buildx`/`build`, acesso ao GitHub para clonar
  o app e conta no Docker Hub para publicar.
- Acesso de rede de saída para baixar imagens oficiais do Frappe/ERPNext.

Verifique:

```bash
docker --version
docker compose version
```

---

## Estrutura de arquivos

```
deploy/
├── .env.example          # Modelo de variáveis (versionável). Copie para .env.
├── apps.example.json     # Lista de apps p/ build (erpnext + coaph_contract_ops).
├── Containerfile         # Build multi-stage da imagem customizada.
├── compose.yaml          # Stack de produção (usa a imagem publicada).
├── README.md             # Este arquivo.
└── scripts/
    ├── build.sh          # Build da imagem customizada (CI/local).
    ├── push.sh           # Publica a imagem no Docker Hub.
    ├── pull.sh           # Baixa a imagem no servidor.
    ├── init-site.sh      # Sobe stack + cria site + instala apps + migrate.
    ├── install-app.sh    # (Re)instala coaph_contract_ops + migrate + clear-cache.
    ├── migrate.sh        # bench migrate.
    ├── seed-demo.sh      # Carrega dados de demonstração.
    ├── backup.sh         # bench backup --with-files (não apaga antigos).
    ├── restore.sh        # Restaura backup (pede confirmação "sim").
    ├── update.sh         # pull + recria containers + migrate + clear-cache.
    └── logs.sh           # Logs dos containers (serviço opcional).
```

> **`apps.json` em produção:** o arquivo `apps.example.json` é só um modelo.
> Para a build real, copie-o para `apps.json` e garanta que o app
> `coaph_contract_ops` esteja em um **repositório Git acessível** pelo ambiente
> de build (ex.: `git@github.com:SUA_ORG/coaph_contract_ops.git`, branch `main`),
> com as credenciais/SSH configuradas. O Frappe core já vem na imagem base, por
> isso o `apps.json` lista apenas `erpnext` e `coaph_contract_ops`.

---

## Configuração do `.env`

```bash
cd deploy
cp .env.example .env
# Edite .env e troque TODOS os "change-me" por senhas fortes reais.
```

Variáveis principais (ver `.env.example` para a lista completa):

| Variável                  | Descrição                                              |
|---------------------------|--------------------------------------------------------|
| `COMPOSE_PROJECT_NAME`    | Nome do projeto Compose (`coaph_sgc`).                  |
| `SITE_NAME`               | Nome do site Frappe (ex.: `sgc.localhost`).            |
| `FRAPPE_SITE_NAME_HEADER` | Host enviado pelo nginx ao backend (geralmente = site).|
| `ADMIN_PASSWORD`          | Senha do Administrator. **Trocar.**                    |
| `DB_ROOT_PASSWORD`        | Senha root do MariaDB. **Trocar.**                     |
| `DB_PASSWORD`             | Senha do banco do site. **Trocar.**                    |
| `FRAPPE_BRANCH`           | Branch do Frappe (`version-15`). Usada no build.       |
| `ERPNEXT_BRANCH`          | Branch do ERPNext (`version-15`). Usada no build.      |
| `COAPH_APP_BRANCH`        | Branch do app custom (`main`). Usada no build.         |
| `HTTP_PORT`               | Porta HTTP no host (**8081**, pois 8080 está ocupada). |
| `HTTPS_PORT`              | Porta HTTPS no host (**8443**).                        |
| `TIMEZONE`                | Fuso horário (`America/Fortaleza`).                    |
| `CUSTOM_IMAGE`            | Imagem no Docker Hub (`coaph/sgc-erpnext`).            |
| `CUSTOM_TAG`              | Tag da imagem (`latest` ou versão, ex.: `v1.0.0`).     |

---

## Tabela de portas

| Serviço        | Porta no container | Porta no host | Observação                          |
|----------------|--------------------|---------------|-------------------------------------|
| frontend HTTP  | 8080               | **8081**      | 8080 está ocupada no servidor.      |
| frontend HTTPS | 8443               | **8443**      | `HTTPS_PORT`.                       |
| backend        | 8000               | —             | Interno (proxy via frontend).       |
| websocket      | 9000               | —             | Interno (`SOCKETIO_PORT`).          |
| db (MariaDB)   | 3306               | —             | Interno (sem exposição no host).    |
| redis-cache    | 6379               | —             | Interno.                            |
| redis-queue    | 6379               | —             | Interno.                            |

Acesso à aplicação: **http://SEU_SERVIDOR:8081**

---

## Modo A — POC / Local

Sobe a stack, cria o site, instala ERPNext + app custom e (opcional) carrega
dados de demonstração. Útil para validar localmente.

> No modo POC, você pode usar a imagem já publicada (`CUSTOM_IMAGE:CUSTOM_TAG`)
> ou uma imagem construída localmente com `./scripts/build.sh` e marcada com a
> mesma `CUSTOM_TAG`.

```bash
cd deploy
cp .env.example .env          # edite as senhas

# (opcional) construir a imagem localmente, em vez de baixar do Hub:
cp apps.example.json apps.json
./scripts/build.sh

# Sobe tudo, cria o site, instala erpnext + coaph_contract_ops e migra:
./scripts/init-site.sh

# (opcional) dados de demonstração:
./scripts/seed-demo.sh
```

Acesse `http://localhost:8081` — usuário `Administrator`, senha = `ADMIN_PASSWORD`.

`init-site.sh` é **idempotente**: se o site já existir, não recria nem perde dados.

---

## Modo B — Imagem customizada (produção)

### 1. Build (CI ou máquina local — NUNCA no servidor)

```bash
cd deploy
cp .env.example .env          # defina CUSTOM_IMAGE, CUSTOM_TAG e branches
cp apps.example.json apps.json
# Edite apps.json: aponte coaph_contract_ops p/ seu repositório Git real.

# Recomenda-se uma TAG versionada (ex.: v1.0.0) em vez de "latest":
#   CUSTOM_TAG=v1.0.0 no .env

./scripts/build.sh            # gera APPS_JSON_BASE64 e builda a imagem
```

### 2. Publicar no Docker Hub

```bash
docker login                  # faça login (credenciais NÃO ficam em scripts)
./scripts/push.sh             # docker push CUSTOM_IMAGE:CUSTOM_TAG
```

### 3. Atualizar o servidor

No servidor (Ubuntu), com `deploy/.env` configurado (mesmos `CUSTOM_IMAGE`/
`CUSTOM_TAG` publicados):

```bash
cd deploy

# Primeira vez (cria o site):
./scripts/pull.sh
./scripts/init-site.sh

# Atualizações seguintes (nova tag publicada):
#   Atualize CUSTOM_TAG no .env para a nova versão e rode:
./scripts/update.sh           # pull + recria containers + migrate + clear-cache
```

> **Tag versionada:** prefira `CUSTOM_TAG=vX.Y.Z` para deploys rastreáveis e
> rollback fácil (basta apontar o `.env` para a tag anterior e rodar `update.sh`).
> O `update.sh` **preserva os volumes** (não usa `down -v`).

---

## Operações do dia a dia

Todos os comandos `bench` rodam dentro do container `backend` via
`docker compose exec`. Os scripts já encapsulam isso.

| Tarefa                         | Comando                          |
|--------------------------------|----------------------------------|
| Migrar banco                   | `./scripts/migrate.sh`           |
| Instalar/atualizar app custom  | `./scripts/install-app.sh`       |
| Dados de demonstração          | `./scripts/seed-demo.sh`         |
| Backup (banco + arquivos)      | `./scripts/backup.sh`            |
| Restaurar backup (destrutivo)  | `./scripts/restore.sh <arquivo>` |
| Atualizar p/ nova imagem       | `./scripts/update.sh`            |
| Ver logs                       | `./scripts/logs.sh [serviço]`    |

### Backup

`./scripts/backup.sh` roda `bench backup --with-files`. Os arquivos ficam no
volume `sites`, em `sites/${SITE_NAME}/private/backups/`. O script **não apaga**
backups antigos e mostra como copiá-los para o host com `docker cp`.

### Restore

`./scripts/restore.sh <caminho-do-backup>` é **destrutivo** — sobrescreve o
banco atual. O script **exige** que você digite `sim` para confirmar.

---

## Avisos de segurança

- **Nunca** versione o `.env` real. Apenas o `.env.example` (com `change-me`).
- **Troque todas** as senhas `change-me` antes de qualquer ambiente exposto.
  O `init-site.sh` recusa subir se as senhas ainda forem `change-me`.
- **Credenciais ficam fora dos scripts.** O `docker login` é feito manualmente.
- Para a build, use **SSH/credenciais** com acesso de leitura ao repositório do
  app; não embuta tokens no `apps.json` versionado.
- O banco e o Redis **não** são expostos no host — somente o frontend (8081/8443).
- Em produção, coloque um proxy reverso TLS (ex.: Traefik/Nginx) à frente, ou
  configure os certificados, antes de expor publicamente.
```
