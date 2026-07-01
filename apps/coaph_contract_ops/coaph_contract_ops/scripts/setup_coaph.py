"""Setup de usuários/dados básicos da COAPH (idempotente).

Uso:
    bench --site <site> execute \
      coaph_contract_ops.scripts.setup_coaph.criar_gestor_contratos
"""

import frappe

RAYLSSON_EMAIL = "licitacao@coaph.com.br"

MODULO_COAPH = "COAPH Contract Ops"
MODULE_PROFILE = "SGC - Apenas Contratos"
WORKSPACE_SGC = "SGC COAPH"


def configurar_navegacao_sgc():
    """Fase 1 + 2 da limpeza de UX:

    1. Bloqueia TODOS os módulos não-COAPH (sujeira do ERPNext/Frappe) para os
       usuários SGC, via um Module Profile reutilizável. O Administrator e
       qualquer System Manager ficam intocados (veem tudo).
    2. Define o workspace inicial dos usuários SGC como 'SGC COAPH' (o login
       cai direto no Cockpit, nunca no 'Home' do ERPNext).

    Idempotente: pode rodar a cada deploy / para cada novo usuário SGC.
    """
    bloqueados = [m for m in frappe.get_all("Module Def", pluck="name")
                  if m != MODULO_COAPH]

    # 1) Module Profile reutilizável -------------------------------------------
    if frappe.db.exists("Module Profile", MODULE_PROFILE):
        mp = frappe.get_doc("Module Profile", MODULE_PROFILE)
        mp.set("block_modules", [])
    else:
        mp = frappe.new_doc("Module Profile")
        mp.module_profile_name = MODULE_PROFILE
    for m in bloqueados:
        mp.append("block_modules", {"module": m})
    mp.save(ignore_permissions=True)

    # 2) Aplica aos usuários SGC (papel 'SGC %'), exceto System Manager/Admin ---
    sgc_users = set(frappe.get_all(
        "Has Role", filters={"role": ["like", "SGC %"], "parenttype": "User"},
        pluck="parent"))
    alvo = []
    for email in sgc_users:
        if email in ("Administrator", "Guest"):
            continue
        papeis = set(frappe.get_roles(email))
        if "System Manager" in papeis:
            continue  # admin técnico vê tudo
        alvo.append(email)

    for email in alvo:
        user = frappe.get_doc("User", email)
        user.module_profile = MODULE_PROFILE
        user.set("block_modules", [])
        for m in bloqueados:
            user.append("block_modules", {"module": m})
        user.default_workspace = WORKSPACE_SGC
        user.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    print(f"Navegação SGC configurada: {len(bloqueados)} módulos bloqueados; "
          f"usuários ajustados: {alvo or '(nenhum)'}; workspace inicial = {WORKSPACE_SGC}.")
    return {"bloqueados": len(bloqueados), "usuarios": alvo}


def concluir_setup_wizard():
    """Marca o setup do site como concluído com os padrões brasileiros.

    Sem isso, o Frappe redireciona TODO login para /desk/setup-wizard, e
    usuários não-administradores recebem 'Not permitted'. Idempotente.
    """
    frappe.db.set_single_value("System Settings", {
        "setup_complete": 1,
        "country": "Brazil",
        "time_zone": "America/Fortaleza",
        "language": "pt-BR",
        "date_format": "dd/mm/yyyy",
        "number_format": "#.###,##",
    })
    # Global Defaults via doc.save() para disparar o on_update, que propaga o
    # default global 'currency' (sem isso os campos Currency renderizam em ₹/INR).
    gd = frappe.get_doc("Global Defaults")
    gd.default_currency = "BRL"
    gd.country = "Brazil"
    gd.save(ignore_permissions=True)
    # NA v15+ o boot usa frappe.is_setup_complete(), que exige is_setup_complete=1
    # nos registros de Installed Application de frappe e erpnext. Sem isso, todo
    # login é redirecionado para /desk/setup-wizard.
    for app in ("frappe", "erpnext", "coaph_contract_ops"):
        if frappe.db.exists("Installed Application", {"app_name": app}):
            frappe.db.set_value("Installed Application", {"app_name": app},
                                "is_setup_complete", 1)
    frappe.db.set_default("desktop:home_page", "workspace")
    frappe.db.commit()
    frappe.clear_cache()
    print("Setup do site concluído (is_setup_complete=1 p/ frappe+erpnext, padrões BR).")


