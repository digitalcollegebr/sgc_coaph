# Quickstart — Demonstração no Mac (Docker Desktop)

Guia rápido para rodar o **SGC COAPH — Gestão 360 de Contratos** no seu Mac
para demonstrar ao cliente. Funciona em Apple Silicon (M1/M2/M3) e Intel.

> A imagem é construída **localmente** a partir do código (não precisa de imagem
> publicada no Docker Hub). A base `frappe/erpnext:version-15` é multi-arch.

## Pré-requisitos
- **Docker Desktop** instalado e **em execução** (ícone da baleia ativo).
- **Git** com acesso ao repositório.
- Recomendado: Docker Desktop com **≥ 6 GB de RAM** (Settings → Resources).
- Porta **8081** livre no Mac.

## Passo a passo (≈ 3 comandos)

```bash
# 1. Clonar o repositório
git clone git@github.com:digitalcollegebr/sgc_coaph.git
cd sgc_coaph

# 2. Subir tudo (build + stack + site + dados de demo) — um comando
chmod +x deploy/scripts/*.sh
deploy/scripts/demo-up.sh
```

O script cria o `.env` (senhas de demo = `admin`), builda a imagem
`coaph/sgc-erpnext:local`, sobe a stack, cria o site `sgc.localhost`,
instala o app e carrega os dados fictícios. Na primeira vez leva alguns
minutos (download da imagem base).

## Acessar
- **URL:** http://localhost:8081
- **Usuário:** `Administrator`
- **Senha:** `admin`
- **Workspace:** menu lateral → **SGC COAPH** (ou `/app/sgc-coaph`)

## Operação durante a demo

```bash
cd deploy
ALIAS="docker compose -f compose.yaml -f compose.local.yaml --env-file .env"

$ALIAS ps                 # status dos containers
$ALIAS logs -f backend    # logs (Ctrl+C para sair)
$ALIAS stop               # parar (mantém os dados)
$ALIAS start              # religar
```

> ⚠️ **Nunca** use `down -v` — isso apaga os volumes (banco e arquivos).
> Para apenas parar, use `stop`. Os dados ficam nos volumes Docker.

## Recarregar dados de demo (idempotente)
```bash
cd deploy
docker compose -f compose.yaml -f compose.local.yaml --env-file .env \
  exec backend bench --site sgc.localhost \
  execute coaph_contract_ops.scripts.seed_demo_data.execute
```

## Roteiro sugerido de demonstração
Veja [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). Resumo:
1. Abrir o **Cockpit Executivo** (workspace SGC COAPH).
2. Abrir um **Contrato 360** → botões *Criar Plano / Ciclo / Renovação*.
3. Mostrar **Mobilização**, **Ciclo Mensal**, **Faturamento/Recebimento/Repasse**.
4. Rodar relatórios (*Contratos Vencendo*, *Repasses Pendentes*).
5. Mostrar **Renovação/Riscos/Pendências** e a **Saúde do Contrato**.

## Problemas comuns
- **Porta 8081 ocupada:** edite `HTTP_PORT` no `deploy/.env` e rode
  `deploy/scripts/demo-up.sh` de novo.
- **Build lento/erro de memória:** aumente a RAM do Docker Desktop
  (Settings → Resources → Memory).
- **Página em branco / 404:** aguarde ~30s após o `up` (assets/site
  inicializando) e atualize.
