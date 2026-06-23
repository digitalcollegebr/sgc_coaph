# SGC COAPH — Gestão 360 de Contratos

Sistema de **Gestão 360 de Contratos** da COAPH, construído sobre **ERPNext** e
**Frappe** (version-15) com um app customizado Frappe chamado
`coaph_contract_ops` (módulo **COAPH ContractOps**).

> **Aviso importante**
> - Projeto **interno** da COAPH.
> - **Não** contém dados reais — todos os exemplos (contratantes, unidades,
>   cooperados, valores em R$) são **fictícios** e servem apenas para demonstração.
> - **Sem fork** do ERPNext/Frappe e **sem alteração do core**: toda a
>   customização vive no app `coaph_contract_ops` (DocTypes próprios, workflows,
>   roles, workspace e, no futuro, Custom Fields via fixtures).

---

## 1. Objetivo

Centralizar e governar o **ciclo de vida completo** de um contrato da COAPH —
da **Oportunidade** até o **Encerramento** — passando pela **Mobilização
Contratual**, pela **Operação** e pelo **Ciclo Mensal de Medição** (Produção →
Validação da Produção → Faturamento → Recebimento → Repasse aos Cooperados).

O conceito central é o **Contrato 360**: um único registro que conecta a parte
comercial, jurídica, de mobilização, operacional e financeira do contrato,
fornecendo indicadores de **Saúde do Contrato**, **Risco Contratual** e
**Pendência Contratual** em um **Cockpit Executivo**.

### O que o sistema entrega

- Funil comercial (Oportunidade → Análise de Viabilidade → Disputa/Proposta →
  Formalização Contratual).
- **Contrato 360** como entidade central de governança.
- **Mobilização Contratual** estruturada em plano e etapas (substitui o termo
  "implantação").
- **Ciclo Mensal de Medição** recorrente com Produção, Faturamento, Recebimento
  e **Repasse aos Cooperados** com **Demonstrativo de Repasse**.
- Governança contínua: Ocorrências, Pendências, Riscos, SLA, Aditivos,
  **Renovação Contratual** e Encerramento.
- **Credenciamento de Cooperados** e **Onboarding Cooperativo**.

---

## 2. Arquitetura (visão em texto)

```
                 ┌───────────────────────────────────────────────┐
                 │            BUILD (FORA do servidor)            │
                 │  ERPNext (v15) + Frappe (v15) + coaph_contract │
                 │            _ops  →  imagem Docker               │
                 └──────────────────────┬────────────────────────┘
                                        │ docker push
                                        ▼
                 ┌───────────────────────────────────────────────┐
                 │   Docker Hub  →  coaph/sgc-erpnext:<tag>        │
                 └──────────────────────┬────────────────────────┘
                                        │ docker compose pull
                                        ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │                       SERVIDOR UBUNTU (produção)                        │
   │                                                                         │
   │   nginx ──► backend (Frappe/ERPNext) ──► MariaDB 10.6                   │
   │     :8081        + websocket (9000)   ──► Redis (cache)                 │
   │                                       ──► Redis (queue)                 │
   │                  + worker + scheduler                                   │
   │                                                                         │
   │   App de negócio: coaph_contract_ops (módulo "COAPH ContractOps")       │
   └───────────────────────────────────────────────────────────────────────┘
```

- **ERPNext oficial + Frappe oficial** (version-15) como dependências.
- App customizado `coaph_contract_ops` empacotado na imagem.
- **Deploy "build-fora"**: a imagem é construída em uma máquina de build,
  publicada no Docker Hub (namespace placeholder `coaph/sgc-erpnext`) e o
  servidor Ubuntu apenas faz `docker compose pull` + `up -d`.
- **HTTP_PORT=8081** (a porta 8080 já está ocupada no servidor).
- **Timezone**: `America/Fortaleza`.
- **MariaDB 10.6** e **Redis** rodam em containers.

Detalhes completos em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) e
[`docs/DEPLOY_UBUNTU_DOCKER.md`](docs/DEPLOY_UBUNTU_DOCKER.md).

---

## 3. Estrutura do repositório

```
coaph_contract_ops/
├── apps/
│   └── coaph_contract_ops/        # App Frappe (módulo "COAPH ContractOps")
├── deploy/
│   ├── compose.yaml               # Stack Docker Compose
│   ├── .env.example               # Variáveis de ambiente (modelo)
│   ├── apps.example.json          # Apps a incluir no build da imagem
│   ├── Containerfile              # Definição da imagem customizada
│   └── scripts/                   # build.sh, push.sh, pull.sh, init-site.sh,
│                                  # install-app.sh, migrate.sh, seed-demo.sh,
│                                  # backup.sh, restore.sh, update.sh, logs.sh
├── docs/                          # Documentação (este conjunto de arquivos)
├── backups/                       # Destino local de backups
└── README.md
```