LOGO_COR = "/assets/coaph_contract_ops/images/coaph/coaph-logo-color.png"
LOGO_BRANCA = "/assets/coaph_contract_ops/images/coaph/coaph-logo-white.png"
FAVICON = "/assets/coaph_contract_ops/images/coaph/coaph-favicon.png"
APP_NAME = "SGC COAPH"


# Traduções pt-BR de strings comuns da UI que o Frappe entrega sem tradução.
# Entram como registros do DocType "Translation" (mesclados em runtime, duráveis).
TRADUCOES_PTBR = {
    # Login
    "Login": "Entrar",
    "Login to {0}": "Entrar em {0}",
    "Forgot Password?": "Esqueceu a senha?",
    "Login with Email Link": "Entrar com link por e-mail",
    "Send login link": "Enviar link de acesso",
    "Sign Up": "Cadastrar",
    "Show": "Mostrar",
    "Hide": "Ocultar",
    "Email": "E-mail",
    "Password": "Senha",
    "Back to Login": "Voltar ao login",
    # Navegação / chrome
    "Search": "Buscar",
    "Search or type a command": "Buscar ou digitar um comando",
    "Notifications": "Notificações",
    "Help": "Ajuda",
    "Settings": "Configurações",
    "My Settings": "Minhas Configurações",
    "Logout": "Sair",
    "Toggle Theme": "Alternar Tema",
    "About": "Sobre",
    "Edit Profile": "Editar Perfil",
    "Reset Desktop Layout": "Redefinir Layout",
    "Apps": "Aplicativos",
    "Home": "Início",
    "Loading...": "Carregando...",
    # Lista / relatório
    "Add": "Adicionar",
    "New": "Novo",
    "Refresh": "Atualizar",
    "Menu": "Menu",
    "Filter By": "Filtrar por",
    "Sort By": "Ordenar por",
    "Last Updated On": "Última Atualização",
    "Created On": "Criado em",
    "Assigned To": "Atribuído a",
    "List View": "Lista",
    "Report View": "Relatório",
    "Load More": "Carregar mais",
    "Select All": "Selecionar tudo",
    "Actions": "Ações",
    "Bulk Edit": "Edição em massa",
    "No records found": "Nenhum registro encontrado",
    "results": "resultados",
    "Saved Filters": "Filtros Salvos",
    # Formulário
    "Save": "Salvar",
    "Cancel": "Cancelar",
    "Submit": "Registrar",
    "Edit": "Editar",
    "Duplicate": "Duplicar",
    "Print": "Imprimir",
    "Attachments": "Anexos",
    "Comments": "Comentários",
    "Add a comment": "Adicionar um comentário",
    "Type a reply / comment": "Escreva uma resposta / comentário",
    "Assign": "Atribuir",
    "Assign To": "Atribuir a",
    "Share": "Compartilhar",
    "Tags": "Etiquetas",
    "New Email": "Novo E-mail",
    "Activity": "Atividade",
    "Connections": "Conexões",
    "Created": "Criado",
    "You": "Você",
    "just now": "agora",
    "Not Saved": "Não Salvo",
    "This form is not editable due to a Workflow.":
        "Este formulário não é editável devido a um Workflow.",
    # Comuns
    "Yes": "Sim",
    "No": "Não",
    "Close": "Fechar",
    "Confirm": "Confirmar",
    "Are you sure you want to proceed?": "Tem certeza de que deseja continuar?",
    "Success": "Sucesso",
    "Error": "Erro",
    "Warning": "Aviso",
    "Please try again": "Tente novamente",
    "Not permitted": "Sem permissão",
    "Add Row": "Adicionar Linha",
    "Delete": "Excluir",
    "Today": "Hoje",
    "Clear": "Limpar",
    "Apply": "Aplicar",
    "Download": "Baixar",
    "Export": "Exportar",
    "Import": "Importar",
}


def aplicar_traducoes_ptbr():
    """Garante o idioma pt-BR e supre traduções comuns ausentes (via Translation).
    Idempotente."""
    frappe.db.set_single_value("System Settings", "language", "pt-BR")
    # Idioma em todos os usuários do sistema
    for u in frappe.get_all("User", filters={"user_type": "System User"}, pluck="name"):
        if u != "Guest":
            frappe.db.set_value("User", u, "language", "pt-BR", update_modified=False)

    criadas = 0
    for origem, destino in TRADUCOES_PTBR.items():
        existe = frappe.db.exists("Translation",
                                  {"language": "pt-BR", "source_text": origem, "context": ["in", ["", None]]})
        if existe:
            frappe.db.set_value("Translation", existe, "translated_text", destino)
            continue
        frappe.get_doc({
            "doctype": "Translation",
            "language": "pt-BR",
            "source_text": origem,
            "translated_text": destino,
        }).insert(ignore_permissions=True)
        criadas += 1

    frappe.db.commit()
    frappe.clear_cache()
    print(f"Traduções pt-BR aplicadas: {criadas} novas de {len(TRADUCOES_PTBR)}; idioma pt-BR em usuários e sistema.")


