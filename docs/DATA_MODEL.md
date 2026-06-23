# Modelo de Dados — SGC COAPH

Este documento lista os **DocTypes** do app `coaph_contract_ops` (módulo
**COAPH ContractOps**), com campos principais, relacionamentos e child tables.

Convenções:

- **Nome técnico** sem acento (ex.: `contrato_360`); **label** em PT-BR.
- **Link** = campo que referencia outro DocType.
- **Child Table** = tabela filha embutida no documento pai.
- Valores monetários em **R$**; datas no formato **DD/MM/AAAA**;
  identificadores fiscais como **CNPJ/CPF** (todos os exemplos são fictícios).

---

## 1. Visão geral dos relacionamentos

```
contratante_coaph ──< unidade_atendimento
        │
        └──< oportunidade_coaph ──1 analise_viabilidade
                     │
                     └──1 disputa_proposta_coaph ──1 formalizacao_contratual
                                                            │
                                                            ▼
                                                      contrato_360  (CENTRAL)
                                                            │
        ┌──────────────┬──────────────┬──────────────┬──────┴───────┬───────────────┐
        ▼              ▼              ▼              ▼              ▼               ▼
 servico_contratado  plano_      ciclo_mensal_   ocorrencia_   risco_         renovacao_
   (child)           mobilizacao   medicao        contratual    contratual     contratual
                         │             │                                       aditivo_
                  etapa_mobilizacao  item_producao (child)                     contratual
                    (child)           │                                        pendencia_
                  cooperado_         faturamento_coaph ──1 recebimento_coaph    contratual
                   mobilizado         │
                                    repasse_cooperados ──< item_repasse (child)
```

---

## 2. Cadastros

### `contratante_coaph` — Contratante
Entidade que contrata a COAPH (ex.: prefeitura, secretaria, hospital).

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `nome_contratante`   | Data        | Razão social / nome do órgão             |
| `cnpj`               | Data        | CNPJ (fictício)                          |
| `tipo_contratante`   | Select      | Público / Privado / Misto                |
| `esfera`             | Select      | Municipal / Estadual / Federal           |
| `responsavel_legal`  | Data        | Nome do responsável                      |
| `contato_email`      | Data        | E-mail de contato                        |
| `contato_telefone`   | Data        | Telefone                                 |
| `endereco`           | Small Text  | Endereço completo                        |
| `situacao`           | Select      | Ativo / Inativo                          |

Relacionamentos: pai de `unidade_atendimento`; referenciado por
`oportunidade_coaph` e `contrato_360`.

### `unidade_atendimento` — Unidade de Atendimento
Local físico onde o serviço é prestado (ex.: UPA, UBS, hospital).

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `nome_unidade`       | Data        | Nome da unidade                          |
| `contratante`        | Link        | → `contratante_coaph`                    |
| `tipo_unidade`       | Select      | UPA / UBS / Hospital / Pronto Atendimento|
| `municipio`          | Data        | Município                                |
| `endereco`           | Small Text  | Endereço                                 |
| `capacidade`         | Int         | Capacidade/leitos (referência)           |
| `situacao`           | Select      | Ativa / Inativa                          |

Relacionamentos: filha de `contratante_coaph`; referenciada por
`servico_contratado` e `item_producao`.

---

## 3. Comercial

### `oportunidade_coaph` — Oportunidade
Início do funil comercial.

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `titulo`             | Data        | Identificação da oportunidade            |
| `contratante`        | Link        | → `contratante_coaph`                    |
| `origem`             | Select      | Edital / Convite / Indicação / Renovação |
| `objeto`             | Small Text  | Objeto resumido                          |
| `valor_estimado`     | Currency    | R$ estimado                              |
| `data_identificacao` | Date        | DD/MM/AAAA                               |
| `prazo_estimado`     | Int         | Meses                                    |
| `responsavel_comercial`| Link      | → User                                   |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

