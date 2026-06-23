# Roadmap — SGC COAPH

Melhorias futuras da **Gestão 360 de Contratos**, posteriores ao MVP/Produção
descritos em [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md). Todas seguem o
princípio: **sem fork, sem alterar o core** — extensões via app
`coaph_contract_ops` e fixtures.

---

## 1. Integrações de relacionamento

| Item                         | Descrição                                                                 |
|------------------------------|---------------------------------------------------------------------------|
| **Assinatura digital**       | Assinatura eletrônica da Formalização Contratual, Aditivos e Renovação Contratual, com trilha de auditoria. |
| **WhatsApp**                 | Alertas/notificações (não como etapa) de Pendências, Renovação próxima e Demonstrativo de Repasse disponível. |
| **E-mail**                   | Envio transacional de Demonstrativos de Repasse e relatórios do Ciclo Mensal. |

---

## 2. Análise e BI

| Item                         | Descrição                                                                 |
|------------------------------|---------------------------------------------------------------------------|
| **Power BI**                 | Conexão de leitura para dashboards executivos externos (Saúde do Contrato, Produção, Faturamento x Recebimento, Repasse). |
| **Indicadores avançados**    | Séries históricas de Risco Contratual e desempenho por unidade/contratante. |

---

## 3. Autoatendimento e dados

| Item                         | Descrição                                                                 |
|------------------------------|---------------------------------------------------------------------------|
| **Portal do Cooperado**      | Área (Frappe Portal) para o cooperado acompanhar Credenciamento, Onboarding Cooperativo e seu Demonstrativo de Repasse. |
| **Importação de planilhas**  | Importação em massa de Produção e cadastros (além do `seed_demo_data`), com validação. |

---

## 4. Inteligência artificial

| Item                                 | Descrição                                                         |
|--------------------------------------|------------------------------------------------------------------|
| **IA para análise contratual**       | Leitura assistida de cláusulas na Formalização Contratual e Aditivos, destacando cláusulas críticas. |
| **IA para risco de renovação**       | Previsão de probabilidade de Renovação Contratual com base em histórico de Saúde do Contrato, SLA e Pendências. |

---

## 5. Integração com o financeiro nativo ERPNext

> Migração do financeiro próprio para os DocTypes nativos, mantendo os DocTypes
> COAPH como fonte de verdade do negócio. Sempre via **Custom Field/fixtures**.

| DocType nativo   | Uso                                                              |
|------------------|-----------------------------------------------------------------|
| **Sales Invoice**| Espelhar/substituir `faturamento_coaph` no contas a receber.    |
| **Payment Entry**| Registrar Recebimento e Repasse aos Cooperados no razão.        |
| **Project**      | Espelhar o Contrato 360 como Projeto para custos e prazos.      |
| **Customer**     | Vincular o Contratante ao cadastro nativo.                      |
| **Supplier**     | Vincular o cooperado como prestador para o Repasse.             |

Ver mapeamento de campos em [`DATA_MODEL.md`](DATA_MODEL.md), seção
"Integrações futuras com DocTypes nativos ERPNext".

---

## 6. Operação e infraestrutura

| Item                         | Descrição                                                                 |
|------------------------------|---------------------------------------------------------------------------|
| **HTTPS / TLS**              | Certificado e reverse proxy (próximo passo logo após a Produção inicial). |
| **CI/CD da imagem**          | Pipeline de build/push automatizado por tag versionada.                   |
| **Backup off-site automatizado**| Replicação agendada da pasta `backups/` para nuvem com retenção.       |
| **Observabilidade**          | Métricas e alertas de saúde dos containers.                              |

---

## 7. Priorização sugerida

1. Integração financeira nativa (Sales Invoice, Payment Entry, Project).
2. HTTPS + backup off-site automatizado.
3. E-mail e WhatsApp para Demonstrativos e alertas.
4. Portal do Cooperado.
5. Importação de planilhas.
6. Power BI.
7. Assinatura digital.
8. IA (análise contratual e risco de renovação).
