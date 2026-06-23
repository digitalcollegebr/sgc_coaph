# Plano de Implementação — SGC COAPH

Plano em três horizontes — **POC**, **MVP** e **Produção** — para a
**Gestão 360 de Contratos**.

---

## 1. POC (Prova de Conceito)

**Objetivo:** validar a viabilidade técnica do app `coaph_contract_ops` sobre
ERPNext/Frappe e o fluxo do Contrato 360 com dados fictícios.

**Escopo**

- Ambiente Docker local com ERPNext v15 + app (módulo COAPH ContractOps).
- DocTypes centrais: `contratante_coaph`, `unidade_atendimento`, `contrato_360`,
  `servico_contratado`, `ciclo_mensal_medicao`, `item_producao`.
- Workspace "SGC COAPH" mínimo (Cockpit básico com 2–3 number cards).
- Script `seed_demo_data` inicial.
- 1 workflow piloto (Ciclo Mensal de Medição).

**Critérios de saída**

- Subir a stack e navegar de Oportunidade a Ciclo Mensal com dados demo.
- Demonstrar abertura/validação de uma competência.

**Entregáveis:** imagem de POC, roteiro de demo curto, este conjunto de docs.

---

## 2. MVP (Produto Mínimo Viável)

**Objetivo:** cobrir o fluxo principal completo e a governança essencial, pronto
para uso interno controlado.

**Escopo**

- **Todos os DocTypes** de [`DATA_MODEL.md`](DATA_MODEL.md).
- **Todos os workflows** de [`WORKFLOWS.md`](WORKFLOWS.md).
- **Roles e matriz de permissões** de [`PERMISSIONS.md`](PERMISSIONS.md)
  (incluindo restrição de dados financeiros sensíveis).
- Automações: cálculo de Saúde do Contrato e Risco Contratual, abertura mensal
  do Ciclo, cálculo de Repasse, Demonstrativo de Repasse, alertas/log de
  Pendências e Renovação.
- Cockpit Executivo completo (number cards + charts).
- `seed_demo_data` cobrindo a história de 20 passos.
- Build-fora + push Docker Hub + pull no servidor (homologação).

**Critérios de saída**

- Executar o roteiro de [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) de ponta a ponta.
- Permissões validadas por role (em especial o bloqueio financeiro).
- Backup e restore testados.

---

## 3. Produção

**Objetivo:** operação real interna da COAPH com confiabilidade.

**Escopo**

- Deploy no servidor Ubuntu via imagem versionada (tag `vX.Y.Z`).
- HTTPS habilitado (reverse proxy + certificado).
- Firewall (UFW) restrito a SSH + 8081 (e 443 quando HTTPS).
- Backups automatizados + cópia off-site + teste de restore agendado.
- Hardening: usuário não-root, `.env` com permissões restritas, rotação de
  senhas.
- Rotina de update com rollback por tag.
- Treinamento dos perfis de usuário.

**Critérios de saída**

- Plano de backup/restore operando.
- Procedimento de atualização documentado e ensaiado.
- Usuários reais cadastrados com seus roles.

---

## 4. Riscos e mitigações

| Risco                                              | Mitigação                                                       |
|----------------------------------------------------|----------------------------------------------------------------|
| Acoplamento indevido ao core ERPNext               | Disciplina de "sem fork"; extensões só via app/fixtures        |
| Crescimento do escopo (scope creep)                | Horizontes POC/MVP/Produção bem delimitados                    |
| Perda de dados em operação Docker                  | Proibição de `down -v`; backups + restore testado              |
| Complexidade dos workflows                         | Começar com workflow piloto na POC; ampliar no MVP             |
| Vazamento de dados financeiros sensíveis           | Permissões por DocType + nível de campo (R$)                   |
| Dependência de versão (version-15)                 | Tags versionadas da imagem; acompanhar releases oficiais       |
| Qualidade dos dados de Produção                    | Etapa de Validação da Produção obrigatória no Ciclo Mensal     |

---

## 5. Próximos passos

1. Implementar os DocTypes e workflows do MVP.
2. Aplicar fixtures de roles/permissões e configurar o Cockpit.
3. Completar o `seed_demo_data` para a história de 20 passos.
4. Versionar a imagem e homologar no servidor.
5. Habilitar HTTPS e backups off-site (entrada em Produção).
6. Iniciar itens do [`ROADMAP.md`](ROADMAP.md) conforme prioridade.
