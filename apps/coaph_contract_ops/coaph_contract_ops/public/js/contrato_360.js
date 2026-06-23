frappe.ui.form.on("Contrato 360", {
	refresh(frm) {
		if (frm.is_new()) return;
		const M = "coaph_contract_ops.coaph_contract_ops.automation.actions.";

		const acao = (label, metodo, dest) =>
			frm.add_custom_button(__(label), () => {
				frappe.call({
					method: M + metodo,
					args: { contrato: frm.doc.name },
					freeze: true,
					callback: (r) => r.message && frappe.set_route("Form", dest, r.message),
				});
			}, __("Criar"));

		acao("Plano de Mobilização", "criar_plano_mobilizacao", "Plano Mobilizacao");
		acao("Ciclo Mensal", "criar_ciclo", "Ciclo Mensal Medicao");
		acao("Renovação", "criar_renovacao", "Renovacao Contratual");

		const registrar = (label, dt) =>
			frm.add_custom_button(__(label), () => {
				frappe.new_doc(dt, { contrato: frm.doc.name });
			}, __("Registrar"));

		registrar("Pendência", "Pendencia Contratual");
		registrar("Risco", "Risco Contratual");
		registrar("Ocorrência", "Ocorrencia Contratual");
	},
});
