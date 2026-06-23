# COAPH ContractOps

App customizado Frappe que implementa o **SGC COAPH — Gestão 360 de Contratos**
sobre ERPNext/Frappe oficiais.

- **Nome técnico:** `coaph_contract_ops`
- **Nome amigável:** COAPH ContractOps
- **Módulo principal:** COAPH ContractOps
- **Produto:** SGC COAPH — Gestão 360 de Contratos

> Este app **não faz fork** do ERPNext/Frappe e **não altera código core**.
> Toda a customização vive aqui (DocTypes, workflows, fixtures, automações).

A documentação completa (arquitetura, modelo de dados, deploy Ubuntu/Docker,
roteiro de demonstração) está na pasta [`../../docs`](../../docs) do repositório
e no [README raiz](../../README.md).

## Instalação (resumo)

```bash
# dentro de um bench existente, com Frappe + ERPNext já instalados
bench get-app coaph_contract_ops /caminho/para/apps/coaph_contract_ops
bench --site SEU_SITE install-app coaph_contract_ops
bench --site SEU_SITE migrate
```

## Carregar dados de demonstração

```bash
bench --site SEU_SITE execute coaph_contract_ops.scripts.seed_demo_data.execute
```

A criação do site, instalação do ERPNext e orquestração Docker estão documentadas
em [`../../docs/DEPLOY_UBUNTU_DOCKER.md`](../../docs/DEPLOY_UBUNTU_DOCKER.md).
