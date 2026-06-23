frappe.ui.form.on("Disputa Proposta COAPH", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.status === "Vencida" || frm.doc.resultado === "Vencida") {
			frm.add_custom_button(__("Criar Formalização Contratual"), () => {
				frappe.call({
					method: "coaph_contract_ops.coaph_contract_ops.automation.actions.criar_formalizacao",
					args: { disputa: frm.doc.name },
					freeze: true,
					callback: (r) => r.message && frappe.set_route("Form", "Formalizacao Contratual", r.message),
				});
			}, __("Avançar"));
		}
	},
});
