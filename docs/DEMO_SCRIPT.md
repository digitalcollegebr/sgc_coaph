# Roteiro de Demonstração — SGC COAPH

Roteiro funcional para apresentar a **Gestão 360 de Contratos**. Use os dados
**fictícios** carregados pelo `seed-demo` (ver
[`DEPLOY_UBUNTU_DOCKER.md`](DEPLOY_UBUNTU_DOCKER.md), seção 7).

> Todos os nomes, CNPJ/CPF e valores (R$) são fictícios. Datas em DD/MM/AAAA.

---

## Parte A — Passeio pelas telas (visão por módulo)

### A.1 Cockpit Executivo
1. Abrir o workspace **"SGC COAPH"**.
2. Mostrar os **number cards**: Contratos ativos, em Mobilização Contratual,
   Faturamento do mês (R$), Recebimento do mês (R$), Repasses pendentes, Riscos
   Altos, Pendências abertas.
3. Mostrar os **charts**: evolução de Produção/Faturamento/Recebimento, Saúde do
   Contrato e funil comercial.

### A.2 Contrato 360
4. Abrir um **Contrato 360**. Destacar a visão central: contratante, vigência,
   valor mensal (R$), **fase**, **Saúde do Contrato** e **Risco Contratual**.
5. Mostrar a aba de **Serviços Contratados** (child table) por unidade.

### A.3 Mobilização Contratual
6. Abrir o **Plano de Mobilização** do contrato. Mostrar **etapas** (checklist,
   responsável, prazo, status) e o **percentual concluído**.
7. Abrir **Cooperados Mobilizados**: Credenciamento de Cooperados e status de
   Onboarding Cooperativo.

### A.4 Ciclo Mensal de Medição
8. Abrir o **Ciclo Mensal de Medição** da competência corrente. Mostrar status
   (Competência Aberta → Produção → Validada) e os **itens de Produção**.
9. Demonstrar a **Validação da Produção** (conferência dos itens).

### A.5 Faturamento e Recebimento
10. A partir do ciclo validado, mostrar o **Faturamento** emitido (valor bruto,
    impostos, valor líquido em R$) e o **Recebimento** baixado.

### A.6 Repasse aos Cooperados
11. Abrir o **Repasse aos Cooperados** da competência: valor total (R$), itens
    por cooperado e o **Demonstrativo de Repasse** anexado.

### A.7 Renovação e Riscos
12. Mostrar a **Renovação Contratual** (avaliação, reajuste, recomendação) e os
    **Riscos Contratuais** (probabilidade × impacto → nível).

### A.8 Pendências
13. Abrir as **Pendências Contratuais**: responsável, prazo, prioridade, status.

### A.9 Saúde do Contrato
14. Voltar ao Contrato 360 e explicar como **Saúde do Contrato** consolida SLA,
    Pendências, Riscos e situação financeira.

---

## Parte B — A história (20 passos)

Narrativa fim-a-fim de um contrato fictício para uma **UPA municipal**.

| #  | Etapa                          | O que demonstrar                                                                 |
|----|--------------------------------|----------------------------------------------------------------------------------|
| 1  | **Oportunidade**               | Surge uma Oportunidade: edital de gestão de plantões para a **UPA Vila Nova** (Prefeitura fictícia, CNPJ fictício). |
| 2  | **Análise de Viabilidade**     | Equipe registra viabilidade técnica/financeira e margem estimada; parecer Favorável. |
| 3  | **Disputa / Proposta**         | Modalidade Pregão; proposta de R$ 180.000,00/mês; resultado **Vencida**.         |
| 4  | **Formalização Contratual**    | Jurídico elabora e formaliza; vigência 01/07/2026 a 30/06/2027; valor global.    |
| 5  | **Contrato 360 criado**        | Nasce o Contrato 360 na fase **Mobilização**; serviços contratados por unidade.  |
| 6  | **Plano de Mobilização**       | Cria-se o Plano de Mobilização com etapas (documentação, insumos, escala).       |
| 7  | **Credenciamento de Cooperados**| Cadastro dos cooperados (médicos, enfermagem); status Credenciado.              |
| 8  | **Onboarding Cooperativo**     | Conclusão do onboarding dos cooperados mobilizados.                              |
| 9  | **Etapas concluídas**          | Todas as etapas atingem 100%; Plano de Mobilização vai a **Concluída**.           |
| 10 | **Operação Liberada**          | Contrato 360 transita para **Operação Assistida**.                              |
| 11 | **Operação Regular**           | Após estabilização, contrato passa a **Operação Regular**.                       |
| 12 | **Competência aberta**         | Abre-se o Ciclo Mensal de Medição da competência 07/2026.                        |
| 13 | **Produção registrada**        | Lançamento dos itens de Produção (plantões realizados por unidade).             |
| 14 | **Validação da Produção**      | Conferência e validação dos itens; produção total consolidada (R$).             |
| 15 | **Faturamento emitido**        | Geração do Faturamento (bruto, impostos, líquido em R$); vencimento.            |
| 16 | **Recebimento baixado**        | Registro do Recebimento (transferência/empenho); status Baixado.               |
| 17 | **Repasse calculado**          | Cálculo do Repasse aos Cooperados a partir da Produção validada.               |
| 18 | **Demonstrativos publicados**  | Geração dos Demonstrativos de Repasse por cooperado; Repasse executado.         |
| 19 | **Competência encerrada**      | Ciclo Mensal de Medição vai a **Competência Encerrada**.                         |
| 20 | **Monitoramento contínuo**     | Cockpit mostra **Saúde do Contrato**, **Risco Contratual** e proximidade de **Renovação Contratual**; registro de Ocorrências e Pendências. |

**Encerramento da demo:** voltar ao Cockpit Executivo e mostrar como o ciclo
recomeça na próxima competência, com a governança contínua acompanhando Saúde,
Risco, Pendências e Renovação do contrato.
