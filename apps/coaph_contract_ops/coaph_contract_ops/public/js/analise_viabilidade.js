frappe.ui.form.on("Analise Viabilidade", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.status === "Aprovada") {
			frm.add_custom_button(__("Criar Disputa/Proposta"), () => {
				frappe.call({
					method: "coaph_contract_ops.coaph_contract_ops.automation.actions.criar_disputa",
					args: { viabilidade: frm.doc.name },
					freeze: true,
					callback: (r) => r.message && frappe.set_route("Form", "Disputa Proposta COAPH", r.message),
				});
			}, __("Avançar"));
		}
	},
});
