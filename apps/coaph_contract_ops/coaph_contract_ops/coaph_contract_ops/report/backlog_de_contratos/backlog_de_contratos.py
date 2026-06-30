"""Backlog de Contratos — visão equivalente à planilha de acompanhamento.

Reproduz as colunas que o gestor de contratos acompanha na planilha
(d_contrato), com filtros por status, contratante, UF e modalidade, e
drill-down para o Contrato 360.
"""

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("gcoop"), "fieldname": "codigo_gcoop", "fieldtype": "Data", "width": 80},
        {"label": _("Contrato"), "fieldname": "name", "fieldtype": "Link", "options": "Contrato 360", "width": 120},
        {"label": _("Nº Contrato"), "fieldname": "numero_contrato", "fieldtype": "Data", "width": 100},
        {"label": _("Título"), "fieldname": "titulo_contrato", "fieldtype": "Data", "width": 220},
        {"label": _("Sigla"), "fieldname": "sigla_contrato", "fieldtype": "Data", "width": 90},
        {"label": _("Contratante"), "fieldname": "contratante_nome", "fieldtype": "Data", "width": 150},
        {"label": _("Município"), "fieldname": "municipio", "fieldtype": "Data", "width": 110},
        {"label": _("UF"), "fieldname": "uf", "fieldtype": "Data", "width": 50},
        {"label": _("Status"), "fieldname": "status_contrato", "fieldtype": "Data", "width": 110},
        {"label": _("Natureza"), "fieldname": "tipo_contrato", "fieldtype": "Data", "width": 90},
        {"label": _("Modalidade"), "fieldname": "modalidade_contratacao", "fieldtype": "Data", "width": 110},
        {"label": _("Especialidade"), "fieldname": "especialidade_principal", "fieldtype": "Data", "width": 130},
        {"label": _("Início"), "fieldname": "vigencia_inicio", "fieldtype": "Date", "width": 90},
        {"label": _("Fim"), "fieldname": "vigencia_fim", "fieldtype": "Date", "width": 90},
        {"label": _("Valor Global"), "fieldname": "valor_global", "fieldtype": "Currency", "width": 120},
        {"label": _("Coop."), "fieldname": "quantidade_cooperados_prevista", "fieldtype": "Int", "width": 60},
        {"label": _("Tx Adm Contr."), "fieldname": "taxa_admin_contratual", "fieldtype": "Percent", "width": 100},
        {"label": _("Tx Adm Bruta"), "fieldname": "taxa_admin_bruta", "fieldtype": "Percent", "width": 100},
        {"label": _("Impostos"), "fieldname": "percentual_impostos", "fieldtype": "Percent", "width": 90},
        {"label": _("Legalidade"), "fieldname": "taxa_legalidade", "fieldtype": "Percent", "width": 90},
        {"label": _("Tx Comercial"), "fieldname": "taxa_comercial", "fieldtype": "Percent", "width": 100},
    ]


def get_data(filters):
    conditions = {}
    for campo in ("status_contrato", "contratante", "uf", "modalidade_contratacao"):
        if filters.get(campo):
            conditions[campo] = filters[campo]

    linhas = frappe.get_list(
        "Contrato 360",
        filters=conditions,
        fields=[
            "codigo_gcoop", "name", "numero_contrato", "titulo_contrato", "sigla_contrato",
            "contratante", "municipio", "uf", "status_contrato", "tipo_contrato",
            "modalidade_contratacao", "especialidade_principal", "vigencia_inicio",
            "vigencia_fim", "valor_global", "quantidade_cooperados_prevista",
            "taxa_admin_contratual", "taxa_admin_bruta", "percentual_impostos",
            "taxa_legalidade", "taxa_comercial",
        ],
        order_by="vigencia_fim asc",
        limit_page_length=0,
    )

    # Resolve o nome do contratante (a coluna Link mostraria só o código CTNT-#####).
    ids = {l.contratante for l in linhas if l.contratante}
    nomes = dict(frappe.get_all("Contratante COAPH", filters={"name": ["in", list(ids)]},
                                fields=["name", "nome_contratante"], as_list=True)) if ids else {}
    for l in linhas:
        l["contratante_nome"] = nomes.get(l.contratante, l.contratante)
    return linhas
