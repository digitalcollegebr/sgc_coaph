"""Ações encadeadas do fluxo de contrato (botões "Criar ...").

Cada função é whitelisted e idempotente: antes de criar o próximo documento,
verifica se já existe um vinculado, evitando duplicidade (regra da seção 12/13).
Retorna o `name` do documento (novo ou existente) para o cliente redirecionar.
"""

import frappe
from frappe import _


def _existente(doctype, filtros):
    return frappe.db.get_value(doctype, filtros, "name")


@frappe.whitelist()
def criar_viabilidade(oportunidade):
    existente = _existente("Analise Viabilidade", {"oportunidade": oportunidade})
    if existente:
        return existente
    op = frappe.get_doc("Oportunidade COAPH", oportunidade)
    doc = frappe.get_doc({
        "doctype": "Analise Viabilidade",
        "oportunidade": op.name,
        "contratante": op.contratante,
        "unidade_atendimento": op.unidade_atendimento,
        "status": "Em análise técnica",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_disputa(viabilidade):
    existente = _existente("Disputa Proposta COAPH", {"oportunidade": ["is", "set"],
                                                       "name": ["in", _disputas_da_viab(viabilidade)]})
    via = frappe.get_doc("Analise Viabilidade", viabilidade)
    if via.status != "Aprovada":
        frappe.throw(_("A Análise de Viabilidade precisa estar Aprovada para criar a Disputa/Proposta."))
    ja = _existente("Disputa Proposta COAPH", {"oportunidade": via.oportunidade})
    if ja:
        return ja
    titulo = frappe.db.get_value("Oportunidade COAPH", via.oportunidade, "titulo") or via.oportunidade
    doc = frappe.get_doc({
        "doctype": "Disputa Proposta COAPH",
        "titulo": titulo,
        "oportunidade": via.oportunidade,
        "contratante": via.contratante,
        "unidade_atendimento": via.unidade_atendimento,
        "status": "Edital/BID recebido",
    }).insert()
    return doc.name


def _disputas_da_viab(viabilidade):
    op = frappe.db.get_value("Analise Viabilidade", viabilidade, "oportunidade")
    return frappe.get_all("Disputa Proposta COAPH", filters={"oportunidade": op}, pluck="name") or [""]


@frappe.whitelist()
def criar_formalizacao(disputa):
    d = frappe.get_doc("Disputa Proposta COAPH", disputa)
    if d.resultado != "Vencida" and d.status != "Vencida":
        frappe.throw(_("A Disputa/Proposta precisa estar Vencida para criar a Formalização Contratual."))
    ja = _existente("Formalizacao Contratual", {"disputa_proposta": disputa})
    if ja:
        return ja
    doc = frappe.get_doc({
        "doctype": "Formalizacao Contratual",
        "disputa_proposta": d.name,
        "contratante": d.contratante,
        "unidade_atendimento": d.unidade_atendimento,
        "status": "Aguardando minuta",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_contrato(formalizacao):
    f = frappe.get_doc("Formalizacao Contratual", formalizacao)
    if f.status != "Contrato assinado":
        frappe.throw(_("A Formalização precisa estar com status 'Contrato assinado' para criar o Contrato 360."))
    ja = _existente("Contrato 360", {"formalizacao_contratual": formalizacao})
    if ja:
        return ja
    titulo = frappe.db.get_value("Contratante COAPH", f.contratante, "nome_contratante") or f.contratante
    contrato = frappe.get_doc({
        "doctype": "Contrato 360",
        "titulo_contrato": f"Contrato {titulo}",
        "contratante": f.contratante,
        "unidade_atendimento": f.unidade_atendimento,
        "formalizacao_contratual": f.name,
        "data_assinatura": f.data_assinatura,
        "responsavel_juridico": f.responsavel_juridico,
        "status_contrato": "Em mobilização",
        "saude_contrato": "Saudável",
    }).insert()
    # cria Plano de Mobilização inicial junto (automação 3)
    criar_plano_mobilizacao(contrato.name)
    return contrato.name


ETAPAS_PADRAO = [
    ("Kickoff interno do contrato", "Operação"),
    ("Plano de mobilização aprovado", "Operação"),
    ("Cadastro e parametrização do contrato", "TI"),
    ("Dimensionamento da equipe", "RH"),
    ("Solicitação de cooperados", "RH"),
    ("Credenciamento dos cooperados", "RH"),
    ("Onboarding cooperativo", "RH"),
    ("Liberação para início da operação", "Operação"),
]


@frappe.whitelist()
def criar_plano_mobilizacao(contrato):
    ja = _existente("Plano Mobilizacao", {"contrato": contrato})
    if ja:
        return ja
    c = frappe.get_doc("Contrato 360", contrato)
    doc = frappe.get_doc({
        "doctype": "Plano Mobilizacao",
        "contrato": c.name,
        "contratante": c.contratante,
        "unidade_atendimento": c.unidade_atendimento,
        "status": "Aguardando kickoff",
        "etapas": [{"etapa": e, "area_responsavel": area, "status": "Não iniciado", "sla_dias": 7}
                   for e, area in ETAPAS_PADRAO],
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_ciclo(contrato, competencia=None):
    c = frappe.get_doc("Contrato 360", contrato)
    if competencia:
        ja = _existente("Ciclo Mensal Medicao", {"contrato": contrato, "competencia": competencia})
        if ja:
            return ja
    doc = frappe.get_doc({
        "doctype": "Ciclo Mensal Medicao",
        "contrato": c.name,
        "competencia": competencia or "",
        "contratante": c.contratante,
        "unidade_atendimento": c.unidade_atendimento,
        "responsavel_operacional": c.responsavel_operacional,
        "responsavel_financeiro": c.responsavel_financeiro,
        "status": "Competência aberta",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_renovacao(contrato):
    ja = _existente("Renovacao Contratual", {"contrato": contrato})
    if ja:
        return ja
    c = frappe.get_doc("Contrato 360", contrato)
    doc = frappe.get_doc({
        "doctype": "Renovacao Contratual",
        "contrato": c.name,
        "vigencia_atual_fim": c.vigencia_fim,
        "status": "Monitorando vigência",
        "estrategia": "Aguardar",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_faturamento(ciclo):
    ja = _existente("Faturamento COAPH", {"ciclo_mensal": ciclo})
    if ja:
        return ja
    cm = frappe.get_doc("Ciclo Mensal Medicao", ciclo)
    doc = frappe.get_doc({
        "doctype": "Faturamento COAPH",
        "ciclo_mensal": cm.name,
        "contrato": cm.contrato,
        "contratante": cm.contratante,
        "competencia": cm.competencia,
        "valor_bruto": cm.valor_producao,
        "status": "Aguardando emissão",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_recebimento(ciclo):
    fat = _existente("Faturamento COAPH", {"ciclo_mensal": ciclo})
    if not fat:
        frappe.throw(_("Crie o Faturamento antes de registrar o Recebimento."))
    ja = _existente("Recebimento COAPH", {"faturamento": fat})
    if ja:
        return ja
    fdoc = frappe.get_doc("Faturamento COAPH", fat)
    doc = frappe.get_doc({
        "doctype": "Recebimento COAPH",
        "faturamento": fdoc.name,
        "contrato": fdoc.contrato,
        "ciclo_mensal": ciclo,
        "valor_previsto": fdoc.valor_liquido or fdoc.valor_bruto,
        "data_prevista": fdoc.data_vencimento,
        "status": "Previsto",
    }).insert()
    return doc.name


@frappe.whitelist()
def criar_repasse(ciclo):
    ja = _existente("Repasse Cooperados", {"ciclo_mensal": ciclo})
    if ja:
        return ja
    cm = frappe.get_doc("Ciclo Mensal Medicao", ciclo)
    doc = frappe.get_doc({
        "doctype": "Repasse Cooperados",
        "ciclo_mensal": cm.name,
        "contrato": cm.contrato,
        "competencia": cm.competencia,
        "valor_total_producao": cm.valor_producao,
        "status": "Aguardando recebimento",
    }).insert()
    return doc.name