### `analise_viabilidade` — Análise de Viabilidade

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `oportunidade`       | Link        | → `oportunidade_coaph`                    |
| `viabilidade_tecnica`| Select      | Alta / Média / Baixa                     |
| `viabilidade_financeira`| Select   | Alta / Média / Baixa                     |
| `margem_estimada`    | Percent     | % estimado                               |
| `riscos_identificados`| Text       | Descrição                                |
| `parecer`            | Select      | Favorável / Favorável c/ ressalvas / Desfavorável |
| `data_parecer`       | Date        | DD/MM/AAAA                               |

### `disputa_proposta_coaph` — Disputa / Proposta

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `oportunidade`       | Link        | → `oportunidade_coaph`                    |
| `modalidade`         | Select      | Pregão / Concorrência / Dispensa / Privada|
| `numero_processo`    | Data        | Nº do processo/edital                     |
| `valor_proposto`     | Currency    | R$ proposto                              |
| `data_sessao`        | Date        | DD/MM/AAAA                               |
| `resultado`          | Select      | Vencedora / Perdida / Em análise         |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

---

## 4. Jurídico / Formalização

### `formalizacao_contratual` — Formalização Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `disputa_proposta`   | Link        | → `disputa_proposta_coaph`               |
| `contratante`        | Link        | → `contratante_coaph`                     |
| `numero_contrato`    | Data        | Nº do contrato                           |
| `data_assinatura`    | Date        | DD/MM/AAAA                               |
| `vigencia_inicio`    | Date        | DD/MM/AAAA                               |
| `vigencia_fim`       | Date        | DD/MM/AAAA                               |
| `valor_global`       | Currency    | R$ global                                |
| `clausulas_criticas` | Text        | Resumo de cláusulas                      |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

Relacionamento: dá origem ao `contrato_360`.

---

## 5. Contrato 360 (central)

### `contrato_360` — Contrato 360
Entidade **central** de governança que conecta todos os blocos.

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `titulo`             | Data        | Nome do contrato                         |
| `contratante`        | Link        | → `contratante_coaph`                     |
| `formalizacao`       | Link        | → `formalizacao_contratual`              |
| `numero_contrato`    | Data        | Nº do contrato                           |
| `vigencia_inicio`    | Date        | DD/MM/AAAA                               |
| `vigencia_fim`       | Date        | DD/MM/AAAA                               |
| `valor_global`       | Currency    | R$ global                                |
| `valor_mensal`       | Currency    | R$ mensal de referência                  |
| `fase`               | Select      | Mobilização / Operação Assistida / Operação Regular / Renovação / Encerramento |
| `saude_contrato`     | Select      | Saudável / Atenção / Crítico (calculado) |
| `nivel_risco`        | Select      | Baixo / Médio / Alto (calculado)         |
| `gestor_contrato`    | Link        | → User (SGC Operação)                    |
| `servicos`           | Child Table | → `servico_contratado`                    |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

Relacionamentos: referenciado por `plano_mobilizacao`,
`ciclo_mensal_medicao`, `ocorrencia_contratual`, `risco_contratual`,
`pendencia_contratual`, `renovacao_contratual`, `aditivo_contratual`.

### `servico_contratado` (child de `contrato_360`) — Serviço Contratado

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `descricao_servico`  | Data        | Descrição                                |
| `unidade_atendimento`| Link        | → `unidade_atendimento`                   |
| `tipo_medicao`       | Select      | Plantão / Procedimento / Posto / Pacote  |
| `quantidade`         | Float       | Quantidade contratada                    |
| `valor_unitario`     | Currency    | R$ unitário                              |
| `valor_total`        | Currency    | R$ total (calculado)                     |

---

## 6. Mobilização Contratual

### `plano_mobilizacao` — Plano de Mobilização

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `data_inicio`        | Date        | DD/MM/AAAA                               |
| `data_prevista_fim`  | Date        | DD/MM/AAAA                               |
| `responsavel`        | Link        | → User (SGC Mobilização)                  |
| `percentual_concluido`| Percent    | % (calculado pelas etapas)               |
| `etapas`             | Child Table | → `etapa_mobilizacao`                      |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

