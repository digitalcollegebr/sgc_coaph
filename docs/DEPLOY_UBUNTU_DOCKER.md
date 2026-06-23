# Deploy em Ubuntu com Docker — SGC COAPH

Guia de implantação do **SGC COAPH** em servidor Ubuntu usando Docker, no modelo
**build-fora + Docker Hub + pull no servidor**.

> A imagem customizada (ERPNext + `coaph_contract_ops`) é construída **fora** do
> servidor de produção, publicada no Docker Hub e o servidor apenas faz
> `docker compose pull` + `up -d`. Isso mantém o servidor leve e o build
> reprodutível.

---

## 1. Pré-requisitos

### Servidor Ubuntu (produção)

| Item              | Recomendação                                  |
|-------------------|-----------------------------------------------|
| SO                | Ubuntu 22.04 LTS (ou superior)                |
| CPU / RAM         | 2 vCPU / 4 GB (mínimo); 4 vCPU / 8 GB (ideal) |
| Disco             | 40 GB+ (dados MariaDB + backups)              |
| Docker Engine     | 24.x ou superior                              |
| Docker Compose    | Plugin v2 (`docker compose`)                  |
| Usuário           | Usuário **não-root** no grupo `docker`        |
| Porta HTTP        | **8081** liberada (8080 está ocupada)         |

### Instalação do Docker (resumo)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Usuário não-root no grupo docker (reentrar na sessão depois)
sudo usermod -aG docker $USER
```

---

## 2. Estrutura de pastas no servidor

```
coaph_contract_ops/
├── deploy/
│   ├── compose.yaml
│   ├── .env                  # criado a partir de .env.example (NÃO versionar)
│   ├── .env.example
│   ├── apps.example.json
│   ├── Containerfile
│   └── scripts/              # build.sh, push.sh, pull.sh, init-site.sh, ...
├── backups/                  # destino dos dumps
└── docs/
```

---

## 3. Variáveis de ambiente (`.env`)

Copie o modelo e edite:

```bash
cd deploy
cp .env.example .env
```

Principais variáveis (todas em `.env.example`):

| Variável                 | Significado                                            |
|--------------------------|--------------------------------------------------------|
| `COMPOSE_PROJECT_NAME`   | Nome do projeto Compose (`coaph_sgc`)                  |
| `SITE_NAME`              | Site Frappe (ex.: `sgc.localhost`)                     |
| `FRAPPE_SITE_NAME_HEADER`| Host enviado pelo nginx ao backend                    |
| `ADMIN_PASSWORD`         | Senha do `Administrator` — **trocar**                  |
| `DB_ROOT_PASSWORD`       | Senha root do MariaDB — **trocar**                     |
| `DB_PASSWORD`            | Senha do banco do site — **trocar**                    |
| `HTTP_PORT`              | **8081** (8080 ocupada)                                |
| `HTTPS_PORT`             | 8443 (uso futuro)                                      |
| `TIMEZONE`               | `America/Fortaleza`                                    |
| `FRAPPE_BRANCH`/`ERPNEXT_BRANCH`| `version-15` (usadas no build)                 |
| `COAPH_APP_BRANCH`       | branch do app (ex.: `main`)                            |
| `CUSTOM_IMAGE`           | `coaph/sgc-erpnext` (Docker Hub)                       |
| `CUSTOM_TAG`             | tag da imagem (ex.: `latest` ou `v1.0.0`)             |

> **Nunca** versione o `.env` real. Troque **todos** os valores `change-me` por
> senhas fortes.

---

## 4. Build fora do servidor + publicação no Docker Hub

Em uma **máquina de build** (notebook/CI), **não** no servidor de produção:

```bash
cd deploy

# 1) Construir a imagem customizada (ERPNext v15 + coaph_contract_ops)
./scripts/build.sh            # usa Containerfile + apps.example.json

# 2) Autenticar e publicar no Docker Hub (namespace coaph/sgc-erpnext)
docker login
./scripts/push.sh             # docker push coaph/sgc-erpnext:<CUSTOM_TAG>
```

Recomenda-se **taguear por versão** (ex.: `v1.0.0`) além de `latest`.

---

## 5. Subir a stack no servidor

No servidor Ubuntu:

```bash
cd deploy