---

## 4. Como instalar (resumo)

A instalação completa em servidor Ubuntu está descrita em
[`docs/DEPLOY_UBUNTU_DOCKER.md`](docs/DEPLOY_UBUNTU_DOCKER.md). Em resumo:

1. **Na máquina de build** (fora do servidor):
   ```bash
   cd deploy
   ./scripts/build.sh        # constrói coaph/sgc-erpnext:<tag>
   ./scripts/push.sh         # publica no Docker Hub
   ```
2. **No servidor Ubuntu**:
   ```bash
   cp .env.example .env      # editar e trocar TODAS as senhas "change-me"
   ./scripts/pull.sh         # docker compose pull
   docker compose up -d      # sobe a stack
   ./scripts/init-site.sh    # cria o site
   ./scripts/install-app.sh  # instala ERPNext + coaph_contract_ops
   ./scripts/migrate.sh      # aplica migrações
   ```

---

## 5. Como rodar

Após a stack estar de pé, acesse:

```
http://<host-do-servidor>:8081
```

Faça login com o usuário `Administrator` (senha definida em `ADMIN_PASSWORD` no
`.env`). O workspace principal é **"SGC COAPH"**, que abre o **Cockpit
Executivo**.

Comandos de operação úteis (scripts em `deploy/scripts/`):

| Ação                | Script         |
|---------------------|----------------|
| Ver logs            | `./logs.sh`    |
| Migrar              | `./migrate.sh` |
| Backup              | `./backup.sh`  |
| Restore             | `./restore.sh` |
| Atualizar versão    | `./update.sh`  |

---

## 6. Como carregar dados de demonstração

Os dados demo são **fictícios** e servem para apresentar o fluxo completo.

Via script de deploy:

```bash
cd deploy
./scripts/seed-demo.sh
```

Ou diretamente via `bench` dentro do container backend:

```bash
bench --site sgc.localhost execute \
  coaph_contract_ops.scripts.seed_demo_data.execute
```

Isso cria contratantes, unidades de atendimento, um **Contrato 360** de exemplo,
plano de **Mobilização Contratual**, um **Ciclo Mensal de Medição** com Produção
e o **Repasse aos Cooperados** correspondente.

Roteiro de demonstração passo a passo em
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 7. Principais módulos

| Módulo                    | Responsabilidade                                            |
|---------------------------|-------------------------------------------------------------|
| Comercial                 | Oportunidade, Análise de Viabilidade, Disputa/Proposta      |
| Jurídico                  | Formalização Contratual, Aditivos, Renovação Contratual     |
| Contrato 360              | Entidade central, serviços contratados, Saúde do Contrato   |
| Mobilização Contratual    | Plano e etapas de mobilização, cooperados mobilizados       |
| Operação                  | Operação Assistida e Operação Regular, Ocorrências, SLA     |
| Ciclo Mensal de Medição   | Produção, Validação da Produção                             |
| Financeiro                | Faturamento, Recebimento, Repasse e Demonstrativo de Repasse|
| RH / Cooperados           | Credenciamento de Cooperados, Onboarding Cooperativo        |
| Governança                | Riscos, Pendências, Renovação, Encerramento                 |

---

## 8. Próximos passos

- Implementar os DocTypes descritos em [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md).
- Configurar workflows nativos Frappe ([`docs/WORKFLOWS.md`](docs/WORKFLOWS.md)).
- Aplicar a matriz de permissões ([`docs/PERMISSIONS.md`](docs/PERMISSIONS.md)).
- Evoluir conforme o [`docs/ROADMAP.md`](docs/ROADMAP.md) (assinatura digital,
  WhatsApp, e-mail, Power BI, portal do cooperado, IA, integração com o
  financeiro nativo do ERPNext).

---

## 9. Documentação

| Documento                                            | Conteúdo                                             |
|------------------------------------------------------|------------------------------------------------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)              | Decisões e componentes da arquitetura                |
| [DATA_MODEL.md](docs/DATA_MODEL.md)                  | DocTypes, campos e relacionamentos                   |
| [WORKFLOWS.md](docs/WORKFLOWS.md)                    | Estados e transições dos workflows                   |
| [PERMISSIONS.md](docs/PERMISSIONS.md)                | Roles e matriz de permissões                         |
| [DEPLOY_UBUNTU_DOCKER.md](docs/DEPLOY_UBUNTU_DOCKER.md)| Deploy em Ubuntu com Docker                          |
| [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)                | Roteiro de demonstração                              |
| [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)| Plano POC / MVP / Produção                           |
| [ROADMAP.md](docs/ROADMAP.md)                        | Melhorias futuras                                    |
