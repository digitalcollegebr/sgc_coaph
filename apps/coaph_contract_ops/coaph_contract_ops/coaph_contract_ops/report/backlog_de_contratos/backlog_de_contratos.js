// Filtros do relatório "Backlog de Contratos".
frappe.query_reports["Backlog de Contratos"] = {
	filters: [
		{
			fieldname: "status_contrato",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Em formalização", "Em mobilização", "Operação assistida",
				"Ativo", "Ativo com atenção", "Crítico", "Vencido", "Em renovação",
				"Suspenso", "Em encerramento", "Encerrado"].join("\n"),
		},
		{
			fieldname: "contratante",
			label: __("Contratante"),
			fieldtype: "Link",
			options: "Contratante COAPH",
		},
		{
			fieldname: "modalidade_contratacao",
			label: __("Modalidade"),
			fieldtype: "Select",
			options: ["", "Venda Direta", "Licitação", "Adesão", "Dispensa",
				"Credenciamento", "Outro"].join("\n"),
		},
		{
			fieldname: "uf",
			label: __("UF"),
			fieldtype: "Data",
		},
	],
};
