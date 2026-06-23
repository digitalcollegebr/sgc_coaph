# Permissões — SGC COAPH

Roles e matriz de permissões por DocType do app `coaph_contract_ops`. Tudo é
configurado pelo sistema **nativo de Role / Role Permission do Frappe**, sem
alterar o core.

---

## 1. Roles (papéis)

| Role                 | Descrição                                                          |
|----------------------|--------------------------------------------------------------------|
| **SGC Administrador**| Administra o app, configurações, workspace e parametrizações       |
| **SGC Diretoria**    | Visão executiva, aprovações estratégicas e financeiras            |
| **SGC Comercial**    | Funil comercial: Oportunidade, Viabilidade, Disputa/Proposta, Renovação |
| **SGC Jurídico**     | Formalização, Aditivos e Renovação Contratual                     |
| **SGC Mobilização**  | Plano e etapas de Mobilização Contratual e cooperados mobilizados |
| **SGC Operação**     | Operação, Ciclo Mensal de Medição, Produção, Ocorrências, Riscos, Pendências |
| **SGC Financeiro**   | Faturamento, Recebimento, Repasse aos Cooperados e Demonstrativos |
| **SGC RH / Cooperados**| Credenciamento de Cooperados e Onboarding Cooperativo           |
| **SGC Consulta**     | Acesso somente leitura (consulta), exceto dados financeiros sensíveis|

---

## 2. Princípios de segurança

- **Dados financeiros sensíveis** (`faturamento_coaph`, `recebimento_coaph`,
  `repasse_cooperados`, `item_repasse`, valores de `contrato_360`) são restritos
  a **SGC Financeiro**, **SGC Diretoria** e **SGC Administrador**.
- **SGC Consulta** **não** acessa os DocTypes financeiros (nem em leitura).
- Separação de responsabilidades reforçada pelos **workflows**: mesmo com
  permissão de escrita, a edição em cada estado fica restrita ao role do estado
  (ver [`WORKFLOWS.md`](WORKFLOWS.md)).
- **SGC Administrador** acumula permissões de configuração, não substituindo a
  governança de workflow.

Legenda: **R** = read, **W** = write, **C** = create, **—** = sem acesso.

---

## 3. Matriz — Cadastros e Comercial

| DocType                 | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|-------------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `contratante_coaph`     | RWC   | R         | RWC       | R        | R        | R        | R       | R       | R        |
| `unidade_atendimento`   | RWC   | R         | RWC       | R        | R        | RW       | R       | R       | R        |
| `oportunidade_coaph`    | RWC   | R         | RWC       | R        | —        | —        | —       | —       | R        |
| `analise_viabilidade`   | RWC   | RW        | RWC       | R        | —        | —        | R       | —       | R        |
| `disputa_proposta_coaph`| RWC   | R         | RWC       | R        | —        | —        | R       | —       | R        |

---

## 4. Matriz — Jurídico e Contrato

| DocType                  | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|--------------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `formalizacao_contratual`| RWC   | RW        | R         | RWC      | R        | R        | R       | —       | R        |
| `contrato_360`           | RWC   | RW        | R         | RW       | RW       | RW       | R       | R       | R *      |
| `servico_contratado`     | RWC   | RW        | R         | RW       | RW       | RW       | R       | R       | R *      |
| `aditivo_contratual`     | RWC   | RW        | R         | RWC      | R        | R        | R       | —       | R        |
| `renovacao_contratual`   | RWC   | RW        | RWC       | RWC      | —        | R        | R       | —       | R        |

\* SGC Consulta vê o Contrato 360 e serviços, porém os **campos de valor**
(`valor_global`, `valor_mensal`, `valor_total`) ficam ocultos via permissão de
nível de campo (Permission Level), restritos a Financeiro/Diretoria/Admin.

---

## 5. Matriz — Mobilização e Cooperados

| DocType                | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|------------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `plano_mobilizacao`    | RWC   | R         | —         | R        | RWC      | RW       | —       | R       | R        |
| `etapa_mobilizacao`    | RWC   | R         | —         | R        | RWC      | RW       | —       | R       | R        |
| `cooperado_mobilizado` | RWC   | R         | —         | R        | RW       | R        | R       | RWC     | R        |

---

## 6. Matriz — Ciclo Mensal e Produção

| DocType               | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|-----------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `ciclo_mensal_medicao`| RWC   | RW        | —         | —        | —        | RWC      | RW      | —       | R        |
| `item_producao`       | RWC   | RW        | —         | —        | —        | RWC      | RW      | —       | R        |

---

## 7. Matriz — Financeiro (sensível)

> Acesso restrito. **SGC Consulta** e papéis operacionais **não** acessam.

| DocType              | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|----------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `faturamento_coaph`  | RWC   | RW        | —         | —        | —        | R        | RWC     | —       | —        |
| `recebimento_coaph`  | RWC   | RW        | —         | —        | —        | —        | RWC     | —       | —        |
| `repasse_cooperados` | RWC   | RW        | —         | —        | —        | —        | RWC     | R **    | —        |
| `item_repasse`       | RWC   | RW        | —         | —        | —        | —        | RWC     | R **    | —        |

\** SGC RH / Cooperados pode visualizar o **Demonstrativo de Repasse** para fins
de Onboarding/atendimento ao cooperado, sem editar valores.

---

## 8. Matriz — Governança

| DocType                | Admin | Diretoria | Comercial | Jurídico | Mobiliz. | Operação | Financ. | RH/Coop | Consulta |
|------------------------|:-----:|:---------:|:---------:|:--------:|:--------:|:--------:|:-------:|:-------:|:--------:|
| `ocorrencia_contratual`| RWC   | R         | —         | R        | RW       | RWC      | R       | —       | R        |
| `risco_contratual`     | RWC   | RW        | R         | RW       | R        | RWC      | R       | —       | R        |
| `pendencia_contratual` | RWC   | R         | R         | RW       | RW       | RWC      | R       | R       | R        |

---

## 9. Perfis sugeridos (combinação de roles por usuário)

| Perfil de usuário          | Roles atribuídos                                        |
|----------------------------|---------------------------------------------------------|
| Diretor                    | SGC Diretoria                                           |
| Gestor de Contratos        | SGC Operação + SGC Consulta                             |
| Analista Comercial         | SGC Comercial                                           |
| Advogado / Jurídico        | SGC Jurídico                                            |
| Coordenador de Mobilização | SGC Mobilização                                         |
| Analista Financeiro        | SGC Financeiro                                          |
| Analista de Cooperados     | SGC RH / Cooperados                                     |
| Auditor / Visitante interno| SGC Consulta                                           |
| Administrador do sistema   | SGC Administrador (+ System Manager nativo, se preciso) |

---

## 10. Implementação

- Roles e permissões distribuídos como **fixtures** (`Role`, `Custom DocPerm`,
  `Workflow`) no app `coaph_contract_ops`.
- Restrições de campo (valores em R$) via **Permission Level** nos campos
  sensíveis.
- Restrições por registro (ex.: gestor vê só seus contratos) podem ser aplicadas
  por **User Permission** quando necessário, sem alterar o core.
