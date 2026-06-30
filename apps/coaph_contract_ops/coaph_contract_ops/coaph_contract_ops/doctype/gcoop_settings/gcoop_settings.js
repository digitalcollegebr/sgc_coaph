frappe.ui.form.on("GCOOP Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Sincronizar agora"), () => {
			frappe.dom.freeze(__("Sincronizando com o GCOOP..."));
			frappe.call({
				method: "coaph_contract_ops.coaph_contract_ops.doctype.gcoop_settings.gcoop_settings.sincronizar_agora",
			}).then((r) => {
				frappe.dom.unfreeze();
				const d = r.message || {};
				frappe.msgprint({
					title: __("Sincronização GCOOP"),
					indicator: (d.erros && d.erros.length) ? "orange" : "green",
					message: __("Criados: {0} · Atualizados: {1} · Oportunidades: {2} · Erros: {3}",
						[d.criados || 0, d.atualizados || 0, d.oportunidades || 0, (d.erros || []).length]),
				});
				frm.reload_doc();
			}).catch(() => frappe.dom.unfreeze());
		}).addClass("btn-primary");
	},
});
