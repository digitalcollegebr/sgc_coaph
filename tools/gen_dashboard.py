#!/usr/bin/env python3
"""Gera fixtures de Cockpit/Workspace:
  fixtures/number_card.json
  fixtures/dashboard_chart.json
  fixtures/workspace.json   (workspace "SGC COAPH" com atalhos, cards e cockpit)
Reexecutável.
"""
import json
import os

FIX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "coaph_contract_ops", "coaph_contract_ops", "fixtures",
)
MODULE = "COAPH Contract Ops"

# ---------------- Number Cards ----------------
def card(name, label, dt, function="Count", based_on=None, filters=None, color="#1f6feb"):
    return {
        "doctype": "Number Card", "name": name, "label": label,
        "document_type": dt, "type": "Document Type", "function": function,
        "aggregate_function_based_on": based_on or "",
        "filters_json": json.dumps(filters or []),
        "is_public": 1, "show_percentage_stats": 1, "stats_time_interval": "Daily",
        "module": MODULE, "color": color,
    }

NUMBER_CARDS = [
    card("SGC Contratos Ativos", "Contratos Ativos", "Contrato 360",
         filters=[["Contrato 360", "status_contrato", "=", "Ativo"]], color="#2ea043"),
    card("SGC Contratos em Mobilizacao", "Contratos em Mobilização", "Contrato 360",
         filters=[["Contrato 360", "status_contrato", "=", "Em mobilização"]], color="#1f6feb"),
    card("SGC Contratos Operacao Assistida", "Contratos em Operação Assistida", "Contrato 360",
         filters=[["Contrato 360", "status_contrato", "=", "Operação assistida"]], color="#1f6feb"),
    card("SGC Contratos Criticos", "Contratos Críticos", "Contrato 360",
         filters=[["Contrato 360", "status_contrato", "=", "Crítico"]], color="#cf222e"),
    card("SGC Receita Mensal Contratada", "Receita Mensal Contratada (R$)", "Contrato 360",
         function="Sum", based_on="valor_mensal",
         filters=[["Contrato 360", "status_contrato", "in",
                   ["Ativo", "Ativo com atenção", "Operação assistida", "Em renovação"]]],
         color="#8250df"),
    card("SGC Pendencias Criticas", "Pendências Críticas", "Pendencia Contratual",
         filters=[["Pendencia Contratual", "prioridade", "=", "Crítica"],
                  ["Pendencia Contratual", "status", "in", ["Aberta", "Em andamento", "Bloqueada"]]],
         color="#cf222e"),
    card("SGC Riscos Criticos", "Riscos Críticos", "Risco Contratual",
         filters=[["Risco Contratual", "criticidade", "=", "Crítica"],
                  ["Risco Contratual", "status", "in",
                   ["Identificado", "Em monitoramento", "Mitigação em andamento", "Materializado"]]],
         color="#cf222e"),
    card("SGC Disputas em Andamento", "Disputas em Andamento", "Disputa Proposta COAPH",
         filters=[["Disputa Proposta COAPH", "status", "in",
                   ["Em análise", "Documentação em preparação", "Proposta em elaboração",
                    "Proposta enviada", "Aguardando resultado"]]], color="#bf8700"),
]

# ---------------- Dashboard Charts ----------------
def chart(name, label, dt, field, ctype="Donut"):
    return {
        "doctype": "Dashboard Chart", "name": name, "chart_name": label,
        "chart_type": "Group By", "document_type": dt, "group_by_type": "Count",
        "group_by_based_on": field, "type": ctype, "is_public": 1, "timeseries": 0,
        "module": MODULE, "number_of_groups": 0, "filters_json": "[]",
        "dynamic_filters_json": "[]", "use_report_chart": 0,
    }

CHARTS = [
    chart("SGC Contratos por Status", "Contratos por Status", "Contrato 360", "status_contrato"),
    chart("SGC Contratos por Saude", "Contratos por Saúde", "Contrato 360", "saude_contrato"),
    chart("SGC Repasses por Status", "Repasses por Status", "Repasse Cooperados", "status", "Bar"),
    chart("SGC Disputas por Resultado", "Disputas por Resultado", "Disputa Proposta COAPH", "resultado", "Bar"),
    chart("SGC Pendencias por Prioridade", "Pendências por Prioridade", "Pendencia Contratual", "prioridade", "Bar"),
]

# ---------------- Workspace ----------------
# Atalhos (shortcuts) — DocTypes mais usados
SHORTCUTS = [
    ("Contrato 360", "Grey"), ("Oportunidade COAPH", "Blue"),
    ("Disputa Proposta COAPH", "Cyan"), ("Plano Mobilizacao", "Orange"),
    ("Ciclo Mensal Medicao", "Green"), ("Repasse Cooperados", "Purple"),
    ("Pendencia Contratual", "Red"), ("Renovacao Contratual", "Yellow"),
]