### `etapa_mobilizacao` (child de `plano_mobilizacao`) — Etapa de Mobilização

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `nome_etapa`         | Data        | Ex.: Documentação, Credenciamento, Insumos|
| `responsavel`        | Link        | → User                                   |
| `data_prevista`      | Date        | DD/MM/AAAA                               |
| `data_conclusao`     | Date        | DD/MM/AAAA                               |
| `status`             | Select      | Pendente / Em andamento / Concluída / Atrasada |
| `checklist`          | Text        | Itens de verificação                     |

### `cooperado_mobilizado` — Cooperado Mobilizado
Vincula cooperados à Mobilização Contratual (Credenciamento / Onboarding
Cooperativo).

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `plano_mobilizacao`  | Link        | → `plano_mobilizacao`                      |
| `nome_cooperado`     | Data        | Nome (fictício)                          |
| `cpf`                | Data        | CPF (fictício)                           |
| `categoria`          | Select      | Médico / Enfermagem / Técnico / Apoio    |
| `unidade_atendimento`| Link        | → `unidade_atendimento`                    |
| `status_credenciamento`| Select    | Em análise / Credenciado / Recusado      |
| `status_onboarding`  | Select      | Pendente / Concluído                     |
| `data_inicio`        | Date        | DD/MM/AAAA                               |

---

## 7. Ciclo Mensal de Medição

### `ciclo_mensal_medicao` — Ciclo Mensal de Medição

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `competencia`        | Data        | MM/AAAA                                  |
| `data_abertura`      | Date        | DD/MM/AAAA                               |
| `data_fechamento`    | Date        | DD/MM/AAAA                               |
| `producao_total`     | Currency    | R$ de Produção (calculado)               |
| `status`             | Select      | Aberta / Produção / Validada / Encerrada |
| `itens_producao`     | Child Table | → `item_producao`                         |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

### `item_producao` (child de `ciclo_mensal_medicao`) — Item de Produção

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `unidade_atendimento`| Link        | → `unidade_atendimento`                    |
| `descricao`          | Data        | Serviço/procedimento medido              |
| `quantidade`         | Float       | Quantidade produzida                     |
| `valor_unitario`     | Currency    | R$ unitário                              |
| `valor_total`        | Currency    | R$ total (calculado)                     |
| `conferido`          | Check       | Marcado na conferência                   |

---

## 8. Financeiro

### `faturamento_coaph` — Faturamento

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `ciclo`              | Link        | → `ciclo_mensal_medicao`                  |
| `contrato`           | Link        | → `contrato_360`                          |
| `numero_nota`        | Data        | Nº da nota / fatura                      |
| `data_emissao`       | Date        | DD/MM/AAAA                               |
| `data_vencimento`    | Date        | DD/MM/AAAA                               |
| `valor_bruto`        | Currency    | R$ bruto                                 |
| `impostos`           | Currency    | R$ de impostos                           |
| `valor_liquido`      | Currency    | R$ líquido (calculado)                   |
| `status`             | Select      | Emitido / Parcial / Pago / Cancelado     |

### `recebimento_coaph` — Recebimento

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `faturamento`        | Link        | → `faturamento_coaph`                      |
| `data_recebimento`   | Date        | DD/MM/AAAA                               |
| `valor_recebido`     | Currency    | R$ recebido                              |
| `forma`              | Select      | Transferência / Empenho / Boleto         |
| `status`             | Select      | Baixado / Parcial / Em atraso            |

### `repasse_cooperados` — Repasse aos Cooperados

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `ciclo`              | Link        | → `ciclo_mensal_medicao`                  |
| `contrato`           | Link        | → `contrato_360`                          |
| `competencia`        | Data        | MM/AAAA                                  |
| `valor_total_repasse`| Currency    | R$ total (calculado)                     |
| `data_repasse`       | Date        | DD/MM/AAAA                               |
| `status`             | Select      | Calculado / Demonstrativos publicados / Executado |
| `itens`              | Child Table | → `item_repasse`                          |

