"""Automações do Contrato 360.

Regras de negócio executadas no `validate` do Contrato 360:
- calcular prazo em meses a partir da vigência;
- calcular valor anual a partir do valor mensal quando aplicável;
- validar que a vigência final é maior que a inicial;
- definir saúde inicial como "Saudavel".

Nada aqui altera código core do ERPNext/Frappe.
"""

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate


def validate_contrato(doc, method=None):
    _validar_vigencia(doc)
    _calcular_prazo_meses(doc)
    _calcular_valor_anual(doc)
    _calcular_taxa_legalidade(doc)
    _definir_saude_inicial(doc)


def _validar_vigencia(doc):
    if doc.get("vigencia_inicio") and doc.get("vigencia_fim"):
        if getdate(doc.vigencia_fim) <= getdate(doc.vigencia_inicio):
            frappe.throw(_("A vigência final deve ser maior que a vigência inicial."))


def _calcular_prazo_meses(doc):
    if doc.get("vigencia_inicio") and doc.get("vigencia_fim"):
        dias = date_diff(doc.vigencia_fim, doc.vigencia_inicio)
        # aproximação de meses (30 dias) — suficiente para indicador gerencial
        doc.prazo_meses = max(1, round(dias / 30))


def _calcular_valor_anual(doc):
    # valor_anual é read_only no formulário => sempre derivado de valor_mensal,
    # recalculando quando valor_mensal muda.
    if flt(doc.get("valor_mensal")):
        doc.valor_anual = flt(doc.valor_mensal) * 12


def _calcular_taxa_legalidade(doc):
    # Regra de negócio (validada contra a planilha de backlog):
    # Taxa de Legalidade = Taxa Administrativa (bruta) + Impostos.
    # Campo read_only no formulário => sempre derivado.
    doc.taxa_legalidade = flt(doc.get("taxa_admin_bruta")) + flt(doc.get("percentual_impostos"))


def _definir_saude_inicial(doc):
    if not doc.get("saude_contrato"):
        doc.saude_contrato = "Saudavel"
