"""Testes do Painel Executivo de Contratos.

Rodar:
  bench --site <site> run-tests \
    --module coaph_contract_ops.coaph_contract_ops.automation.test_dashboard

FrappeTestCase envolve cada teste em transação e faz rollback ao final,
então os registros de teste não persistem.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from coaph_contract_ops.coaph_contract_ops.automation.dashboard import get_painel_executivo


def _contratante(nome):
    if frappe.db.exists("Contratante COAPH", {"nome_contratante": nome}):
        return frappe.db.get_value("Contratante COAPH", {"nome_contratante": nome}, "name")
    return frappe.get_doc({
        "doctype": "Contratante COAPH", "nome_contratante": nome,
        "tipo_contratante": "Privado", "status": "Ativo",
    }).insert(ignore_permissions=True).name


def _contrato(titulo, contratante, vig_fim, status, saude, valor=1000):
    doc = frappe.get_doc({
        "doctype": "Contrato 360", "titulo_contrato": titulo,
        "contratante": contratante, "vigencia_inicio": add_days(nowdate(), -400),
        "vigencia_fim": vig_fim, "valor_mensal": valor, "saude_contrato": saude,
    }).insert(ignore_permissions=True)
    # status do workflow é gravado direto (evita o guarda de transição)
    frappe.db.set_value("Contrato 360", doc.name, "status_contrato", status)
    return doc.name


class TestPainelExecutivo(FrappeTestCase):
    def test_estrutura_de_retorno(self):
        data = get_painel_executivo()
        for chave in ("as_of", "resumo", "kpis", "contratos", "gargalos"):
            self.assertIn(chave, data)
        for k in ("ativos", "vencidos", "atrasados", "bloqueados_criticos",
                  "valor_total_ativos", "valor_total_criticos"):
            self.assertIn(k, data["kpis"])

    def test_semaforo_vermelho_vencido_e_critico(self):
        ct = _contratante("QA DASH Contratante")
        nome = _contrato("QA DASH Vencido Crítico", ct,
                         add_days(nowdate(), -10), "Crítico", "Crítico")
        data = get_painel_executivo()
        linha = next(x for x in data["contratos"] if x["name"] == nome)
        self.assertEqual(linha["semaforo"], "vermelho")
        self.assertEqual(len(linha["etapas"]), 6)
        self.assertTrue(linha["depende_presidencia"])
        self.assertGreaterEqual(data["kpis"]["vencidos"], 1)
        self.assertGreaterEqual(data["kpis"]["bloqueados_criticos"], 1)

    def test_semaforo_verde_saudavel_no_prazo(self):
        ct = _contratante("QA DASH Contratante")
        nome = _contrato("QA DASH Saudável", ct,
                         add_days(nowdate(), 365), "Ativo", "Saudável")
        data = get_painel_executivo()
        linha = next(x for x in data["contratos"] if x["name"] == nome)
        self.assertEqual(linha["semaforo"], "verde")
        self.assertFalse(linha["depende_presidencia"])
        # etapa atual (Op. Regular) deve estar destacada
        self.assertTrue(any(e["atual"] for e in linha["etapas"]))

    def test_semaforo_amarelo_vencendo(self):
        ct = _contratante("QA DASH Contratante")
        nome = _contrato("QA DASH Vencendo", ct,
                         add_days(nowdate(), 45), "Ativo", "Saudável")
        data = get_painel_executivo()
        linha = next(x for x in data["contratos"] if x["name"] == nome)
        self.assertEqual(linha["semaforo"], "amarelo")

    def test_ordenacao_severidade_primeiro(self):
        # a lista deve vir ordenada por severidade ascendente (vermelho=0 primeiro)
        data = get_painel_executivo()
        sev = [c["severidade"] for c in data["contratos"]]
        self.assertEqual(sev, sorted(sev))
