"""Consolidações automáticas (sem alterar core).

1. Recebimento COAPH: calcula `diferenca = valor_recebido - valor_previsto`.
2. Ciclo Mensal de Medição: consolida os totais a partir dos documentos
   filhos vinculados (Faturamento, Recebimento, Repasse), via doc_events.

Usa frappe.db.set_value (escrita direta) para não disparar o workflow do
Ciclo nem causar recursão.
"""

import frappe
from frappe.utils import flt


def recebimento_validate(doc, method=None):
    doc.diferenca = flt(doc.valor_recebido) - flt(doc.valor_previsto)


def _soma(doctype, campo, ciclo, status_excluir=None):
    cond = "ciclo_mensal = %(ciclo)s"
    params = {"ciclo": ciclo}
    if status_excluir:
        cond += " AND status != %(st)s"
        params["st"] = status_excluir
    val = frappe.db.sql(
        f"SELECT COALESCE(SUM(`{campo}`), 0) FROM `tab{doctype}` WHERE {cond}",
        params,
    )[0][0]
    return flt(val)


def recalcular_ciclo(ciclo):
    if not ciclo or not frappe.db.exists("Ciclo Mensal Medicao", ciclo):
        return
    frappe.db.set_value(
        "Ciclo Mensal Medicao", ciclo,
        {
            "valor_faturado": _soma("Faturamento COAPH", "valor_liquido", ciclo, "Cancelada"),
            "valor_recebido": _soma("Recebimento COAPH", "valor_recebido", ciclo, "Cancelado"),
            "valor_repasse": _soma("Repasse Cooperados", "valor_total_repasse", ciclo, "Cancelado"),
        },
        update_modified=False,
    )


def atualizar_ciclo(doc, method=None):
    """doc_event de Faturamento/Recebimento/Repasse → recalcula o Ciclo pai."""
    recalcular_ciclo(doc.get("ciclo_mensal"))


# ----------------------------------------------------------------- backfill
def recalcular_todos():
    """Reprocessa dados já existentes (executar uma vez após o deploy):
        bench --site SITE execute
          coaph_contract_ops.coaph_contract_ops.automation.rollup.recalcular_todos
    """
    for r in frappe.get_all("Recebimento COAPH",
                            fields=["name", "valor_recebido", "valor_previsto"]):
        frappe.db.set_value("Recebimento COAPH", r.name,
                            "diferenca", flt(r.valor_recebido) - flt(r.valor_previsto),
                            update_modified=False)
    for c in frappe.get_all("Ciclo Mensal Medicao", pluck="name"):
        recalcular_ciclo(c)
    frappe.db.commit()
    print("Rollup concluído: recebimentos e ciclos reprocessados.")
