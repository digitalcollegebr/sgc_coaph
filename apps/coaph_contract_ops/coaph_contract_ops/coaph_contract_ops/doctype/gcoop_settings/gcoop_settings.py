import frappe
from frappe.model.document import Document


class GCOOPSettings(Document):
    pass


@frappe.whitelist()
def sincronizar_agora():
    """Chamado pelo botão 'Sincronizar agora' do formulário GCOOP Settings."""
    from coaph_contract_ops.integrations.gcoop.sync import sincronizar_contratos
    return sincronizar_contratos()