def aplicar_identidade_visual():
    """Aplica a identidade da Coaph nas configurações que vivem no banco
    (logo, favicon, splash, nome do app) e cria o Letter Head para impressão.
    Idempotente. O CSS de marca e o logo das telas vêm dos hooks/assets.
    """
    # Navbar
    nav = frappe.get_doc("Navbar Settings")
    nav.app_logo = LOGO_COR
    nav.save(ignore_permissions=True)

    # Website / login / splash / favicon / nome
    ws = frappe.get_doc("Website Settings")
    ws.app_name = APP_NAME
    ws.app_logo = LOGO_COR
    ws.favicon = FAVICON
    ws.splash_image = LOGO_COR
    ws.footer_logo = LOGO_BRANCA
    ws.save(ignore_permissions=True)

    frappe.db.set_single_value("System Settings", "app_name", APP_NAME)

    # Letter Head para impressão de contratos/documentos
    _criar_letter_head()

    frappe.db.commit()
    frappe.clear_cache()
    print(f"Identidade visual aplicada: logo/favicon/splash + app_name='{APP_NAME}' + Letter Head COAPH.")


def _criar_letter_head():
    nome = "COAPH"
    cabecalho = (
        '<div style="display:flex;align-items:center;gap:12px;'
        'border-bottom:3px solid #bd0717;padding-bottom:8px;">'
        f'<img src="{LOGO_COR}" style="height:48px;border-radius:6px;">'
        '<div style="line-height:1.2;">'
        '<div style="font-size:16px;font-weight:700;color:#7c0813;">COAPH</div>'
        '<div style="font-size:11px;color:#404040;">Cooperativa de Atendimento Pré e Hospitalar</div>'
        '</div></div>'
    )
    rodape = (
        '<div style="border-top:1px solid #ddd;padding-top:6px;margin-top:8px;'
        'font-size:10px;color:#888;text-align:center;">'
        'SGC COAPH — Gestão 360 de Contratos · documento gerado pelo sistema</div>'
    )
    if frappe.db.exists("Letter Head", nome):
        lh = frappe.get_doc("Letter Head", nome)
    else:
        lh = frappe.new_doc("Letter Head")
        lh.letter_head_name = nome
    lh.content = cabecalho
    lh.footer = rodape
    lh.is_default = 1
    lh.disabled = 0
    lh.save(ignore_permissions=True)


def criar_gestor_contratos():
    """Cria o usuário do gestor de contratos (Raylsson) como SGC Administrador
    e o define como gestor padrão dos contratos sem gestor."""
    if not frappe.db.exists("User", RAYLSSON_EMAIL):
        user = frappe.get_doc({
            "doctype": "User",
            "email": RAYLSSON_EMAIL,
            "first_name": "Raylsson",
            "last_name": "Almeida",
            "send_welcome_email": 0,
            "user_type": "System User",
        })
        user.insert(ignore_permissions=True)
        print(f"Usuário criado: {RAYLSSON_EMAIL}")
    else:
        user = frappe.get_doc("User", RAYLSSON_EMAIL)
        print(f"Usuário já existe: {RAYLSSON_EMAIL}")

    # SGC Administrador = vê tudo. SGC Operacao/Comercial = papéis exigidos pelo
    # Workflow Contrato 360 (allow_edit) para poder EDITAR e mover os contratos.
    for role in ("SGC Administrador", "SGC Operacao", "SGC Comercial"):
        if not any(r.role == role for r in user.get("roles", [])):
            user.append("roles", {"role": role})
    user.save(ignore_permissions=True)
    print("Papéis:", [r.role for r in user.roles])

    # Define como gestor padrão dos contratos que ainda não têm gestor.
    sem_gestor = frappe.get_all("Contrato 360",
                                filters={"gestor_contrato": ["in", ["", None]]},
                                pluck="name")
    for nome in sem_gestor:
        frappe.db.set_value("Contrato 360", nome, "gestor_contrato",
                            RAYLSSON_EMAIL, update_modified=False)
    frappe.db.commit()
    print(f"Definido como gestor em {len(sem_gestor)} contratos.")
    return RAYLSSON_EMAIL