# 1) Baixar a imagem publicada
./scripts/pull.sh             # docker compose pull

# 2) Subir os serviços (nginx, backend, websocket, worker, scheduler, db, redis)
docker compose up -d

# 3) Conferir
docker compose ps
./scripts/logs.sh             # acompanhar logs
```

---

## 6. Criar site, instalar ERPNext e o app, migrar

```bash
cd deploy

# Cria o site (usa SITE_NAME, ADMIN_PASSWORD, DB_*)
./scripts/init-site.sh

# Instala ERPNext + coaph_contract_ops no site
./scripts/install-app.sh

# Aplica migrações (DocTypes, workflows, fixtures de roles/permissões)
./scripts/migrate.sh
```

Acesse: `http://<host>:8081` e faça login como `Administrator`.

---

## 7. Carregar dados de demonstração (fictícios)

```bash
cd deploy
./scripts/seed-demo.sh
```

Equivalente direto via `bench` no container backend:

```bash
docker compose exec backend \
  bench --site sgc.localhost execute \
  coaph_contract_ops.scripts.seed_demo_data.execute
```

---

## 8. Backup

```bash
cd deploy
./scripts/backup.sh           # gera dump (db + arquivos) em ../backups/
```

O script executa, no backend:

```bash
bench --site sgc.localhost backup --with-files
```

e copia os artefatos para a pasta `backups/` do host.

---

## 9. Restore

> Procedimento sensível. Faça **sempre** um backup antes e valide o ambiente.

```bash
cd deploy
./scripts/restore.sh <arquivo-do-backup>
```

Equivalente:

```bash
docker compose exec backend \
  bench --site sgc.localhost restore <caminho-do-sql> \
  --with-public-files <tar> --with-private-files <tar>
```

**Teste o restore periodicamente** em um ambiente separado — backup que nunca
foi restaurado não é backup confiável.

---

## 10. Atualização (update) com tag versionada

Fluxo recomendado para subir uma nova versão:

```bash
# (build) na máquina de build
CUSTOM_TAG=v1.1.0 ./scripts/build.sh
CUSTOM_TAG=v1.1.0 ./scripts/push.sh

# (servidor) atualizar para a nova tag
cd deploy
# editar CUSTOM_TAG=v1.1.0 no .env
./scripts/update.sh
```

`update.sh` faz, em ordem: `backup.sh` → `docker compose pull` →
`docker compose up -d` → `migrate.sh`. Sempre prefira **tags versionadas** a
`latest` em produção para permitir rollback (basta apontar `CUSTOM_TAG` para a
versão anterior e rodar `update.sh`).

---

## 11. Cuidados de produção

- **Usuário não-root**: operar Docker com usuário no grupo `docker`, nunca como
  root direto.
- **Firewall (UFW)**: liberar apenas o necessário (SSH e a porta `8081`).
  ```bash
  sudo ufw allow OpenSSH
  sudo ufw allow 8081/tcp
  sudo ufw enable
  ```
- **HTTPS**: previsto como **próximo passo** (reverse proxy/Traefik ou nginx com
  Let's Encrypt na porta 443/8443). A primeira versão sobe em HTTP na 8081.
- **Backup off-site**: replicar a pasta `backups/` para armazenamento externo
  (objeto/nuvem) com retenção definida.
- **Testar restore**: validar restauração regularmente em ambiente de teste.
- **Segredos**: manter o `.env` fora do Git, com permissões restritas
  (`chmod 600 .env`).
- **Monitoramento**: acompanhar `./scripts/logs.sh` e `docker compose ps`.

> ⚠️ **NUNCA** execute `docker compose down -v` sem confirmação explícita: a flag
> `-v` **remove os volumes** e, com eles, **o banco de dados MariaDB e os
> arquivos do site**. Para parar a stack sem perder dados, use apenas
> `docker compose down` (sem `-v`) ou `docker compose stop`.
