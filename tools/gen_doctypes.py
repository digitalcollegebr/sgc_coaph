#!/usr/bin/env python3
"""Gerador determinístico dos DocTypes do app coaph_contract_ops.

Emite, para cada DocType:
  doctype/<scrub>/<scrub>.json    (definição)
  doctype/<scrub>/<scrub>.py      (controller stub)
  doctype/<scrub>/__init__.py

Rode com:  python3 tools/gen_doctypes.py
Reexecutável (sobrescreve). Mantém o schema versionado e consistente.

Convenções:
  - fieldnames sem acento (snake_case); labels em PT-BR;
  - naming_series nos DocTypes principais;
  - Link fields entre documentos; child tables com istable=1;
  - campo `status` é usado como workflow_state_field quando há workflow.
"""
import json
import os

BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "coaph_contract_ops", "coaph_contract_ops",
    "coaph_contract_ops", "doctype",
)
MODULE = "COAPH Contract Ops"
TS = "2026-06-23 00:00:00.000000"

ADMIN = "SGC Administrador"
SYS = "System Manager"
DIRETORIA = "SGC Diretoria"
CONSULTA = "SGC Consulta"
COMERCIAL = "SGC Comercial"
JURIDICO = "SGC Juridico"
MOBILIZACAO = "SGC Mobilizacao"
OPERACAO = "SGC Operacao"
FINANCEIRO = "SGC Financeiro"
RH = "SGC RH Cooperados"


def scrub(name):
    return name.lower().replace(" ", "_").replace("-", "_")


def classname(name):
    # Frappe deriva o nome da classe do controller como doctype.replace(" ", "")
    # (preserva maiúsculas — ex.: "Faturamento COAPH" -> "FaturamentoCOAPH").
    return name.replace(" ", "").replace("-", "")


def f(fieldname, fieldtype, label=None, options=None, reqd=0, in_list_view=0,
      read_only=0, default=None, description=None, in_standard_filter=0):
    d = {"fieldname": fieldname, "fieldtype": fieldtype}
    if label is not None:
        d["label"] = label
    if options is not None:
        d["options"] = "\n".join(options) if isinstance(options, list) else options
    if reqd:
        d["reqd"] = 1
    if in_list_view:
        d["in_list_view"] = 1
    if read_only:
        d["read_only"] = 1
    if default is not None:
        d["default"] = default
    if description:
        d["description"] = description
    if in_standard_filter:
        d["in_standard_filter"] = 1
    return d


def sec(fieldname, label):
    return {"fieldname": fieldname, "fieldtype": "Section Break", "label": label}


def col(fieldname):
    return {"fieldname": fieldname, "fieldtype": "Column Break"}


def series(prefix):
    return f("naming_series", "Select", "Série", options=[prefix])


def perms(owners, readers=None, financial=False):
    """owners: papéis com create/write/delete; readers: somente leitura."""
    readers = readers or []
    result = []
    seen = set()

    def add(role, level=0, write=0, create=0, delete=0, submit=0):
        if (role, level) in seen:
            return
        seen.add((role, level))
        result.append({
            "role": role, "permlevel": level,
            "read": 1, "write": write, "create": create,
            "delete": delete, "submit": submit,
            "report": 1, "export": 1, "share": 1, "print": 1, "email": 1,
        })

    add(SYS, write=1, create=1, delete=1)
    add(ADMIN, write=1, create=1, delete=1)
    for r in owners:
        add(r, write=1, create=1, delete=1)
    for r in readers:
        add(r)
    if not financial:
        add(DIRETORIA)
        add(CONSULTA)
    else:
        add(DIRETORIA)  # diretoria vê financeiro; consulta NÃO
    return result


def build(name, fields, naming_prefix=None, istable=0, title_field=None,
          owners=None, readers=None, financial=False, has_workflow=False,
          search_fields=None):
    doc = {
        "actions": [],
        "creation": TS,
        "doctype": "DocType",
        "editable_grid": 1,
        "engine": "InnoDB",
        "field_order": [x["fieldname"] for x in fields],
        "fields": fields,
        "index_web_pages_for_search": 1,
        "links": [],
        "modified": TS,
        "modified_by": "Administrator",
        "module": MODULE,
        "name": name,
        "owner": "Administrator",
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
    }
    if istable:
        doc["istable"] = 1
        doc["permissions"] = []
    else:
        doc["permissions"] = perms(owners or [], readers, financial)
        doc["track_changes"] = 1
        if naming_prefix:
            doc["autoname"] = "naming_series:"
            doc["naming_rule"] = 'By "Naming Series" field'
        if title_field:
            doc["title_field"] = title_field
            doc["show_title_field_in_link"] = 1
        if search_fields:
            doc["search_fields"] = ",".join(search_fields)
    if has_workflow:
        doc["allow_workflow"] = 1

    folder = os.path.join(BASE, scrub(name))
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, scrub(name) + ".json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    open(os.path.join(folder, "__init__.py"), "w").close()
    if not istable:
        ctrl = (
            "import frappe\n"
            "from frappe.model.document import Document\n\n\n"
            f"class {classname(name)}(Document):\n\tpass\n"
        )
    else:
        ctrl = (
            "from frappe.model.document import Document\n\n\n"
            f"class {classname(name)}(Document):\n\tpass\n"
        )
    with open(os.path.join(folder, scrub(name) + ".py"), "w", encoding="utf-8") as fh:
        fh.write(ctrl)
    return name