### `item_repasse` (child de `repasse_cooperados`) — Item de Repasse / Demonstrativo de Repasse

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `cooperado`          | Data        | Nome do cooperado (fictício)             |
| `cpf`                | Data        | CPF (fictício)                           |
| `producao_associada` | Currency    | R$ de Produção do cooperado              |
| `descontos`          | Currency    | R$ de descontos                          |
| `valor_liquido`      | Currency    | R$ líquido do repasse (calculado)        |
| `demonstrativo`      | Attach      | PDF do Demonstrativo de Repasse          |

---

## 9. Governança

### `ocorrencia_contratual` — Ocorrência Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `tipo`               | Select      | Operacional / Financeira / Jurídica / SLA|
| `descricao`          | Text        | Descrição                                |
| `data_ocorrencia`    | Date        | DD/MM/AAAA                               |
| `gravidade`          | Select      | Baixa / Média / Alta                     |
| `status`             | Select      | Aberta / Em tratamento / Resolvida       |

### `risco_contratual` — Risco Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `descricao_risco`    | Text        | Descrição                                |
| `probabilidade`      | Select      | Baixa / Média / Alta                     |
| `impacto`            | Select      | Baixo / Médio / Alto                     |
| `nivel`              | Select      | Baixo / Médio / Alto (calculado)         |
| `plano_mitigacao`    | Text        | Ações de mitigação                       |
| `status`             | Select      | Identificado / Em mitigação / Mitigado   |

### `pendencia_contratual` — Pendência Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `descricao`          | Text        | Descrição                                |
| `responsavel`        | Link        | → User                                   |
| `prazo`              | Date        | DD/MM/AAAA                               |
| `prioridade`         | Select      | Baixa / Média / Alta                     |
| `status`             | Select      | Aberta / Em andamento / Concluída / Vencida |

### `renovacao_contratual` — Renovação Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `vigencia_atual_fim` | Date        | DD/MM/AAAA                               |
| `nova_vigencia_fim`  | Date        | DD/MM/AAAA                               |
| `reajuste`           | Percent     | % de reajuste                            |
| `recomendacao`       | Select      | Renovar / Renegociar / Encerrar          |
| `estado_workflow`    | Select      | (gerido pelo workflow)                   |

### `aditivo_contratual` — Aditivo Contratual

| Campo                | Tipo        | Observações                              |
|----------------------|-------------|------------------------------------------|
| `contrato`           | Link        | → `contrato_360`                          |
| `tipo_aditivo`       | Select      | Prazo / Valor / Escopo / Reequilíbrio    |
| `descricao`          | Text        | Descrição                                |
| `valor_impacto`      | Currency    | R$ de impacto                            |
| `data_assinatura`    | Date        | DD/MM/AAAA                               |
| `status`             | Select      | Em elaboração / Assinado / Vigente       |

---

## 10. Integrações futuras com DocTypes nativos ERPNext

> Estas integrações **não** fazem parte da primeira versão. Quando
> implementadas, serão feitas **sem alterar o core**, apenas via **Custom Field**
> e **Property Setter** distribuídos como **fixtures** no app `coaph_contract_ops`.

| DocType nativo  | Uso futuro na COAPH                                                       | Ligação proposta (Custom Field)                       |
|-----------------|--------------------------------------------------------------------------|-------------------------------------------------------|
| **Customer**    | Representar o Contratante no financeiro nativo                            | `contratante_coaph.customer` → Customer               |
| **Supplier**    | Representar o cooperado como prestador para fins de Repasse               | `cooperado_mobilizado.supplier` → Supplier            |
| **Project**     | Espelhar o Contrato 360 como Projeto para acompanhamento e custos         | `contrato_360.project` → Project                      |
| **Sales Invoice**| Substituir/integrar o `faturamento_coaph` no contas a receber nativo     | `faturamento_coaph.sales_invoice` → Sales Invoice     |
| **Payment Entry**| Registrar Recebimento e Repasse no razão financeiro nativo              | `recebimento_coaph.payment_entry`, `repasse_cooperados.payment_entry` → Payment Entry |

Princípios:

- Os DocTypes próprios da COAPH continuam sendo a **fonte de verdade do negócio**;
  os nativos passam a ser o **ledger financeiro**.
- Toda extensão de DocType nativo é versionada como fixture no app.
- Nenhuma migração altera tabelas do core diretamente.
