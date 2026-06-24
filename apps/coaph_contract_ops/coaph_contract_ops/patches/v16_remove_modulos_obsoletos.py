"""Limpeza para upgrade v15 -> v16.

Alguns módulos do Frappe (ex.: "Social") foram removidos na v16. Sites criados
na v15 mantêm um `Module Def` órfão no banco que quebra o sync de schema durante
o `bench migrate` (ModuleNotFoundError: No module named 'frappe.social').

Este patch roda em pre_model_sync (antes do sync) e remove esses Module Def
órfãos, permitindo a migração sem intervenção manual. Não altera código core —
apenas remove um registro de dados sem módulo correspondente.
"""

import os

import frappe

# Módulos removidos na v16 (app de origem -> nome do Module Def)
MODULOS_REMOVIDOS = [("frappe", "Social")]


def execute():
    for app, modulo in MODULOS_REMOVIDOS:
        if not frappe.db.exists("Module Def", modulo):
            continue
        # confirma que realmente não há o pacote/pasta do módulo instalado
        try:
            app_path = frappe.get_app_path(app)
        except Exception:  # noqa: BLE001
            app_path = None
        pasta = os.path.join(app_path, frappe.scrub(modulo)) if app_path else None
        if pasta and os.path.isdir(pasta):
            continue  # ainda existe; não remover
        frappe.db.delete("Module Def", {"name": modulo})
        frappe.db.commit()
        print(f"[coaph_contract_ops] Module Def órfão removido: {modulo}")
