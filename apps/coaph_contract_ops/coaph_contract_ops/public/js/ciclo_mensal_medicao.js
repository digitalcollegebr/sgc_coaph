frappe.ui.form.on("Ciclo Mensal Medicao", {
	refresh(frm) {
		if (frm.is_new()) return;
		const M = "coaph_contract_ops.coaph_contract_ops.automation.actions.";

		const acao = (label, metodo, dest) =>
			frm.add_custom_button(__(label), () => {
				frappe.call({
					method: M + metodo,
					args: { ciclo: frm.doc.name },
					freeze: true,
					callback: (r) => r.message && frappe.set_route("Form", dest, r.message),
				});
			}, __("Criar"));

		acao("Faturamento", "criar_faturamento", "Faturamento COAPH");
		acao("Recebimento", "criar_recebimento", "Recebimento COAPH");
		acao("Repasse", "criar_repasse", "Repasse Cooperados");
	},
});