# Cartões de links agrupados (Card Break + Links)
LINK_GROUPS = [
    ("Entrada do Contrato", [
        ("Oportunidade COAPH", "Oportunidades"),
        ("Analise Viabilidade", "Viabilidades / Go-No-Go"),
        ("Disputa Proposta COAPH", "Disputas e Propostas"),
        ("Formalizacao Contratual", "Formalizações Contratuais"),
    ]),
    ("Gestão do Contrato", [
        ("Contrato 360", "Contrato 360"),
        ("Plano Mobilizacao", "Mobilizações"),
        ("Cooperado Mobilizado", "Cooperados Mobilizados"),
    ]),
    ("Ciclo Mensal e Financeiro", [
        ("Ciclo Mensal Medicao", "Ciclos Mensais"),
        ("Faturamento COAPH", "Faturamentos"),
        ("Recebimento COAPH", "Recebimentos"),
        ("Repasse Cooperados", "Repasses aos Cooperados"),
    ]),
    ("Governança Contratual", [
        ("Pendencia Contratual", "Pendências"),
        ("Ocorrencia Contratual", "Ocorrências"),
        ("Risco Contratual", "Riscos"),
        ("Renovacao Contratual", "Renovações"),
        ("Aditivo Contratual", "Aditivos"),
    ]),
    ("Cadastros", [
        ("Contratante COAPH", "Contratantes"),
        ("Unidade Atendimento", "Unidades de Atendimento"),
    ]),
]

# Relatórios (Query Reports) — grupo com link_type "Report"
REPORTS = [
    "Contratos por Status", "Contratos por Saude", "Contratos Vencendo",
    "Mobilizacoes em Atraso", "Ciclos Mensais por Competencia", "Faturado x Recebido",
    "Repasses Pendentes", "Pendencias Criticas", "Riscos Criticos",
    "Pipeline de Oportunidades", "Disputas por Resultado", "Tempo Medio de Mobilizacao",
]


def build_content():
    blocks = [
        {"id": "hdr_cockpit", "type": "header",
         "data": {"text": "<span class=\"h4\"><b>Cockpit Executivo — SGC COAPH</b></span>", "col": 12}},
    ]
    for c in NUMBER_CARDS:
        blocks.append({"id": "nc_" + c["name"].replace(" ", "_"), "type": "number_card",
                       "data": {"number_card_name": c["name"], "col": 3}})
    blocks.append({"id": "hdr_charts", "type": "header",
                   "data": {"text": "<span class=\"h5\"><b>Indicadores</b></span>", "col": 12}})
    for ch in CHARTS:
        blocks.append({"id": "ch_" + ch["name"].replace(" ", "_"), "type": "chart",
                       "data": {"chart_name": ch["name"], "col": 6}})
    blocks.append({"id": "hdr_atalhos", "type": "header",
                   "data": {"text": "<span class=\"h5\"><b>Atalhos</b></span>", "col": 12}})
    for dt, _ in SHORTCUTS:
        blocks.append({"id": "sc_" + dt.replace(" ", "_"), "type": "shortcut",
                       "data": {"shortcut_name": dt, "col": 3}})
    blocks.append({"id": "hdr_modulos", "type": "header",
                   "data": {"text": "<span class=\"h5\"><b>Módulos</b></span>", "col": 12}})
    for grp, _ in LINK_GROUPS:
        blocks.append({"id": "card_" + grp.replace(" ", "_"), "type": "card",
                       "data": {"card_name": grp, "col": 4}})
    blocks.append({"id": "card_Relatorios", "type": "card",
                   "data": {"card_name": "Relatórios", "col": 4}})
    return json.dumps(blocks)


shortcut_rows = [{"type": "DocType", "link_to": dt, "label": dt, "color": color, "doc_view": "List"}
                 for dt, color in SHORTCUTS]

link_rows = []
for grp, items in LINK_GROUPS:
    link_rows.append({"type": "Card Break", "label": grp, "hidden": 0,
                      "link_count": len(items), "onboard": 0})
    for dt, label in items:
        link_rows.append({"type": "Link", "link_type": "DocType", "link_to": dt,
                          "label": label, "hidden": 0, "onboard": 0, "is_query_report": 0})
link_rows.append({"type": "Card Break", "label": "Relatórios", "hidden": 0,
                  "link_count": len(REPORTS), "onboard": 0})
for rep in REPORTS:
    link_rows.append({"type": "Link", "link_type": "Report", "link_to": rep,
                      "label": rep, "hidden": 0, "onboard": 0, "is_query_report": 1})

workspace = {
    "doctype": "Workspace", "name": "SGC COAPH", "label": "SGC COAPH",
    "title": "SGC COAPH", "module": MODULE, "public": 1, "is_hidden": 0,
    "icon": "organization", "indicator_color": "blue",
    "sequence_id": 1.0, "content": build_content(),
    "shortcuts": shortcut_rows, "links": link_rows,
    "number_cards": [{"number_card_name": c["name"], "label": c["label"]} for c in NUMBER_CARDS],
    "charts": [{"chart_name": ch["name"], "label": ch["chart_name"]} for ch in CHARTS],
    "roles": [],
}

json.dump(NUMBER_CARDS, open(os.path.join(FIX, "number_card.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
json.dump(CHARTS, open(os.path.join(FIX, "dashboard_chart.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
json.dump([workspace], open(os.path.join(FIX, "workspace.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("Cockpit gerado:", len(NUMBER_CARDS), "number cards,", len(CHARTS), "charts, 1 workspace")
