"""Setup de usuários/dados básicos da COAPH (idempotente).

Uso:
    bench --site <site> execute \
      coaph_contract_ops.scripts.setup_coaph.criar_gestor_contratos
"""

import frappe

RAYLSSON_EMAIL = "licitacao@coaph.com.br"


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

    for role in ("SGC Administrador",):
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
