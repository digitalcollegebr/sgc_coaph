frappe.ui.form.on("Oportunidade COAPH", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Criar Análise de Viabilidade"), () => {
			frappe.call({
				method: "coaph_contract_ops.coaph_contract_ops.automation.actions.criar_viabilidade",
				args: { oportunidade: frm.doc.name },
				freeze: true,
				callback: (r) => r.message && frappe.set_route("Form", "Analise Viabilidade", r.message),
			});
		}, __("Avançar"));
	},
});
