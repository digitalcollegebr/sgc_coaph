# Workflows — SGC COAPH

Workflows **nativos do Frappe** (DocType "Workflow") aplicados aos DocTypes do
app `coaph_contract_ops`. Cada workflow define **estados** (com o role que pode
editar naquele estado) e **transições** (ação, estado origem → destino e o role
que executa).

Roles citados estão detalhados em [`PERMISSIONS.md`](PERMISSIONS.md).

> Convenção: estados de submissão Frappe — `docstatus` 0 = rascunho,
> 1 = submetido, 2 = cancelado. Onde aplicável, o estado final "trava" o
> documento.

---

## 1. Workflow — Oportunidade (`oportunidade_coaph`)

**Estados**

| Estado            | Role responsável  | docstatus |
|-------------------|-------------------|-----------|
| Identificada      | SGC Comercial     | 0         |
| Em Qualificação   | SGC Comercial     | 0         |
| Qualificada       | SGC Comercial     | 0         |
| Convertida        | SGC Comercial     | 1         |
| Descartada        | SGC Comercial     | 2         |

**Transições**

| Ação           | De                | Para            | Executa por     |
|----------------|-------------------|-----------------|-----------------|
| Qualificar     | Identificada      | Em Qualificação | SGC Comercial   |
| Aprovar Qualif.| Em Qualificação   | Qualificada     | SGC Comercial   |
| Converter      | Qualificada       | Convertida      | SGC Comercial   |
| Descartar      | (qualquer)        | Descartada      | SGC Comercial   |

**Regras:** só é possível converter após existir `analise_viabilidade` com
parecer Favorável ou Favorável c/ ressalvas.

---

## 2. Workflow — Viabilidade (`analise_viabilidade`)

**Estados**

| Estado          | Role responsável            | docstatus |
|-----------------|-----------------------------|-----------|
| Em Análise      | SGC Comercial               | 0         |
| Aguardando Parecer| SGC Diretoria             | 0         |
| Aprovada        | SGC Diretoria               | 1         |
| Reprovada       | SGC Diretoria               | 2         |

**Transições**

| Ação            | De                  | Para               | Executa por   |
|-----------------|---------------------|--------------------|---------------|
| Enviar p/ Parecer| Em Análise         | Aguardando Parecer | SGC Comercial |
| Aprovar         | Aguardando Parecer  | Aprovada           | SGC Diretoria |
| Reprovar        | Aguardando Parecer  | Reprovada          | SGC Diretoria |

**Regras:** `margem_estimada` abaixo do limite definido exige parecer explícito
da SGC Diretoria.

---

## 3. Workflow — Disputa / Proposta (`disputa_proposta_coaph`)

**Estados**

| Estado            | Role responsável  | docstatus |
|-------------------|-------------------|-----------|
| Em Preparação     | SGC Comercial     | 0         |
| Proposta Enviada  | SGC Comercial     | 0         |
| Em Disputa        | SGC Comercial     | 0         |
| Vencida           | SGC Comercial     | 1         |
| Perdida           | SGC Comercial     | 2         |

**Transições**

| Ação            | De                | Para             | Executa por   |
|-----------------|-------------------|------------------|---------------|
| Enviar Proposta | Em Preparação     | Proposta Enviada | SGC Comercial |
| Iniciar Disputa | Proposta Enviada  | Em Disputa       | SGC Comercial |
| Registrar Vitória| Em Disputa       | Vencida          | SGC Comercial |
| Registrar Derrota| Em Disputa       | Perdida          | SGC Comercial |

**Regras:** transição para "Vencida" habilita a criação da
`formalizacao_contratual`.

---

## 4. Workflow — Formalização (`formalizacao_contratual`)

**Estados**

| Estado              | Role responsável  | docstatus |
|---------------------|-------------------|-----------|
| Em Elaboração       | SGC Jurídico      | 0         |
| Em Revisão Jurídica | SGC Jurídico      | 0         |
| Aguardando Assinatura| SGC Diretoria    | 0         |
| Formalizado         | SGC Jurídico      | 1         |
| Arquivado           | SGC Jurídico      | 2         |

**Transições**

| Ação               | De                   | Para                | Executa por   |
|--------------------|----------------------|---------------------|---------------|
| Enviar p/ Revisão  | Em Elaboração        | Em Revisão Jurídica | SGC Jurídico  |
| Liberar p/ Assinatura| Em Revisão Jurídica| Aguardando Assinatura| SGC Jurídico  |
| Confirmar Assinatura| Aguardando Assinatura| Formalizado        | SGC Diretoria |
| Arquivar           | (qualquer)           | Arquivado           | SGC Jurídico  |

**Regras:** ao "Formalizar", o sistema habilita a criação do `contrato_360`
(fase inicial = Mobilização).

---

## 5. Workflow — Contrato 360 (`contrato_360`)

Controla a **fase** macro do contrato.

**Estados**

| Estado            | Role responsável  | docstatus |
|-------------------|-------------------|-----------|
| Mobilização       | SGC Mobilização   | 0         |
| Operação Assistida| SGC Operação      | 1         |
| Operação Regular  | SGC Operação      | 1         |
| Em Renovação      | SGC Jurídico      | 1         |
| Encerrado         | SGC Diretoria     | 2         |

