#!/usr/bin/env python3
"""Gera os 12 Query Reports nativos do módulo COAPH Contract Ops.
Cada relatório: report/<scrub>/<scrub>.json + __init__.py  (is_standard=Yes).
Reexecutável (single source of truth — sobrescreve os 3 iniciais também).

Títulos sem acento (folder = scrub do nome); os LABELS das colunas usam PT-BR
com acento e formatação BR (Currency=R$, Date=DD/MM/AAAA via Frappe).
"""
import json
import os

REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "coaph_contract_ops", "coaph_contract_ops",
    "coaph_contract_ops", "report",
)
MODULE = "COAPH Contract Ops"
TS = "2026-06-23 00:00:00.000000"

ADMIN, DIR = "SGC Administrador", "SGC Diretoria"
COM, JUR, MOB = "SGC Comercial", "SGC Juridico", "SGC Mobilizacao"
OPE, FIN = "SGC Operacao", "SGC Financeiro"


def scrub(name):
    return name.lower().replace(" ", "_").replace("-", "_")


def report(name, ref, sql, roles, total=0):
    folder = os.path.join(REPORT_DIR, scrub(name))
    os.makedirs(folder, exist_ok=True)
    open(os.path.join(folder, "__init__.py"), "w").close()
    doc = {
        "add_total_row": total, "columns": [], "creation": TS, "disabled": 0,
        "docstatus": 0, "doctype": "Report", "filters": [], "idx": 0,
        "is_standard": "Yes", "letterhead": None, "modified": TS,
        "module": MODULE, "name": name, "owner": "Administrator",
        "prepared_report": 0, "query": sql, "ref_doctype": ref,
        "report_name": name, "report_type": "Query Report",
        "roles": [{"role": r} for r in roles],
    }
    with open(os.path.join(folder, scrub(name) + ".json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


# 1
report("Contratos por Status", "Contrato 360",
       "SELECT\n    status_contrato AS \"Status::220\",\n    COUNT(*) AS \"Quantidade:Int:120\",\n"
       "    SUM(valor_mensal) AS \"Receita Mensal:Currency:160\"\n"
       "FROM `tabContrato 360`\nGROUP BY status_contrato\nORDER BY 2 DESC",
       [ADMIN, DIR, COM, OPE], total=1)

# 2
report("Contratos por Saude", "Contrato 360",
       "SELECT\n    saude_contrato AS \"Saúde::220\",\n    COUNT(*) AS \"Quantidade:Int:120\",\n"
       "    SUM(valor_mensal) AS \"Receita Mensal:Currency:160\"\n"
       "FROM `tabContrato 360`\nGROUP BY saude_contrato\nORDER BY 2 DESC",
       [ADMIN, DIR, COM, OPE], total=1)

# 3
report("Contratos Vencendo", "Contrato 360",
       "SELECT\n    name AS \"Contrato:Link/Contrato 360:220\",\n"
       "    contratante AS \"Contratante:Link/Contratante COAPH:200\",\n"
       "    vigencia_fim AS \"Fim da Vigência:Date:120\",\n"
       "    DATEDIFF(vigencia_fim, CURDATE()) AS \"Dias p/ Vencer:Int:120\",\n"
       "    status_contrato AS \"Status::150\",\n    saude_contrato AS \"Saúde::120\",\n"
       "    valor_mensal AS \"Valor Mensal:Currency:140\"\n"
       "FROM `tabContrato 360`\nWHERE vigencia_fim IS NOT NULL\n"
       "  AND DATEDIFF(vigencia_fim, CURDATE()) <= 180\n  AND status_contrato != 'Encerrado'\n"
       "ORDER BY vigencia_fim ASC",
       [ADMIN, DIR, COM, OPE])

# 4
report("Mobilizacoes em Atraso", "Plano Mobilizacao",
       "SELECT\n    e.parent AS \"Plano:Link/Plano Mobilizacao:200\",\n"
       "    p.contrato AS \"Contrato:Link/Contrato 360:220\",\n"
       "    e.etapa AS \"Etapa::220\",\n    e.area_responsavel AS \"Área::120\",\n"
       "    e.data_fim_prevista AS \"Fim Previsto:Date:120\",\n    e.status AS \"Status::120\"\n"
       "FROM `tabEtapa Mobilizacao` e\nJOIN `tabPlano Mobilizacao` p ON p.name = e.parent\n"
       "WHERE e.status = 'Atrasado'\n   OR (e.data_fim_prevista < CURDATE()\n"
       "       AND e.status NOT IN ('Concluído', 'Cancelado'))\nORDER BY e.data_fim_prevista ASC",
       [ADMIN, DIR, MOB, OPE])

# 5
report("Ciclos Mensais por Competencia", "Ciclo Mensal Medicao",
       "SELECT\n    competencia AS \"Competência::120\",\n    COUNT(*) AS \"Qtd Ciclos:Int:100\",\n"
       "    SUM(valor_producao) AS \"Produção:Currency:150\",\n"
       "    SUM(valor_faturado) AS \"Faturado:Currency:150\",\n"
       "    SUM(valor_recebido) AS \"Recebido:Currency:150\",\n"
       "    SUM(valor_repasse) AS \"Repasse:Currency:150\"\n"
       "FROM `tabCiclo Mensal Medicao`\nGROUP BY competencia\nORDER BY competencia DESC",
       [ADMIN, DIR, OPE, FIN], total=1)

# 6
report("Faturado x Recebido", "Faturamento COAPH",
       "SELECT\n    f.contrato AS \"Contrato:Link/Contrato 360:220\",\n"
       "    f.competencia AS \"Competência::110\",\n    SUM(f.valor_liquido) AS \"Faturado:Currency:150\",\n"
       "    IFNULL(SUM(r.valor_recebido), 0) AS \"Recebido:Currency:150\",\n"
       "    SUM(f.valor_liquido) - IFNULL(SUM(r.valor_recebido), 0) AS \"A Receber:Currency:150\"\n"
       "FROM `tabFaturamento COAPH` f\nLEFT JOIN `tabRecebimento COAPH` r ON r.faturamento = f.name\n"
       "GROUP BY f.contrato, f.competencia\nORDER BY f.competencia DESC",
       [ADMIN, DIR, FIN], total=1)

# 7
report("Repasses Pendentes", "Repasse Cooperados",
       "SELECT\n    name AS \"Repasse:Link/Repasse Cooperados:200\",\n"
       "    contrato AS \"Contrato:Link/Contrato 360:220\",\n    competencia AS \"Competência::110\",\n"
       "    valor_total_repasse AS \"Valor de Repasse:Currency:160\",\n    status AS \"Status::170\"\n"
       "FROM `tabRepasse Cooperados`\nWHERE status NOT IN ('Pago', 'Cancelado')\n"
       "ORDER BY data_calculo ASC",
       [ADMIN, DIR, FIN], total=1)

# 8
report("Pendencias Criticas", "Pendencia Contratual",
       "SELECT\n    name AS \"Pendência:Link/Pendencia Contratual:180\",\n"
       "    contrato AS \"Contrato:Link/Contrato 360:220\",\n    area AS \"Área::120\",\n"
       "    prioridade AS \"Prioridade::100\",\n    status AS \"Status::130\",\n"
       "    data_abertura AS \"Abertura:Date:110\",\n    prazo AS \"Prazo:Date:110\"\n"
       "FROM `tabPendencia Contratual`\nWHERE prioridade IN ('Alta', 'Crítica')\n"
       "  AND status NOT IN ('Concluída', 'Cancelada')\n"
       "ORDER BY FIELD(prioridade, 'Crítica', 'Alta'), prazo ASC",
       [ADMIN, DIR, OPE, MOB])

# 9
report("Riscos Criticos", "Risco Contratual",
       "SELECT\n    name AS \"Risco:Link/Risco Contratual:180\",\n"
       "    contrato AS \"Contrato:Link/Contrato 360:220\",\n    tipo_risco AS \"Tipo::130\",\n"
       "    criticidade AS \"Criticidade::110\",\n    status AS \"Status::150\",\n    prazo AS \"Prazo:Date:110\"\n"
       "FROM `tabRisco Contratual`\nWHERE criticidade IN ('Alta', 'Crítica')\n"
       "  AND status NOT IN ('Mitigado', 'Encerrado')\n"
       "ORDER BY FIELD(criticidade, 'Crítica', 'Alta')",
       [ADMIN, DIR, OPE])

# 10
report("Pipeline de Oportunidades", "Oportunidade COAPH",
       "SELECT\n    name AS \"Oportunidade:Link/Oportunidade COAPH:200\",\n"
       "    contratante AS \"Contratante:Link/Contratante COAPH:200\",\n    status AS \"Status::180\",\n"
       "    prioridade AS \"Prioridade::100\",\n"
       "    valor_estimado_mensal AS \"Estim. Mensal:Currency:140\",\n"
       "    probabilidade AS \"Prob.:Percent:90\",\n"
       "    data_prevista_decisao AS \"Decisão Prevista:Date:130\"\n"
       "FROM `tabOportunidade COAPH`\n"
       "WHERE status NOT IN ('Descartada', 'Convertida em disputa/proposta')\n"
       "ORDER BY FIELD(prioridade, 'Crítica', 'Alta', 'Média', 'Baixa'), data_prevista_decisao ASC",
       [ADMIN, DIR, COM])

# 11
report("Disputas por Resultado", "Disputa Proposta COAPH",
       "SELECT\n    IFNULL(NULLIF(resultado, ''), 'Em andamento') AS \"Resultado::180\",\n"
       "    COUNT(*) AS \"Quantidade:Int:120\",\n    SUM(valor_proposto) AS \"Valor Proposto:Currency:160\"\n"
       "FROM `tabDisputa Proposta COAPH`\nGROUP BY 1\nORDER BY 2 DESC",
       [ADMIN, DIR, COM], total=1)

# 12
report("Tempo Medio de Mobilizacao", "Plano Mobilizacao",
       "SELECT\n    contrato AS \"Contrato:Link/Contrato 360:240\",\n"
       "    data_kickoff_realizada AS \"Kickoff:Date:120\",\n    data_go_live AS \"Go-Live:Date:120\",\n"
       "    DATEDIFF(data_go_live, data_kickoff_realizada) AS \"Dias de Mobilização:Int:160\"\n"
       "FROM `tabPlano Mobilizacao`\n"
       "WHERE data_go_live IS NOT NULL AND data_kickoff_realizada IS NOT NULL\n"
       "ORDER BY 4 DESC",
       [ADMIN, DIR, MOB, OPE], total=0)

print("Relatórios gerados em:", REPORT_DIR)
print("Total:", len([d for d in os.listdir(REPORT_DIR)
                      if os.path.isdir(os.path.join(REPORT_DIR, d))]))
