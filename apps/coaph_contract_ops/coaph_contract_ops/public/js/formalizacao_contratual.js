frappe.ui.form.on("Formalizacao Contratual", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.status === "Contrato assinado") {
			frm.add_custom_button(__("Criar Contrato 360"), () => {
				frappe.call({
					method: "coaph_contract_ops.coaph_contract_ops.automation.actions.criar_contrato",
					args: { formalizacao: frm.doc.name },
					freeze: true,
					callback: (r) => r.message && frappe.set_route("Form", "Contrato 360", r.message),
				});
			}, __("Avançar"));
		}
	},
});
