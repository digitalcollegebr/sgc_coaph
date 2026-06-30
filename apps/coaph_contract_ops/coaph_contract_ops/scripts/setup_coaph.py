"""Setup de usuários/dados básicos da COAPH (idempotente).

Uso:
    bench --site <site> execute \
      coaph_contract_ops.scripts.setup_coaph.criar_gestor_contratos
"""

import frappe

RAYLSSON_EMAIL = "licitacao@coaph.com.br"


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
    for app in ("frappe", "erpnext"):
        if frappe.db.exists("Installed Application", {"app_name": app}):
            frappe.db.set_value("Installed Application", {"app_name": app},
                                "is_setup_complete", 1)
    frappe.db.set_default("desktop:home_page", "workspace")
    frappe.db.commit()
    frappe.clear_cache()
    print("Setup do site concluído (is_setup_complete=1 p/ frappe+erpnext, padrões BR).")


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