# ===================================================================
# 10.1 Contratante COAPH
# ===================================================================
build("Contratante COAPH", naming_prefix="CTNT-.#####", title_field="nome_contratante",
      owners=[COMERCIAL], readers=[JURIDICO, OPERACAO, FINANCEIRO, MOBILIZACAO, RH],
      search_fields=["razao_social", "cnpj"],
      fields=[
          series("CTNT-.#####"),
          f("nome_contratante", "Data", "Nome do Contratante", reqd=1, in_list_view=1),
          f("tipo_contratante", "Select", "Tipo de Contratante",
            options=["Público", "Privado", "Filantrópico", "Cooperativa", "Outro"], in_list_view=1),
          f("cnpj", "Data", "CNPJ", in_list_view=1),
          col("cb1"),
          f("razao_social", "Data", "Razão Social"),
          f("nome_fantasia", "Data", "Nome Fantasia"),
          f("status", "Select", "Status",
            options=["Ativo", "Inativo", "Prospect", "Bloqueado"], default="Ativo", in_list_view=1),
          sec("sec_end", "Endereço e Contato"),
          f("cidade", "Data", "Cidade"),
          f("estado", "Data", "Estado (UF)"),
          f("endereco", "Small Text", "Endereço"),
          col("cb2"),
          f("contato_principal", "Data", "Contato Principal"),
          f("email_contato", "Data", "E-mail de Contato"),
          f("telefone_contato", "Data", "Telefone de Contato"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.2 Unidade de Atendimento
# ===================================================================
build("Unidade Atendimento", naming_prefix="UNID-.#####", title_field="nome_unidade",
      owners=[COMERCIAL, OPERACAO], readers=[JURIDICO, FINANCEIRO, MOBILIZACAO, RH],
      fields=[
          series("UNID-.#####"),
          f("nome_unidade", "Data", "Nome da Unidade", reqd=1, in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", reqd=1, in_list_view=1),
          f("tipo_unidade", "Select", "Tipo de Unidade",
            options=["Hospital", "UPA", "Clínica", "Ambulatório", "Teleassistência", "Administrativo", "Outro"],
            in_list_view=1),
          col("cb1"),
          f("status", "Select", "Status",
            options=["Ativa", "Inativa", "Em mobilização"], default="Ativa", in_list_view=1),
          f("capacidade_atendimento", "Data", "Capacidade de Atendimento"),
          sec("sec_end", "Endereço e Contato"),
          f("cidade", "Data", "Cidade"),
          f("estado", "Data", "Estado (UF)"),
          f("endereco", "Small Text", "Endereço"),
          col("cb2"),
          f("contato_operacional", "Data", "Contato Operacional"),
          f("telefone_operacional", "Data", "Telefone Operacional"),
          f("email_operacional", "Data", "E-mail Operacional"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.3 Oportunidade COAPH  (workflow)
# ===================================================================
build("Oportunidade COAPH", naming_prefix="OPOR-.YYYY.-.#####", title_field="titulo",
      owners=[COMERCIAL], readers=[JURIDICO, OPERACAO, FINANCEIRO], has_workflow=True,
      fields=[
          series("OPOR-.YYYY.-.#####"),
          f("titulo", "Data", "Título", reqd=1, in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", in_list_view=1),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          f("origem", "Select", "Origem",
            options=["Indicação", "Prospecção", "Edital", "BID privado", "Renovação", "Demanda interna", "Outro"]),
          col("cb1"),
          f("tipo_cliente", "Select", "Tipo de Cliente", options=["Público", "Privado"]),
          f("tipo_servico", "Data", "Tipo de Serviço"),
          f("prioridade", "Select", "Prioridade",
            options=["Baixa", "Média", "Alta", "Crítica"], default="Média", in_list_view=1),
          f("status", "Select", "Status",
            options=["Demanda identificada", "Oportunidade registrada", "Oportunidade qualificada",
                     "Em análise de viabilidade", "Aprovada para avanço", "Descartada",
                     "Convertida em disputa/proposta"],
            default="Demanda identificada", in_list_view=1),
          sec("sec_valores", "Valores e Prazos"),
          f("valor_estimado_mensal", "Currency", "Valor Estimado Mensal (R$)"),
          f("valor_estimado_anual", "Currency", "Valor Estimado Anual (R$)"),
          f("probabilidade", "Percent", "Probabilidade (%)"),
          col("cb2"),
          f("data_identificacao", "Date", "Data de Identificação"),
          f("data_prevista_decisao", "Date", "Data Prevista de Decisão"),
          f("responsavel_comercial", "Link", "Responsável Comercial", options="User"),
          sec("sec_desc", "Descrição"),
          f("descricao", "Text", "Descrição"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.4 Análise de Viabilidade (workflow)
# ===================================================================
build("Analise Viabilidade", naming_prefix="VIAB-.YYYY.-.#####",
      owners=[COMERCIAL], readers=[JURIDICO, OPERACAO, FINANCEIRO], has_workflow=True,
      fields=[
          series("VIAB-.YYYY.-.#####"),
          f("oportunidade", "Link", "Oportunidade", options="Oportunidade COAPH", reqd=1, in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH"),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          col("cb1"),
          f("responsavel", "Link", "Responsável", options="User"),
          f("status", "Select", "Status",
            options=["Em análise técnica", "Em análise financeira", "Em análise jurídica",
                     "Aguardando comitê", "Aprovada", "Reprovada", "Revisão solicitada"],
            default="Em análise técnica", in_list_view=1),
          f("decisao", "Select", "Decisão", options=["", "Go", "No-Go", "Aguardar", "Revisar"], in_list_view=1),
          sec("sec_analises", "Análises"),
          f("analise_tecnica", "Text", "Análise Técnica"),
          f("analise_financeira", "Text", "Análise Financeira"),
          f("analise_juridica", "Text", "Análise Jurídica"),
          f("disponibilidade_cooperados", "Text", "Disponibilidade de Cooperados"),
          sec("sec_riscos", "Riscos e Margem"),
          f("margem_estimativa", "Percent", "Margem Estimada (%)"),
          f("risco_operacional", "Select", "Risco Operacional", options=["Baixo", "Médio", "Alto", "Crítico"]),
          col("cb2"),
          f("risco_juridico", "Select", "Risco Jurídico", options=["Baixo", "Médio", "Alto", "Crítico"]),
          f("risco_financeiro", "Select", "Risco Financeiro", options=["Baixo", "Médio", "Alto", "Crítico"]),
          sec("sec_decisao", "Parecer e Decisão"),
          f("parecer_final", "Text", "Parecer Final"),
          f("data_decisao", "Date", "Data da Decisão"),
          f("aprovador", "Link", "Aprovador", options="User"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.5 Disputa / Proposta COAPH (workflow)
# ===================================================================
build("Disputa Proposta COAPH", naming_prefix="DISP-.YYYY.-.#####", title_field="titulo",
      owners=[COMERCIAL], readers=[JURIDICO, OPERACAO, FINANCEIRO], has_workflow=True,
      fields=[
          series("DISP-.YYYY.-.#####"),
          f("titulo", "Data", "Título", reqd=1, in_list_view=1),
          f("oportunidade", "Link", "Oportunidade", options="Oportunidade COAPH"),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", in_list_view=1),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          col("cb1"),
          f("tipo_disputa", "Select", "Tipo de Disputa",
            options=["Licitação pública", "BID privado", "Proposta direta", "Cotação",
                     "Renovação competitiva", "Chamamento", "Outro"], in_list_view=1),
          f("modalidade", "Data", "Modalidade"),
          f("numero_edital_ou_bid", "Data", "Número do Edital/BID"),
          f("orgao_ou_empresa", "Data", "Órgão ou Empresa"),
          sec("sec_datas", "Datas"),
          f("data_publicacao", "Date", "Data de Publicação"),
          f("data_abertura", "Date", "Data de Abertura"),
          col("cb2"),
          f("data_envio_proposta", "Date", "Data de Envio da Proposta"),
          f("data_resultado", "Date", "Data do Resultado"),
          sec("sec_valores", "Valores"),
          f("valor_estimado", "Currency", "Valor Estimado (R$)"),
          f("valor_proposto", "Currency", "Valor Proposto (R$)"),
          col("cb3"),
          f("responsavel", "Link", "Responsável", options="User"),
          sec("sec_status", "Status e Resultado"),
          f("status", "Select", "Status",
            options=["Edital/BID recebido", "Em análise", "Documentação em preparação",
                     "Proposta em elaboração", "Proposta enviada", "Aguardando resultado",
                     "Vencida", "Perdida", "Cancelada"],
            default="Edital/BID recebido", in_list_view=1),
          f("resultado", "Select", "Resultado",
            options=["", "Em andamento", "Vencida", "Perdida", "Cancelada", "Sem resultado"], in_list_view=1),
          f("motivo_perda", "Small Text", "Motivo da Perda"),
          f("concorrentes", "Small Text", "Concorrentes"),
          sec("sec_docs", "Documentos e Observações"),
          f("documentos_obrigatorios", "Text", "Documentos Obrigatórios"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.6 Formalização Contratual (workflow)
# ===================================================================
build("Formalizacao Contratual", naming_prefix="FORM-.YYYY.-.#####",
      owners=[JURIDICO], readers=[COMERCIAL, OPERACAO, FINANCEIRO], has_workflow=True,
      fields=[
          series("FORM-.YYYY.-.#####"),
          f("disputa_proposta", "Link", "Disputa/Proposta", options="Disputa Proposta COAPH", in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", in_list_view=1),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          col("cb1"),
          f("responsavel_juridico", "Link", "Responsável Jurídico", options="User"),
          f("responsavel_comercial", "Link", "Responsável Comercial", options="User"),
          f("status", "Select", "Status",
            options=["Aguardando minuta", "Minuta em análise jurídica", "Minuta em negociação",
                     "Ajustes solicitados", "Aprovada juridicamente", "Em assinatura",
                     "Contrato assinado", "Contrato recusado", "Cancelada"],
            default="Aguardando minuta", in_list_view=1),
          sec("sec_minuta", "Minuta"),
          f("numero_minuta", "Data", "Número da Minuta"),
          f("versao_minuta", "Data", "Versão da Minuta"),
          f("data_recebimento_minuta", "Date", "Recebimento da Minuta"),
          col("cb2"),
          f("data_envio_ajustes", "Date", "Envio de Ajustes"),
          f("data_aprovacao_juridica", "Date", "Aprovação Jurídica"),
          f("data_assinatura", "Date", "Data de Assinatura"),
          sec("sec_juridico", "Análise Jurídica"),
          f("clausulas_criticas", "Text", "Cláusulas Críticas"),
          f("pendencias_juridicas", "Text", "Pendências Jurídicas"),
          f("parecer_juridico", "Text", "Parecer Jurídico"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.8 Serviço Contratado (child de Contrato 360)
# ===================================================================
build("Servico Contratado", istable=1,
      fields=[
          f("servico", "Data", "Serviço", in_list_view=1, reqd=1),
          f("especialidade", "Data", "Especialidade", in_list_view=1),
          f("unidade_medida", "Select", "Unidade de Medida",
            options=["Hora", "Plantão", "Atendimento", "Mensalidade", "Pacote", "Outro"], in_list_view=1),
          f("quantidade_prevista", "Float", "Qtd. Prevista", in_list_view=1),
          f("valor_unitario", "Currency", "Valor Unitário (R$)", in_list_view=1),
          f("valor_mensal_previsto", "Currency", "Valor Mensal Previsto (R$)", in_list_view=1),
          f("descricao", "Small Text", "Descrição"),
          f("observacoes", "Small Text", "Observações"),
      ])

# ===================================================================
# 10.7 Contrato 360 (DocType central, workflow)
# ===================================================================
build("Contrato 360", naming_prefix="CONT-.YYYY.-.#####", title_field="titulo_contrato",
      owners=[COMERCIAL, OPERACAO], readers=[JURIDICO, FINANCEIRO, MOBILIZACAO, RH],
      has_workflow=True, search_fields=["numero_contrato", "contratante"],
      fields=[
          sec("sec_id", "Identificação"),
          series("CONT-.YYYY.-.#####"),
          f("numero_contrato", "Data", "Número do Contrato", in_list_view=1),
          f("titulo_contrato", "Data", "Título do Contrato", reqd=1, in_list_view=1),
          col("cb_id"),
          f("tipo_contrato", "Select", "Tipo de Contrato",
            options=["Público", "Privado", "Emergencial", "Renovação", "Aditivo", "Outro"], in_list_view=1),
          f("origem", "Select", "Origem",
            options=["Licitação", "BID privado", "Proposta direta", "Renovação", "Aditivo"]),
          f("formalizacao_contratual", "Link", "Formalização Contratual", options="Formalizacao Contratual"),
          sec("sec_cliente", "Contratante e Unidade"),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", reqd=1, in_list_view=1),
          col("cb_cliente"),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          sec("sec_vigencia", "Vigência e Valores"),
          f("data_assinatura", "Date", "Data de Assinatura"),
          f("vigencia_inicio", "Date", "Início da Vigência"),
          f("vigencia_fim", "Date", "Fim da Vigência"),
          f("prazo_meses", "Int", "Prazo (meses)", read_only=1),
          col("cb_vig"),
          f("valor_mensal", "Currency", "Valor Mensal (R$)"),
          f("valor_anual", "Currency", "Valor Anual (R$)", read_only=1),
          f("valor_global", "Currency", "Valor Global (R$)"),
          f("indice_reajuste", "Select", "Índice de Reajuste",
            options=["IPCA", "IGPM", "INPC", "Fixo", "Outro"]),
          f("data_base_reajuste", "Date", "Data-base do Reajuste"),
          f("aviso_previo_dias", "Int", "Aviso Prévio (dias)"),
          sec("sec_status", "Status e Saúde"),
          f("status_contrato", "Select", "Status do Contrato",
            options=["Em formalização", "Em mobilização", "Operação assistida", "Ativo",
                     "Ativo com atenção", "Crítico", "Em renovação", "Suspenso",
                     "Em encerramento", "Encerrado"],
            default="Em formalização", in_list_view=1),
          col("cb_saude"),
          f("saude_contrato", "Select", "Saúde do Contrato",
            options=["Saudável", "Atenção", "Crítico", "Risco de perda"], default="Saudável", in_list_view=1),
          f("risco_renovacao", "Select", "Risco de Renovação",
            options=["Baixo", "Médio", "Alto", "Crítico"]),
          sec("sec_resp", "Responsáveis"),
          f("gestor_contrato", "Link", "Gestor do Contrato", options="User"),
          f("responsavel_operacional", "Link", "Responsável Operacional", options="User"),
          col("cb_resp"),
          f("responsavel_financeiro", "Link", "Responsável Financeiro", options="User"),
          f("responsavel_juridico", "Link", "Responsável Jurídico", options="User"),
          sec("sec_servicos", "Serviços Contratados"),
          f("servicos", "Table", "Serviços", options="Servico Contratado"),
          sec("sec_fin", "Parâmetros Financeiros"),
          f("condicao_pagamento", "Data", "Condição de Pagamento"),
          f("dia_previsto_faturamento", "Int", "Dia Previsto de Faturamento"),
          f("dia_previsto_recebimento", "Int", "Dia Previsto de Recebimento"),
          col("cb_fin"),
          f("centro_custo", "Data", "Centro de Custo"),
          f("conta_receita", "Data", "Conta de Receita"),
          f("retencoes_previstas", "Currency", "Retenções Previstas (R$)"),
          f("observacoes_financeiras", "Small Text", "Observações Financeiras"),
          sec("sec_op", "Parâmetros Operacionais"),
          f("tipo_servico", "Data", "Tipo de Serviço"),
          f("especialidades", "Small Text", "Especialidades"),
          f("volume_estimado", "Data", "Volume Estimado"),
          col("cb_op"),
          f("quantidade_cooperados_prevista", "Int", "Qtd. de Cooperados Prevista"),
          f("escala_prevista", "Data", "Escala Prevista"),
          f("sla_operacional", "Small Text", "SLA Operacional"),
          f("observacoes_operacionais", "Small Text", "Observações Operacionais"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.10 Etapa de Mobilização (child)
# ===================================================================
build("Etapa Mobilizacao", istable=1,
      fields=[
          f("etapa", "Data", "Etapa", in_list_view=1, reqd=1),
          f("area_responsavel", "Select", "Área Responsável",
            options=["Comercial", "Jurídico", "Operação", "RH", "Financeiro", "Diretoria", "TI"],
            in_list_view=1),
          f("responsavel", "Link", "Responsável", options="User", in_list_view=1),
          f("status", "Select", "Status",
            options=["Não iniciado", "Em andamento", "Concluído", "Atrasado", "Bloqueado"],
            default="Não iniciado", in_list_view=1),
          f("data_inicio_prevista", "Date", "Início Previsto"),
          f("data_fim_prevista", "Date", "Fim Previsto", in_list_view=1),
          f("data_conclusao", "Date", "Conclusão"),
          f("sla_dias", "Int", "SLA (dias)"),
          f("criterio_conclusao", "Small Text", "Critério de Conclusão"),
          f("descricao", "Small Text", "Descrição"),
          f("comentario", "Small Text", "Comentário"),
          f("anexo", "Attach", "Anexo"),
      ])

# ===================================================================
# 10.9 Plano de Mobilização (workflow)
# ===================================================================
build("Plano Mobilizacao", naming_prefix="MOBI-.YYYY.-.#####",
      owners=[MOBILIZACAO, RH], readers=[COMERCIAL, OPERACAO, JURIDICO], has_workflow=True,
      fields=[
          series("MOBI-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH", in_list_view=1),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          col("cb1"),
          f("responsavel_mobilizacao", "Link", "Responsável pela Mobilização", options="User"),
          f("status", "Select", "Status",
            options=["Aguardando kickoff", "Kickoff interno realizado", "Plano de mobilização definido",
                     "Contrato parametrizado", "Equipe dimensionada", "Cooperados em mobilização",
                     "Cooperados credenciados", "Onboarding concluído", "Operação liberada",
                     "Mobilização cancelada"],
            default="Aguardando kickoff", in_list_view=1),
          f("progresso_percentual", "Percent", "Progresso (%)", in_list_view=1),
          sec("sec_datas", "Datas"),
          f("data_kickoff_prevista", "Date", "Kickoff Previsto"),
          f("data_kickoff_realizada", "Date", "Kickoff Realizado"),
          col("cb2"),
          f("data_prevista_go_live", "Date", "Go-Live Previsto"),
          f("data_go_live", "Date", "Go-Live Realizado"),
          sec("sec_etapas", "Etapas da Mobilização"),
          f("etapas", "Table", "Etapas", options="Etapa Mobilizacao"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.11 Cooperado Mobilizado
# ===================================================================
build("Cooperado Mobilizado", naming_prefix="COOP-.#####", title_field="nome_cooperado",
      owners=[MOBILIZACAO, RH], readers=[OPERACAO, COMERCIAL],
      fields=[
          series("COOP-.#####"),
          f("nome_cooperado", "Data", "Nome do Cooperado", reqd=1, in_list_view=1),
          f("cpf", "Data", "CPF"),
          f("especialidade", "Data", "Especialidade", in_list_view=1),
          f("registro_profissional", "Data", "Registro Profissional"),
          col("cb1"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", in_list_view=1),
          f("plano_mobilizacao", "Link", "Plano de Mobilização", options="Plano Mobilizacao"),
          f("status_credenciamento", "Select", "Status do Credenciamento",
            options=["Solicitado", "Em análise", "Documentação pendente", "Credenciado",
                     "Treinamento pendente", "Apto", "Inativo", "Substituído"],
            default="Solicitado", in_list_view=1),
          sec("sec_datas", "Credenciamento e Onboarding"),
          f("data_solicitacao", "Date", "Data da Solicitação"),
          f("data_credenciamento", "Date", "Data do Credenciamento"),
          f("apto_para_operacao", "Check", "Apto para Operação"),
          col("cb2"),
          f("treinamento_realizado", "Check", "Onboarding Cooperativo Realizado"),
          f("data_treinamento", "Date", "Data do Onboarding"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.13 Item de Produção (child)
# ===================================================================
build("Item Producao", istable=1,
      fields=[
          f("cooperado", "Link", "Cooperado", options="Cooperado Mobilizado", in_list_view=1),
          f("servico", "Data", "Serviço", in_list_view=1),
          f("data", "Date", "Data", in_list_view=1),
          f("quantidade", "Float", "Quantidade", in_list_view=1),
          f("unidade_medida", "Select", "Unidade",
            options=["Hora", "Plantão", "Atendimento", "Mensalidade", "Pacote", "Outro"]),
          f("valor_unitario", "Currency", "Valor Unitário (R$)"),
          f("valor_total", "Currency", "Valor Total (R$)", in_list_view=1),
          f("status_validacao", "Select", "Status de Validação",
            options=["Registrado", "Em conferência", "Validado", "Contestado", "Glosado", "Corrigido"],
            default="Registrado", in_list_view=1),
          f("observacoes", "Small Text", "Observações"),
      ])

# ===================================================================
# 10.12 Ciclo Mensal de Medição (workflow)
# ===================================================================
build("Ciclo Mensal Medicao", naming_prefix="CICLO-.YYYY.-.#####", title_field="competencia",
      owners=[OPERACAO], readers=[FINANCEIRO, COMERCIAL, MOBILIZACAO], has_workflow=True,
      fields=[
          series("CICLO-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("competencia", "Data", "Competência (MM/AAAA)", reqd=1, in_list_view=1),
          f("mes", "Int", "Mês"),
          f("ano", "Int", "Ano"),
          col("cb1"),
          f("contratante", "Link", "Contratante", options="Contratante COAPH"),
          f("unidade_atendimento", "Link", "Unidade de Atendimento", options="Unidade Atendimento"),
          f("responsavel_operacional", "Link", "Responsável Operacional", options="User"),
          f("responsavel_financeiro", "Link", "Responsável Financeiro", options="User"),
          sec("sec_status", "Status"),
          f("status", "Select", "Status",
            options=["Competência aberta", "Produção em registro", "Produção em conferência",
                     "Produção fechada", "Produção validada", "Prazo de contestação",
                     "Liberada para faturamento", "NF emitida", "Aguardando recebimento",
                     "Recebida", "Repasse calculado", "Demonstrativos publicados",
                     "Repasse executado", "Competência encerrada", "Bloqueada"],
            default="Competência aberta", in_list_view=1),
          f("data_abertura", "Date", "Data de Abertura"),
          f("data_fechamento_prevista", "Date", "Fechamento Previsto"),
          f("data_fechamento_real", "Date", "Fechamento Real"),
          sec("sec_valores", "Valores Consolidados"),
          f("valor_producao", "Currency", "Valor de Produção (R$)"),
          f("valor_faturado", "Currency", "Valor Faturado (R$)"),
          col("cb2"),
          f("valor_recebido", "Currency", "Valor Recebido (R$)"),
          f("valor_repasse", "Currency", "Valor de Repasse (R$)"),
          sec("sec_itens", "Itens de Produção"),
          f("itens_producao", "Table", "Itens de Produção", options="Item Producao"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.14 Faturamento COAPH (financeiro)
# ===================================================================
build("Faturamento COAPH", naming_prefix="FAT-.YYYY.-.#####",
      owners=[FINANCEIRO], readers=[], financial=True,
      fields=[
          series("FAT-.YYYY.-.#####"),
          f("ciclo_mensal", "Link", "Ciclo Mensal", options="Ciclo Mensal Medicao", in_list_view=1),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", in_list_view=1),
          f("contratante", "Link", "Contratante", options="Contratante COAPH"),
          f("competencia", "Data", "Competência (MM/AAAA)"),
          col("cb1"),
          f("numero_nf", "Data", "Número da NF"),
          f("status", "Select", "Status",
            options=["Aguardando emissão", "NF emitida", "Enviada ao cliente",
                     "Aguardando recebimento", "Recebida", "Atrasada", "Cancelada"],
            default="Aguardando emissão", in_list_view=1),
          sec("sec_datas", "Datas e Valores"),
          f("data_emissao", "Date", "Data de Emissão"),
          f("data_envio_cliente", "Date", "Envio ao Cliente"),
          f("data_vencimento", "Date", "Vencimento"),
          col("cb2"),
          f("valor_bruto", "Currency", "Valor Bruto (R$)", in_list_view=1),
          f("retencoes", "Currency", "Retenções (R$)"),
          f("valor_liquido", "Currency", "Valor Líquido (R$)", in_list_view=1),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.15 Recebimento COAPH (financeiro)
# ===================================================================
build("Recebimento COAPH", naming_prefix="REC-.YYYY.-.#####",
      owners=[FINANCEIRO], readers=[], financial=True,
      fields=[
          series("REC-.YYYY.-.#####"),
          f("faturamento", "Link", "Faturamento", options="Faturamento COAPH", in_list_view=1),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", in_list_view=1),
          f("ciclo_mensal", "Link", "Ciclo Mensal", options="Ciclo Mensal Medicao"),
          col("cb1"),
          f("status", "Select", "Status",
            options=["Previsto", "Recebido parcial", "Recebido integral", "Atrasado",
                     "Divergente", "Cancelado"],
            default="Previsto", in_list_view=1),
          sec("sec_valores", "Datas e Valores"),
          f("data_prevista", "Date", "Data Prevista"),
          f("data_recebimento", "Date", "Data do Recebimento"),
          col("cb2"),
          f("valor_previsto", "Currency", "Valor Previsto (R$)", in_list_view=1),
          f("valor_recebido", "Currency", "Valor Recebido (R$)", in_list_view=1),
          f("diferenca", "Currency", "Diferença (R$)", read_only=1),
          sec("sec_obs", "Comprovante e Observações"),
          f("comprovante", "Attach", "Comprovante"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.17 Item de Repasse (child)
# ===================================================================
build("Item Repasse", istable=1,
      fields=[
          f("cooperado", "Link", "Cooperado", options="Cooperado Mobilizado", in_list_view=1),
          f("servico", "Data", "Serviço", in_list_view=1),
          f("quantidade", "Float", "Quantidade", in_list_view=1),
          f("valor_bruto", "Currency", "Valor Bruto (R$)", in_list_view=1),
          f("descontos", "Currency", "Descontos (R$)"),
          f("acrescimos", "Currency", "Acréscimos (R$)"),
          f("valor_liquido", "Currency", "Valor Líquido (R$)", in_list_view=1),
          f("status", "Select", "Status",
            options=["Calculado", "Conferido", "Demonstrativo publicado", "Pago", "Bloqueado", "Contestado"],
            default="Calculado", in_list_view=1),
          f("observacoes", "Small Text", "Observações"),
      ])

# ===================================================================
# 10.16 Repasse aos Cooperados (financeiro)
# ===================================================================
build("Repasse Cooperados", naming_prefix="REP-.YYYY.-.#####",
      owners=[FINANCEIRO], readers=[], financial=True,
      fields=[
          series("REP-.YYYY.-.#####"),
          f("ciclo_mensal", "Link", "Ciclo Mensal", options="Ciclo Mensal Medicao", in_list_view=1),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", in_list_view=1),
          f("competencia", "Data", "Competência (MM/AAAA)", in_list_view=1),
          col("cb1"),
          f("data_calculo", "Date", "Data do Cálculo"),
          f("responsavel", "Link", "Responsável", options="User"),
          f("status", "Select", "Status",
            options=["Aguardando recebimento", "Em cálculo", "Calculado", "Em conferência",
                     "Demonstrativos publicados", "Pagamento programado", "Pago",
                     "Bloqueado", "Cancelado"],
            default="Aguardando recebimento", in_list_view=1),
          sec("sec_valores", "Valores"),
          f("valor_total_producao", "Currency", "Valor Total de Produção (R$)"),
          f("valor_total_repasse", "Currency", "Valor Total de Repasse (R$)", in_list_view=1),
          col("cb2"),
          f("retencoes", "Currency", "Retenções (R$)"),
          f("ajustes", "Currency", "Ajustes (R$)"),
          sec("sec_itens", "Demonstrativo de Repasse (Itens)"),
          f("itens_repasse", "Table", "Itens de Repasse", options="Item Repasse"),
          sec("sec_obs", "Observações"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.18 Ocorrência Contratual
# ===================================================================
build("Ocorrencia Contratual", naming_prefix="OCOR-.YYYY.-.#####",
      owners=[OPERACAO], readers=[COMERCIAL, JURIDICO, FINANCEIRO, MOBILIZACAO],
      fields=[
          series("OCOR-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("ciclo_mensal", "Link", "Ciclo Mensal", options="Ciclo Mensal Medicao"),
          f("tipo_ocorrencia", "Select", "Tipo de Ocorrência",
            options=["Operacional", "Financeira", "Jurídica", "Cliente", "Cooperado",
                     "SLA", "Documental", "Sistema", "Outro"], in_list_view=1),
          col("cb1"),
          f("criticidade", "Select", "Criticidade",
            options=["Baixa", "Média", "Alta", "Crítica"], default="Média", in_list_view=1),
          f("status", "Select", "Status",
            options=["Aberta", "Em análise", "Em tratamento", "Aguardando terceiro",
                     "Resolvida", "Cancelada"],
            default="Aberta", in_list_view=1),
          f("responsavel", "Link", "Responsável", options="User"),
          sec("sec_desc", "Descrição e Tratamento"),
          f("descricao", "Text", "Descrição"),
          f("impacto", "Small Text", "Impacto"),
          f("data_abertura", "Date", "Data de Abertura"),
          col("cb2"),
          f("prazo_resolucao", "Date", "Prazo de Resolução"),
          f("data_resolucao", "Date", "Data de Resolução"),
          f("solucao", "Text", "Solução"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.19 Risco Contratual
# ===================================================================
build("Risco Contratual", naming_prefix="RISC-.YYYY.-.#####",
      owners=[OPERACAO], readers=[COMERCIAL, JURIDICO, FINANCEIRO],
      fields=[
          series("RISC-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("tipo_risco", "Select", "Tipo de Risco",
            options=["Renovação", "Financeiro", "Operacional", "Jurídico", "Reputacional",
                     "Cooperados", "Cliente", "Outro"], in_list_view=1),
          f("criticidade", "Select", "Criticidade",
            options=["Baixa", "Média", "Alta", "Crítica"], default="Média", in_list_view=1),
          col("cb1"),
          f("probabilidade", "Select", "Probabilidade", options=["Baixa", "Média", "Alta"]),
          f("impacto", "Select", "Impacto", options=["Baixo", "Médio", "Alto"]),
          f("status", "Select", "Status",
            options=["Identificado", "Em monitoramento", "Mitigação em andamento",
                     "Mitigado", "Materializado", "Encerrado"],
            default="Identificado", in_list_view=1),
          sec("sec_plano", "Descrição e Mitigação"),
          f("descricao", "Text", "Descrição"),
          f("plano_mitigacao", "Text", "Plano de Mitigação"),
          f("responsavel", "Link", "Responsável", options="User"),
          f("prazo", "Date", "Prazo"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.20 Renovação Contratual (workflow)
# ===================================================================
build("Renovacao Contratual", naming_prefix="RENO-.YYYY.-.#####",
      owners=[COMERCIAL], readers=[JURIDICO, OPERACAO, FINANCEIRO], has_workflow=True,
      fields=[
          series("RENO-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("vigencia_atual_fim", "Date", "Fim da Vigência Atual", in_list_view=1),
          f("dias_para_vencimento", "Int", "Dias para Vencimento", in_list_view=1),
          col("cb1"),
          f("responsavel_renovacao", "Link", "Responsável pela Renovação", options="User"),
          f("estrategia", "Select", "Estratégia",
            options=["Renovar", "Renegociar", "Reprecificar", "Aditivar", "Encerrar", "Aguardar"]),
          f("status", "Select", "Status",
            options=["Monitorando vigência", "Alerta 180 dias", "Alerta 120 dias", "Alerta 90 dias",
                     "Em análise de renovação", "Em negociação", "Minuta de renovação",
                     "Renovado", "Não renovado", "Encerrado"],
            default="Monitorando vigência", in_list_view=1),
          sec("sec_alertas", "Marcos de Alerta"),
          f("data_alerta_180", "Date", "Alerta 180 dias"),
          f("data_alerta_120", "Date", "Alerta 120 dias"),
          f("data_alerta_90", "Date", "Alerta 90 dias"),
          col("cb_al"),
          f("data_alerta_60", "Date", "Alerta 60 dias"),
          f("data_alerta_30", "Date", "Alerta 30 dias"),
          sec("sec_reajuste", "Reajuste e Valores"),
          f("indice_reajuste", "Select", "Índice de Reajuste",
            options=["IPCA", "IGPM", "INPC", "Fixo", "Outro"]),
          f("percentual_reajuste_proposto", "Percent", "Reajuste Proposto (%)"),
          f("novo_valor_mensal", "Currency", "Novo Valor Mensal (R$)"),
          sec("sec_pareceres", "Pareceres e Decisão"),
          f("parecer_comercial", "Small Text", "Parecer Comercial"),
          f("parecer_operacional", "Small Text", "Parecer Operacional"),
          f("parecer_financeiro", "Small Text", "Parecer Financeiro"),
          f("parecer_juridico", "Small Text", "Parecer Jurídico"),
          col("cb_dec"),
          f("decisao_final", "Small Text", "Decisão Final"),
          f("data_decisao", "Date", "Data da Decisão"),
          f("observacoes", "Text", "Observações"),
      ])

# ===================================================================
# 10.21 Pendência Contratual
# ===================================================================
build("Pendencia Contratual", naming_prefix="PEND-.YYYY.-.#####",
      owners=[OPERACAO, MOBILIZACAO, COMERCIAL, JURIDICO, FINANCEIRO],
      readers=[],
      fields=[
          series("PEND-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", in_list_view=1),
          f("ciclo_mensal", "Link", "Ciclo Mensal", options="Ciclo Mensal Medicao"),
          f("area", "Select", "Área",
            options=["Comercial", "Jurídico", "Operação", "RH", "Financeiro", "Diretoria", "TI", "Cliente"],
            in_list_view=1),
          f("tipo_pendencia", "Data", "Tipo de Pendência"),
          col("cb1"),
          f("prioridade", "Select", "Prioridade",
            options=["Baixa", "Média", "Alta", "Crítica"], default="Média", in_list_view=1),
          f("status", "Select", "Status",
            options=["Aberta", "Em andamento", "Aguardando terceiro", "Bloqueada",
                     "Concluída", "Cancelada"],
            default="Aberta", in_list_view=1),
          f("responsavel", "Link", "Responsável", options="User"),
          f("solicitante", "Link", "Solicitante", options="User"),
          sec("sec_desc", "Descrição e Prazos"),
          f("descricao", "Text", "Descrição"),
          f("impacto", "Small Text", "Impacto"),
          f("data_abertura", "Date", "Data de Abertura"),
          col("cb2"),
          f("prazo", "Date", "Prazo"),
          f("data_conclusao", "Date", "Data de Conclusão"),
          f("comentario_final", "Small Text", "Comentário Final"),
      ])

# ===================================================================
# 10.22 Aditivo Contratual
# ===================================================================
build("Aditivo Contratual", naming_prefix="ADIT-.YYYY.-.#####",
      owners=[JURIDICO, COMERCIAL], readers=[OPERACAO, FINANCEIRO],
      fields=[
          series("ADIT-.YYYY.-.#####"),
          f("contrato", "Link", "Contrato 360", options="Contrato 360", reqd=1, in_list_view=1),
          f("tipo_aditivo", "Select", "Tipo de Aditivo",
            options=["Prazo", "Valor", "Escopo", "Reajuste", "Serviço", "Outro"], in_list_view=1),
          f("numero_aditivo", "Data", "Número do Aditivo"),
          col("cb1"),
          f("status", "Select", "Status",
            options=["Em elaboração", "Em análise jurídica", "Em negociação",
                     "Em assinatura", "Assinado", "Cancelado"],
            default="Em elaboração", in_list_view=1),
          f("responsavel_juridico", "Link", "Responsável Jurídico", options="User"),
          f("responsavel_comercial", "Link", "Responsável Comercial", options="User"),
          sec("sec_datas", "Datas e Vigência"),
          f("data_solicitacao", "Date", "Data da Solicitação"),
          f("data_assinatura", "Date", "Data de Assinatura"),
          f("vigencia_inicio", "Date", "Início da Vigência"),
          f("vigencia_fim", "Date", "Fim da Vigência"),
          sec("sec_valores", "Valores e Alteração"),
          f("valor_anterior", "Currency", "Valor Anterior (R$)"),
          f("valor_novo", "Currency", "Valor Novo (R$)"),
          col("cb2"),
          f("descricao_alteracao", "Text", "Descrição da Alteração"),
          f("observacoes", "Text", "Observações"),
      ])

print("DocTypes gerados em:", BASE)
