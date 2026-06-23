frappe.pages["painel-executivo-contratos"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Painel Executivo de Contratos"),
		single_column: true,
	});

	const $body = $(wrapper).find(".layout-main-section");
	$body.html('<div class="sgc-painel"><div class="text-muted">' + __("Carregando…") + "</div></div>");
	const $root = $body.find(".sgc-painel");

	page.set_primary_action(__("Atualizar"), () => carregar(), "refresh");

	const CORES = {
		verde: "#2ea043", amarelo: "#d29922", vermelho: "#cf222e",
		azul: "#1f6feb", cinza: "#8c959f",
	};
	const LABEL_SEMAFORO = {
		verde: "Saudável", amarelo: "Atenção", vermelho: "Crítico", cinza: "Não iniciado", azul: "Em andamento",
	};

	const fmtBRL = (v) =>
		(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
	const esc = frappe.utils.escape_html;

	function kpiCard(label, valor, cor, sub) {
		return `<div class="sgc-kpi" style="border-top:3px solid ${cor}">
			<div class="sgc-kpi-num" style="color:${cor}">${valor}</div>
			<div class="sgc-kpi-lbl">${esc(label)}</div>
			${sub ? `<div class="sgc-kpi-sub">${esc(sub)}</div>` : ""}
		</div>`;
	}

	function barraEtapas(etapas) {
		return (
			'<div class="sgc-ciclo">' +
			etapas
				.map((e) => {
					const cor = CORES[e.cor] || CORES.cinza;
					const atual = e.atual ? "sgc-etapa-atual" : "";
					return `<div class="sgc-etapa ${atual}" title="${esc(e.label)}">
						<span class="sgc-dot" style="background:${cor}"></span>
						<span class="sgc-etapa-lbl">${esc(e.label)}</span>
					</div>`;
				})
				.join('<span class="sgc-seta">›</span>') +
			"</div>"
		);
	}

	function cardContrato(c) {
		const cor = CORES[c.semaforo] || CORES.cinza;
		const dias = c.dias_para_vencer;
		let venc = "—";
		if (c.vigencia_fim) {
			const d = frappe.datetime.str_to_user(c.vigencia_fim);
			const tag =
				dias == null ? "" :
				dias < 0 ? ` <b style="color:${CORES.vermelho}">(${Math.abs(dias)}d vencido)</b>` :
				dias <= 90 ? ` <b style="color:${CORES.amarelo}">(${dias}d)</b>` :
				` <span class="text-muted">(${dias}d)</span>`;
			venc = d + tag;
		}
		const badges =
			(c.depende_presidencia
				? `<span class="sgc-badge" style="background:${CORES.vermelho}">Depende da Presidência</span>` : "") +
			(c.atrasado ? `<span class="sgc-badge" style="background:${CORES.amarelo}">Atrasado</span>` : "") +
			(c.riscos_criticos ? `<span class="sgc-badge" style="background:#6e7781">${c.riscos_criticos} risco(s) crítico(s)</span>` : "");

		return `<div class="sgc-card" style="border-left:5px solid ${cor}">
			<div class="sgc-card-top">
				<div>
					<a class="sgc-num" href="/app/contrato-360/${encodeURIComponent(c.name)}">${esc(c.numero_contrato)}</a>
					<span class="sgc-titulo">${esc(c.titulo || "")}</span>
				</div>
				<div class="sgc-status">
					<span class="sgc-dot" style="background:${cor}"></span>
					${esc(LABEL_SEMAFORO[c.semaforo] || c.saude || "")}
				</div>
			</div>
			<div class="sgc-meta">
				<span><b>Contratante:</b> ${esc(c.contratante || "—")}</span>
				<span><b>Área/Unidade:</b> ${esc(c.unidade || "—")}</span>
				<span><b>Responsável:</b> ${esc(c.responsavel || "—")}</span>
				<span><b>Etapa:</b> ${esc(c.etapa_atual || "—")}</span>
				<span><b>Vencimento:</b> ${venc}</span>
				<span><b>Valor mensal:</b> ${fmtBRL(c.valor_mensal)}</span>
			</div>
			${barraEtapas(c.etapas)}
			<div class="sgc-acao"><b>Próxima ação:</b> ${esc(c.proxima_acao)} ${badges}</div>
		</div>`;
	}

	function gargalosHtml(gargalos) {
		if (!gargalos.length) return "";
		const max = Math.max(...gargalos.map((g) => g.qtd));
		const linhas = gargalos
			.map((g) => `<div class="sgc-garg-row">
				<span class="sgc-garg-lbl">${esc(g.etapa)}</span>
				<span class="sgc-garg-bar" style="width:${Math.round((g.qtd / max) * 100)}%"></span>
				<span class="sgc-garg-val">${g.qtd}</span>
			</div>`).join("");
		return `<div class="sgc-bloco"><h5>Gargalos por etapa</h5>${linhas}</div>`;
	}

	function render(d) {
		const k = d.kpis;
		const kpis =
			kpiCard("Contratos ativos", k.ativos, CORES.verde) +
			kpiCard("Em andamento", k.em_andamento, CORES.azul) +
			kpiCard("Aguardando aprovação", k.aguardando_aprovacao, CORES.cinza) +
			kpiCard("Vencendo ≤30 dias", k.vencendo_30, CORES.amarelo) +
			kpiCard("Vencendo 31–60", k.vencendo_60, CORES.amarelo) +
			kpiCard("Vencendo 61–90", k.vencendo_90, CORES.amarelo) +
			kpiCard("Vencidos", k.vencidos, CORES.vermelho) +
			kpiCard("Atrasados", k.atrasados, CORES.vermelho) +
			kpiCard("Bloqueados / críticos", k.bloqueados_criticos, CORES.vermelho) +
			kpiCard("Valor total ativos", fmtBRL(k.valor_total_ativos), CORES.verde, "soma mensal") +
			kpiCard("Valor total críticos", fmtBRL(k.valor_total_criticos), CORES.vermelho, "soma mensal");

		const legenda =
			'<div class="sgc-legenda">' +
			Object.keys(LABEL_SEMAFORO)
				.map((c) => `<span><span class="sgc-dot" style="background:${CORES[c]}"></span>${LABEL_SEMAFORO[c]}</span>`)
				.join("") +
			`<span class="text-muted">Posição em ${frappe.datetime.str_to_user(d.as_of)}</span></div>`;

		const cards = d.contratos.length
			? d.contratos.map(cardContrato).join("")
			: '<div class="text-muted">Nenhum contrato visível para o seu perfil.</div>';

		$root.html(
			`<div class="sgc-kpis">${kpis}</div>` +
			gargalosHtml(d.gargalos) +
			`<div class="sgc-bloco"><h5>Contratos — visão contrato a contrato</h5>${legenda}${cards}</div>`
		);
	}

	function carregar() {
		$root.html('<div class="text-muted">' + __("Carregando…") + "</div>");
		frappe.call({
			method: "coaph_contract_ops.coaph_contract_ops.automation.dashboard.get_painel_executivo",
			callback: (r) => r.message && render(r.message),
		});
	}

	carregar();
};
