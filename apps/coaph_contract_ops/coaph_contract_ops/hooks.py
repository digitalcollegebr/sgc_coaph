app_name = "coaph_contract_ops"
app_title = "COAPH Contract Ops"
app_publisher = "COAPH"
app_description = "SGC COAPH — Gestão 360 de Contratos"
app_email = "ti@coaph.example.org"
app_license = "Projeto interno COAPH"

# Documentação amigável do produto
# Nome do produto: SGC COAPH — Gestão 360 de Contratos

# ------------------------------------------------------------------
# Fixtures — exporta as customizações deste app (nunca toca o core).
# Filtramos por módulo/nome para não arrastar registros de outros apps.
# ------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "SGC Administrador",
        "SGC Diretoria",
        "SGC Comercial",
        "SGC Juridico",
        "SGC Mobilizacao",
        "SGC Operacao",
        "SGC Financeiro",
        "SGC RH Cooperados",
        "SGC Consulta",
    ]]]},
    {"dt": "Workflow State"},
    {"dt": "Workflow Action Master"},
    {"dt": "Workflow", "filters": [["name", "in", [
        "Workflow Oportunidade COAPH",
        "Workflow Analise Viabilidade",
        "Workflow Disputa Proposta COAPH",
        "Workflow Formalizacao Contratual",
        "Workflow Contrato 360",
        "Workflow Plano Mobilizacao",
        "Workflow Ciclo Mensal Medicao",
        "Workflow Renovacao Contratual",
    ]]]},
    {"dt": "Workspace", "filters": [["module", "=", "COAPH Contract Ops"]]},
    {"dt": "Custom Field", "filters": [["module", "=", "COAPH Contract Ops"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "COAPH Contract Ops"]]},
    {"dt": "Dashboard Chart", "filters": [["module", "=", "COAPH Contract Ops"]]},
    {"dt": "Number Card", "filters": [["module", "=", "COAPH Contract Ops"]]},
    {"dt": "Notification", "filters": [["name", "in", [
        "Notificacao de Producao Validada",
        "Notificacao de Faturamento Emitido",
        "Notificacao de Demonstrativos Publicados",
        "Notificacao de Repasse Concluido",
        "Alerta de Pendencia Critica",
        "Alerta de Contrato Critico",
    ]]]},
]

# ------------------------------------------------------------------
# Client Scripts — botões "Criar ..." nos formulários (seção 13).
# ------------------------------------------------------------------
doctype_js = {
    "Oportunidade COAPH": "public/js/oportunidade_coaph.js",
    "Analise Viabilidade": "public/js/analise_viabilidade.js",
    "Disputa Proposta COAPH": "public/js/disputa_proposta_coaph.js",
    "Formalizacao Contratual": "public/js/formalizacao_contratual.js",
    "Contrato 360": "public/js/contrato_360.js",
    "Ciclo Mensal Medicao": "public/js/ciclo_mensal_medicao.js",
}

# ------------------------------------------------------------------
# Document Events — automações entre documentos.
# A lógica vive em controllers/funções deste app (sem alterar core).
# ------------------------------------------------------------------
doc_events = {
    "Contrato 360": {
        "validate": "coaph_contract_ops.coaph_contract_ops.automation.contrato.validate_contrato",
    },
}

# ------------------------------------------------------------------
# Scheduler — tarefas diárias de governança contratual.
# ------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "coaph_contract_ops.coaph_contract_ops.automation.scheduler.verificar_renovacoes",
        "coaph_contract_ops.coaph_contract_ops.automation.scheduler.verificar_mobilizacoes_atrasadas",
    ],
}

# Idioma padrão da interface
# (a tradução fina dos labels é feita por DocType; aqui só registramos o app)
