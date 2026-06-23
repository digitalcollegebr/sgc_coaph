"""Testes das consolidações (rollup) do Ciclo Mensal e da diferença do Recebimento.

Rodar:
  bench --site <site> run-tests \
    --module coaph_contract_ops.coaph_contract_ops.automation.test_rollup
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


def _contratante():
    nome = "QA ROLLUP Contratante"
    if frappe.db.exists("Contratante COAPH", {"nome_contratante": nome}):
        return frappe.db.get_value("Contratante COAPH", {"nome_contratante": nome}, "name")
    return frappe.get_doc({"doctype": "Contratante COAPH", "nome_contratante": nome,
                           "tipo_contratante": "Privado", "status": "Ativo"}
                          ).insert(ignore_permissions=True).name


def _contrato(ct):
    return frappe.get_doc({"doctype": "Contrato 360", "titulo_contrato": "QA ROLLUP Contrato",
                           "contratante": ct, "vigencia_inicio": add_days(nowdate(), -10),
                           "vigencia_fim": add_days(nowdate(), 355), "valor_mensal": 1000}
                          ).insert(ignore_permissions=True).name


def _ciclo(contrato, ct):
    return frappe.get_doc({"doctype": "Ciclo Mensal Medicao", "contrato": contrato,
                           "competencia": "06/2026", "contratante": ct,
                           "valor_producao": 1000}).insert(ignore_permissions=True).name


class TestRollup(FrappeTestCase):
    def test_recebimento_calcula_diferenca(self):
        ct = _contratante()
        contrato = _contrato(ct)
        ciclo = _ciclo(contrato, ct)
        rec = frappe.get_doc({"doctype": "Recebimento COAPH", "contrato": contrato,
                              "ciclo_mensal": ciclo, "valor_previsto": 1000,
                              "valor_recebido": 600}).insert(ignore_permissions=True)
        self.assertEqual(rec.diferenca, -400)

    def test_faturamento_consolida_no_ciclo(self):
        ct = _contratante()
        contrato = _contrato(ct)
        ciclo = _ciclo(contrato, ct)
        frappe.get_doc({"doctype": "Faturamento COAPH", "contrato": contrato,
                        "ciclo_mensal": ciclo, "valor_bruto": 1000, "valor_liquido": 950,
                        "status": "NF emitida"}).insert(ignore_permissions=True)
        self.assertEqual(frappe.db.get_value("Ciclo Mensal Medicao", ciclo, "valor_faturado"), 950)

    def test_recebimento_consolida_no_ciclo(self):
        ct = _contratante()
        contrato = _contrato(ct)
        ciclo = _ciclo(contrato, ct)
        frappe.get_doc({"doctype": "Recebimento COAPH", "contrato": contrato,
                        "ciclo_mensal": ciclo, "valor_previsto": 1000, "valor_recebido": 800,
                        "status": "Recebido integral"}).insert(ignore_permissions=True)
        self.assertEqual(frappe.db.get_value("Ciclo Mensal Medicao", ciclo, "valor_recebido"), 800)

    def test_repasse_consolida_no_ciclo(self):
        ct = _contratante()
        contrato = _contrato(ct)
        ciclo = _ciclo(contrato, ct)
        frappe.get_doc({"doctype": "Repasse Cooperados", "contrato": contrato,
                        "ciclo_mensal": ciclo, "competencia": "06/2026",
                        "valor_total_repasse": 700}).insert(ignore_permissions=True)
        self.assertEqual(frappe.db.get_value("Ciclo Mensal Medicao", ciclo, "valor_repasse"), 700)
