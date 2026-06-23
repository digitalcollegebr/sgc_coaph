# Arquitetura — SGC COAPH (Gestão 360 de Contratos)

Este documento descreve as decisões arquiteturais do **SGC COAPH**, a plataforma
de **Gestão 360 de Contratos** da COAPH.

---

## 1. Decisão arquitetural (resumo)

| Decisão                         | Escolha                                                        |
|---------------------------------|---------------------------------------------------------------|
| Plataforma base                 | **ERPNext** + **Frappe** oficiais, version-15                  |
| Estratégia de customização      | **App customizado** `coaph_contract_ops` (sem fork, sem core)  |
| Empacotamento                   | **Imagem Docker customizada** (ERPNext + app)                  |
| Distribuição                    | **Docker Hub** (`coaph/sgc-erpnext`)                           |
| Deploy no servidor              | `docker compose pull` + `up -d` (build feito **fora**)         |
| Banco de dados                  | **MariaDB 10.6** (container)                                   |
| Cache / fila                    | **Redis** (containers separados para cache e queue)           |
| Porta HTTP                      | **8081** (8080 ocupada no servidor)                           |
| Timezone                        | **America/Fortaleza**                                          |

---

## 2. Por que ERPNext / Frappe

- **Modelo de dados declarativo (DocTypes)**: criar entidades como Contrato 360,
  Ciclo Mensal de Medição e Repasse aos Cooperados é configuração + metadados, o
  que acelera a entrega.
- **Workflows nativos**: estados e transições por papel já existem na plataforma,
  cobrindo o funil comercial, a Mobilização Contratual e o Ciclo Mensal.
- **Sistema de permissões granular**: roles, permissões por DocType e por campo,
  além de regras de compartilhamento — essencial para isolar dados financeiros
  sensíveis.
- **Relatórios, dashboards e workspace**: number cards e charts permitem montar o
  **Cockpit Executivo** sem desenvolvimento pesado de front-end.
- **Base ERP madura**: futuramente integramos com os DocTypes nativos
  (Customer, Supplier, Sales Invoice, Payment Entry, Project) sem reinventar o
  financeiro.
- **Open source e self-hosted**: alinhado a um projeto interno com controle de
  dados próprio.

---

## 3. Por que NÃO fazer fork

- **Atualizações**: manter um fork sincronizado com upstream (version-15 e
  futuras) é custoso e arriscado. Um app separado segue as versões oficiais.
- **Suporte e comunidade**: a plataforma permanece "vanilla" — patches,
  correções de segurança e documentação oficial continuam válidos.
- **Isolamento de responsabilidade**: toda a lógica de negócio da COAPH vive em
  `coaph_contract_ops`. O core ERPNext/Frappe é tratado como dependência
  imutável.
- **Extensão correta**: customizações que toquem DocTypes nativos serão feitas
  por **Custom Field** e **Property Setter** distribuídos como **fixtures** no
  app — nunca editando arquivos do core.

> **Regra de ouro:** nada é alterado dentro de `apps/frappe` ou `apps/erpnext`.
> Tudo o que é COAPH está em `apps/coaph_contract_ops`.

---

## 4. Módulos da aplicação

O app expõe um único módulo Frappe — **COAPH ContractOps** — organizado
logicamente nos seguintes blocos funcionais:

| Bloco                      | DocTypes principais                                                  |
|----------------------------|---------------------------------------------------------------------|
| Cadastros                  | `contratante_coaph`, `unidade_atendimento`                          |
| Comercial                  | `oportunidade_coaph`, `analise_viabilidade`, `disputa_proposta_coaph`|
| Jurídico                   | `formalizacao_contratual`, `aditivo_contratual`, `renovacao_contratual`|
| Contrato                   | `contrato_360`, `servico_contratado`                               |
| Mobilização                | `plano_mobilizacao`, `etapa_mobilizacao`, `cooperado_mobilizado`    |
| Ciclo Mensal de Medição    | `ciclo_mensal_medicao`, `item_producao`                            |
| Financeiro                 | `faturamento_coaph`, `recebimento_coaph`, `repasse_cooperados`, `item_repasse`|
| Governança                 | `ocorrencia_contratual`, `risco_contratual`, `pendencia_contratual` |

O modelo de dados completo está em [`DATA_MODEL.md`](DATA_MODEL.md).

---

## 5. Componentes de infraestrutura

| Componente        | Função                                                            |
|-------------------|------------------------------------------------------------------|
| `nginx`           | Servidor web / proxy reverso, expõe a porta **8081**             |
| `backend`         | Processo Frappe/ERPNext (gunicorn)                               |
| `websocket`       | Socket.IO (porta interna 9000) para realtime                     |
| `worker`          | Processamento de jobs em background                              |
| `scheduler`       | Tarefas agendadas (abertura/encerramento de competência, alertas)|
| `db` (MariaDB 10.6)| Banco de dados do site                                          |
| `redis-cache`     | Cache                                                            |
| `redis-queue`     | Fila de jobs                                                     |

Todos definidos em `deploy/compose.yaml` e parametrizados por `deploy/.env`.

---

## 6. Automações previstas (app)

Implementadas no app `coaph_contract_ops` (server scripts / hooks / scheduler),
sem tocar o core:

- **Cálculo da Saúde do Contrato**: indicador derivado de SLA, Pendências,
  Riscos e situação financeira do Contrato 360.
- **Recalcular Risco Contratual**: reavaliação periódica do nível de Risco
  Contratual (inclusive proximidade de vencimento → Renovação Contratual).
- **Abertura automática do Ciclo Mensal de Medição** por competência para cada
  Contrato 360 ativo (scheduler mensal).
- **Cálculo do Repasse aos Cooperados** a partir da Produção validada e dos
  parâmetros do contrato.
- **Geração do Demonstrativo de Repasse** por cooperado.
- **Alertas e notificações** (log/checklist/histórico) de: etapas de Mobilização
  atrasadas, Faturamento pendente, Recebimento em atraso, Renovação Contratual
  próxima do prazo e Pendências Contratuais vencidas.
- **Validações de transição** nos workflows (ex.: não validar Produção com itens
  inconsistentes; não emitir Faturamento sem Validação da Produção).
- **Atualização de status do Contrato 360** a partir das fases (Mobilização →
  Operação Liberada → Operação Regular → Renovação/Encerramento).

---

## 7. Workspace e Cockpit Executivo

- Workspace principal: **"SGC COAPH"**.
- **Cockpit Executivo**: number cards (contratos ativos, em Mobilização,
  faturamento do mês, recebimento do mês, repasses pendentes, riscos altos,
  pendências abertas) + charts (evolução de Produção/Faturamento/Recebimento,
  Saúde do Contrato, funil comercial).
- Atalhos para os módulos (Comercial, Contrato 360, Mobilização, Ciclo Mensal,
  Financeiro, Governança, Cooperados).

---

## 8. Limites da primeira versão (escopo)

A primeira versão **não** inclui (ver [`ROADMAP.md`](ROADMAP.md)):

- Integração financeira com DocTypes nativos do ERPNext (Sales Invoice, Payment
  Entry, Project) — o Faturamento/Recebimento/Repasse são DocTypes próprios nesta
  fase.
- Assinatura digital de contratos.
- Integração com WhatsApp / e-mail transacional externo.
- Portal do cooperado (autoatendimento).
- Power BI / BI externo.
- IA para análise contratual e previsão de risco de renovação.
- Importação em massa via planilhas (além do `seed_demo_data`).
- HTTPS no servidor (previsto como próximo passo de produção).
