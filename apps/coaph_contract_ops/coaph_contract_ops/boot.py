"""Ajustes de bootinfo do SGC COAPH.

Filtra o launcher (/desk) — o array `bootinfo.desktop_icons` (ver
frappe/desk/doctype/desktop_icon/desktop_icon.get_desktop_icons) — para que
usuários operacionais da Coaph vejam APENAS o ícone "Contratos".

Usa allowlist por PAPEL (não blocklist): à prova de upgrade — se o ERPNext
adicionar novos ícones numa versão futura, eles não vazam para o perfil SGC.
Administrator e System Manager NÃO são afetados (veem tudo — requisito).
"""

import frappe

LABELS_PERMITIDOS = {"Contratos", "My Workspaces"}

SGC_ROLES = {
    "SGC Administrador", "SGC Diretoria", "SGC Comercial", "SGC Juridico",
    "SGC Mobilizacao", "SGC Operacao", "SGC Financeiro", "SGC RH Cooperados",
    "SGC Consulta",
}


def filtrar_launcher(bootinfo):
    """Hook extend_bootinfo: no launcher, deixa só 'Contratos' para perfis SGC."""
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles())
    if "System Manager" in roles:
        return  # admin técnico vê tudo
    if not (roles & SGC_ROLES):
        return  # usuários não-SGC: não mexe

    icons = bootinfo.get("desktop_icons") or []
    bootinfo["desktop_icons"] = [
        ic for ic in icons if ic.get("label") in LABELS_PERMITIDOS
    ]
