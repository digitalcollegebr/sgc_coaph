app_name = "coaph_contract_ops"
app_title = "SGC COAPH"
app_publisher = "COAPH"
app_description = "SGC COAPH — Gestão 360 de Contratos"
app_email = "ti@coaph.example.org"
app_license = "Projeto interno COAPH"

# Documentação amigável do produto
# Nome do produto: SGC COAPH — Gestão 360 de Contratos

# ------------------------------------------------------------------
# Identidade visual da Coaph (sem fork do core).
# CSS de marca injetado no Desk e no portal/login; logo nas telas.
# Os assets em /assets/coaph_contract_ops/... vêm de public/ após build.
# ------------------------------------------------------------------
app_logo_url = "/assets/coaph_contract_ops/images/coaph/coaph-logo-color.png"
app_include_css = "/assets/coaph_contract_ops/css/coaph_brand.css"
web_include_css = "/assets/coaph_contract_ops/css/coaph_brand.css"

# Registro do "app" na tela de apps / cabeçalho da barra lateral (v15+):
# define a logo (tile vermelho) e o nome "SGC COAPH" no switcher/launcher.
add_to_apps_screen = [
    {
        "name": "coaph_contract_ops",
        "logo": "/assets/coaph_contract_ops/images/coaph/coaph-logo-color.png",
        "title": "SGC COAPH",
        "route": "/app/sgc-coaph",
    }
]

# Launcher /desk: mantém só o ícone "Contratos" para usuários operacionais
# (Administrator/System Manager veem tudo). Ver coaph_contract_ops/boot.py.
extend_bootinfo = [
    "coaph_contract_ops.boot.filtrar_launcher",
]

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
    # IMPORTANTE: Workspace por ÚLTIMO — depende de Number Card/Dashboard Chart/
    # Page/Report já existirem. Na v16 a importação é estrita e, se o workspace
    # vier antes, suas referências falham e ele não é criado.
    {"dt": "Workspace", "filters": [["module", "=", "COAPH Contract Ops"]]},
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
    "Recebimento COAPH": {
        "validate": "coaph_contract_ops.coaph_contract_ops.automation.rollup.recebimento_validate",
        "on_update": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
        "on_trash": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
    },
    "Faturamento COAPH": {
        "on_update": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
        "on_trash": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
    },
    "Repasse Cooperados": {
        "on_update": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
        "on_trash": "coaph_contract_ops.coaph_contract_ops.automation.rollup.atualizar_ciclo",
    },
}

# ------------------------------------------------------------------
# Scheduler — tarefas diárias de governança contratual.
# ------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "coaph_contract_ops.coaph_contract_ops.automation.scheduler.verificar_renovacoes",
        "coaph_contract_ops.coaph_contract_ops.automation.scheduler.verificar_mobilizacoes_atrasadas",
        # Sincroniza contratos do GCOOP (só roda se a integração estiver ativa).
        "coaph_contract_ops.integrations.gcoop.sync.sincronizar_agendado",
    ],
}

# Idioma padrão da interface
# (a tradução fina dos labels é feita por DocType; aqui só registramos o app)