**Transições**

| Ação                  | De                 | Para               | Executa por      |
|-----------------------|--------------------|--------------------|------------------|
| Liberar Operação      | Mobilização        | Operação Assistida | SGC Mobilização  |
| Estabilizar Operação  | Operação Assistida | Operação Regular   | SGC Operação     |
| Iniciar Renovação     | Operação Regular   | Em Renovação       | SGC Jurídico     |
| Voltar à Operação     | Em Renovação       | Operação Regular   | SGC Operação     |
| Encerrar Contrato     | (qualquer ativo)   | Encerrado          | SGC Diretoria    |

**Regras:** "Liberar Operação" exige `plano_mobilizacao` Concluído (100%).

---

## 6. Workflow — Mobilização (`plano_mobilizacao`)

**Estados**

| Estado            | Role responsável  | docstatus |
|-------------------|-------------------|-----------|
| Planejada         | SGC Mobilização   | 0         |
| Em Andamento      | SGC Mobilização   | 0         |
| Em Validação      | SGC Operação      | 0         |
| Concluída         | SGC Mobilização   | 1         |
| Suspensa          | SGC Mobilização   | 0         |

**Transições**

| Ação            | De            | Para         | Executa por      |
|-----------------|---------------|--------------|------------------|
| Iniciar         | Planejada     | Em Andamento | SGC Mobilização  |
| Enviar Validação| Em Andamento  | Em Validação | SGC Mobilização  |
| Aprovar         | Em Validação  | Concluída    | SGC Operação     |
| Devolver        | Em Validação  | Em Andamento | SGC Operação     |
| Suspender       | Em Andamento  | Suspensa     | SGC Mobilização  |
| Retomar         | Suspensa      | Em Andamento | SGC Mobilização  |

**Regras:** "Aprovar" exige todas as `etapa_mobilizacao` com status Concluída e
cooperados com `status_credenciamento` = Credenciado.

---

## 7. Workflow — Ciclo Mensal (`ciclo_mensal_medicao`)

Núcleo do **Ciclo Mensal de Medição**.

**Estados**

| Estado              | Role responsável  | docstatus |
|---------------------|-------------------|-----------|
| Competência Aberta  | SGC Operação      | 0         |
| Produção Registrada | SGC Operação      | 0         |
| Produção Conferida  | SGC Operação      | 0         |
| Produção Validada   | SGC Diretoria     | 0         |
| Faturamento Emitido | SGC Financeiro    | 0         |
| Competência Encerrada| SGC Financeiro   | 1         |

**Transições**

| Ação                | De                  | Para                | Executa por    |
|---------------------|---------------------|---------------------|----------------|
| Registrar Produção  | Competência Aberta  | Produção Registrada | SGC Operação   |
| Conferir Produção   | Produção Registrada | Produção Conferida  | SGC Operação   |
| Validar Produção    | Produção Conferida  | Produção Validada   | SGC Diretoria  |
| Emitir Faturamento  | Produção Validada   | Faturamento Emitido | SGC Financeiro |
| Encerrar Competência| Faturamento Emitido | Competência Encerrada| SGC Financeiro|

**Regras:**
- "Validar Produção" exige todos os `item_producao` com `conferido` = Sim.
- "Emitir Faturamento" cria o `faturamento_coaph`.
- "Encerrar Competência" só após Recebimento baixado e Repasse aos Cooperados
  executado (Demonstrativos publicados).

---

## 8. Workflow — Renovação (`renovacao_contratual`)

**Estados**

| Estado              | Role responsável  | docstatus |
|---------------------|-------------------|-----------|
| Em Avaliação        | SGC Comercial     | 0         |
| Em Negociação       | SGC Comercial     | 0         |
| Aprovada            | SGC Diretoria     | 1         |
| Renovada            | SGC Jurídico      | 1         |
| Não Renovada        | SGC Diretoria     | 2         |

**Transições**

| Ação            | De            | Para          | Executa por   |
|-----------------|---------------|---------------|---------------|
| Iniciar Negociação| Em Avaliação| Em Negociação | SGC Comercial |
| Aprovar Renovação| Em Negociação| Aprovada      | SGC Diretoria |
| Formalizar Renovação| Aprovada  | Renovada      | SGC Jurídico  |
| Não Renovar     | (qualquer)    | Não Renovada  | SGC Diretoria |

**Regras:**
- "Formalizar Renovação" atualiza `vigencia_fim` no `contrato_360` e pode gerar
  `aditivo_contratual` de prazo/valor.
- "Não Renovar" sinaliza o Contrato 360 para Encerramento.

---

## 9. Observações gerais

- Toda transição é registrada no **histórico/log** nativo do documento (sem uso
  do termo proibido "comunicar"). Notificações são feitas por alertas/log.
- Validações de transição são implementadas como `before_transition` /
  `validate` no app, **sem** alterar o core.
- Cada estado restringe a edição ao role responsável, reforçando a separação de
  responsabilidades da [matriz de permissões](PERMISSIONS.md).
