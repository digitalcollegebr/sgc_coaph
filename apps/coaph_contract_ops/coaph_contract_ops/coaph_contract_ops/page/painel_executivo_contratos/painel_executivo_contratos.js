frappe.pages["painel-executivo-contratos"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Painel Executivo de Contratos"),
		single_column: true,
	});

	const CORES = {
		verde: "#2ea043", amarelo: "#d29922", vermelho: "#cf222e",
		azul: "#1f6feb", cinza: "#8c959f",
	};
	const LABEL = { verde: "Saudável", amarelo: "Atenção", vermelho: "Crítico", cinza: "Não iniciado", azul: "Em andamento" };
	const fmtBRL = (v) => (v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
	const fmtBRLk = (v) => (Math.abs(v) >= 1000 ? "R$ " + (v / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 0 }) + " mil" : fmtBRL(v));
	const esc = frappe.utils.escape_html;

	let DATA = null;
	const state = { q: "", etapa: "", semaforo: "", soPres: false, quick: "", sort: "sev" };

	const $body = $(wrapper).find(".layout-main-section");
	$body.html('<div class="sgc-painel"></div>');
	const $root = $body.find(".sgc-painel");

	page.set_primary_action(__("Atualizar"), () => carregar(), "refresh");
	page.add_inner_button(__("Exportar CSV"), () => exportarCSV());

	// ----------------------------------------------------------------- quick filters
	const QUICK = {
		ativos: (c) => !["Encerrado", "Suspenso", "Em formalização"].includes(c.etapa_atual),
		andamento: (c) => ["Em mobilização", "Operação assistida"].includes(c.etapa_atual),
		aprovacao: (c) => c.etapa_atual === "Em formalização",
		venc30: (c) => c.dias_para_vencer != null && c.dias_para_vencer >= 0 && c.dias_para_vencer <= 30,
		venc60: (c) => c.dias_para_vencer != null && c.dias_para_vencer > 30 && c.dias_para_vencer <= 60,
		venc90: (c) => c.dias_para_vencer != null && c.dias_para_vencer > 60 && c.dias_para_vencer <= 90,
		vencidos: (c) => c.dias_para_vencer != null && c.dias_para_vencer < 0 && c.etapa_atual !== "Encerrado",
		atrasados: (c) => c.atrasado,
		criticos: (c) => c.semaforo === "vermelho" || c.riscos_criticos > 0,
		presidencia: (c) => c.depende_presidencia,
	};

	function aplicarFiltros() {
		let arr = DATA.contratos.slice();
		const q = state.q.trim().toLowerCase();
		if (q) arr = arr.filter((c) =>
			(c.numero_contrato || "").toLowerCase().includes(q) ||
			(c.titulo || "").toLowerCase().includes(q) ||
			(c.contratante || "").toLowerCase().includes(q) ||
			(c.responsavel || "").toLowerCase().includes(q));
		if (state.etapa) arr = arr.filter((c) => c.etapa_atual === state.etapa);
		if (state.semaforo) arr = arr.filter((c) => c.semaforo === state.semaforo);
		if (state.soPres) arr = arr.filter((c) => c.depende_presidencia);
		if (state.quick && QUICK[state.quick]) arr = arr.filter(QUICK[state.quick]);

		const cmp = {
			sev: (a, b) => a.severidade - b.severidade || ((a.dias_para_vencer ?? 1e9) - (b.dias_para_vencer ?? 1e9)),
			venc: (a, b) => (a.dias_para_vencer ?? 1e9) - (b.dias_para_vencer ?? 1e9),
			valor: (a, b) => b.valor_mensal - a.valor_mensal,
			nome: (a, b) => (a.contratante || "").localeCompare(b.contratante || ""),
		}[state.sort];
		arr.sort(cmp);
		return arr;
	}

	// ----------------------------------------------------------------- render: KPIs
	function kpi(label, valor, cor, quick, sub) {
		const active = quick && state.quick === quick ? "sgc-kpi-active" : "";
		const clickable = quick ? `role="button" tabindex="0" data-quick="${quick}"` : "";
		return `<div class="sgc-kpi ${active}" style="border-top:3px solid ${cor}" ${clickable}
				aria-label="${esc(label)}: ${valor}">
			<div class="sgc-kpi-num" style="color:${cor}">${valor}</div>
			<div class="sgc-kpi-lbl">${esc(label)}</div>
			${sub ? `<div class="sgc-kpi-sub">${esc(sub)}</div>` : ""}
		</div>`;
	}

	function grupoKpis(titulo, cards) {
		return `<div class="sgc-kpi-grupo"><div class="sgc-grupo-h">${esc(titulo)}</div>
			<div class="sgc-kpis">${cards}</div></div>`;
	}

	function renderTopo() {
		const k = DATA.kpis, r = DATA.resumo;
		const resumo = `<div class="sgc-resumo">
			<div><span class="sgc-rnum">${r.total}</span><span>contratos na carteira</span></div>
			<div><span class="sgc-rnum">${fmtBRL(r.valor_sob_gestao)}</span><span>valor mensal sob gestão</span></div>
			<div><span class="sgc-rnum" style="color:${r.pct_saudavel >= 70 ? CORES.verde : r.pct_saudavel >= 40 ? CORES.amarelo : CORES.vermelho}">${r.pct_saudavel}%</span><span>saudáveis</span></div>
			<div><span class="sgc-rnum" style="color:${r.criticos ? CORES.vermelho : CORES.verde}">${r.criticos}</span><span>críticos/bloqueados</span></div>
			<div><span class="sgc-rnum" style="color:${r.requer_presidencia ? CORES.vermelho : CORES.cinza}">${r.requer_presidencia}</span><span>requerem presidência</span></div>
			<div class="sgc-asof text-muted">Posição em ${frappe.datetime.str_to_user(DATA.as_of)}</div>
		</div>`;

		const volume = grupoKpis("Volume", [
			kpi("Ativos", k.ativos, CORES.verde, "ativos"),
			kpi("Em andamento", k.em_andamento, CORES.azul, "andamento"),
			kpi("Aguardando aprovação", k.aguardando_aprovacao, CORES.cinza, "aprovacao"),
		].join(""));
		const prazos = grupoKpis("Prazos", [
			kpi("Vence ≤30d", k.vencendo_30, CORES.amarelo, "venc30"),
			kpi("Vence 31–60d", k.vencendo_60, CORES.amarelo, "venc60"),
			kpi("Vence 61–90d", k.vencendo_90, CORES.amarelo, "venc90"),
			kpi("Vencidos", k.vencidos, CORES.vermelho, "vencidos"),
		].join(""));
		const risco = grupoKpis("Risco & Bloqueios", [
			kpi("Atrasados", k.atrasados, CORES.vermelho, "atrasados"),
			kpi("Bloqueados/críticos", k.bloqueados_criticos, CORES.vermelho, "criticos"),
			kpi("Dependem da presidência", DATA.resumo.requer_presidencia, CORES.vermelho, "presidencia"),
		].join(""));
		const fin = grupoKpis("Financeiro (mensal)", [
			kpi("Valor ativos", fmtBRLk(k.valor_total_ativos), CORES.verde, "", "soma mensal"),
			kpi("Valor críticos", fmtBRLk(k.valor_total_criticos), CORES.vermelho, "criticos", "clique p/ filtrar"),
		].join(""));

		return resumo + `<div class="sgc-kpi-cols">${volume}${prazos}${risco}${fin}</div>` + renderGargalos();
	}

	function renderGargalos() {
		const g = DATA.gargalos;
		if (!g.length) return "";
		const max = Math.max(...g.map((x) => x.qtd));
		const linhas = g.map((x) => {
			const ativo = state.etapa === x.etapa ? "sgc-garg-active" : "";
			return `<div class="sgc-garg-row ${ativo}" role="button" tabindex="0" data-etapa="${esc(x.etapa)}">
				<span class="sgc-garg-lbl">${esc(x.etapa)}</span>
				<span class="sgc-garg-bar" style="width:${Math.round((x.qtd / max) * 100)}%"></span>
				<span class="sgc-garg-val">${x.qtd}</span></div>`;
		}).join("");
		return `<div class="sgc-bloco"><h5>Gargalos por etapa <small class="text-muted">(clique para filtrar)</small></h5>${linhas}</div>`;
	}

	// ----------------------------------------------------------------- render: toolbar
	function renderToolbar() {
		const etapas = [...new Set(DATA.contratos.map((c) => c.etapa_atual))].sort();
		const opt = (v, l, sel) => `<option value="${esc(v)}" ${sel ? "selected" : ""}>${esc(l)}</option>`;
		return `<div class="sgc-toolbar">
			<input type="search" class="form-control input-sm sgc-busca" placeholder="🔎 Buscar nº, título, contratante, responsável…" value="${esc(state.q)}">
			<select class="form-control input-sm sgc-fetapa">${opt("", "Todas as etapas")}${etapas.map((e) => opt(e, e, state.etapa === e)).join("")}</select>
			<select class="form-control input-sm sgc-fsem">${opt("", "Todos os semáforos")}${Object.keys(LABEL).map((s) => opt(s, LABEL[s], state.semaforo === s)).join("")}</select>
			<select class="form-control input-sm sgc-sort">
				${opt("sev", "Ordenar: Severidade", state.sort === "sev")}
				${opt("venc", "Ordenar: Vencimento", state.sort === "venc")}
				${opt("valor", "Ordenar: Valor", state.sort === "valor")}
				${opt("nome", "Ordenar: Contratante", state.sort === "nome")}
			</select>
			<label class="sgc-chk"><input type="checkbox" class="sgc-pres" ${state.soPres ? "checked" : ""}> Só presidência</label>
			<button class="btn btn-xs btn-default sgc-limpar">Limpar filtros</button>
			<span class="sgc-count text-muted"></span>
		</div>`;
	}

	// ----------------------------------------------------------------- render: cards
	function barraEtapas(etapas) {
		return '<div class="sgc-ciclo" role="list">' + etapas.map((e) => {
			const cor = CORES[e.cor] || CORES.cinza;
			return `<div class="sgc-etapa ${e.atual ? "sgc-etapa-atual" : ""}" role="listitem" title="${esc(e.label)}: ${LABEL[e.cor] || ""}">
				<span class="sgc-dot" style="background:${cor}" aria-hidden="true"></span>
				<span class="sgc-etapa-lbl">${esc(e.label)}</span></div>`;
		}).join('<span class="sgc-seta" aria-hidden="true">›</span>') + "</div>";
	}

	function cardContrato(c) {
		const cor = CORES[c.semaforo] || CORES.cinza;
		const dias = c.dias_para_vencer;
		let venc = "—";
		if (c.vigencia_fim) {
			const d = frappe.datetime.str_to_user(c.vigencia_fim);
			const tag = dias == null ? "" :
				dias < 0 ? ` <b style="color:${CORES.vermelho}">${Math.abs(dias)}d vencido</b>` :
				dias <= 90 ? ` <b style="color:${CORES.amarelo}">${dias}d</b>` :
				` <span class="text-muted">${dias}d</span>`;
			venc = d + tag;
		}
		const badges =
			(c.depende_presidencia ? `<span class="sgc-badge" style="background:${CORES.vermelho}">Presidência</span>` : "") +
			(c.atrasado ? `<span class="sgc-badge" style="background:${CORES.amarelo}">Atrasado</span>` : "") +
			(c.riscos_criticos ? `<span class="sgc-badge" style="background:#6e7781">${c.riscos_criticos} risco(s)</span>` : "");
		return `<div class="sgc-card" style="border-left:5px solid ${cor}">
			<div class="sgc-card-top">
				<div class="sgc-card-id">
					<span class="sgc-dot" style="background:${cor}" title="${LABEL[c.semaforo]}"></span>
					<a class="sgc-num" href="/app/contrato-360/${encodeURIComponent(c.name)}">${esc(c.numero_contrato)}</a>
					<span class="sgc-titulo">${esc(c.titulo || "")}</span>
				</div>
				<div class="sgc-card-val">${fmtBRL(c.valor_mensal)}<small>/mês</small></div>
			</div>
			<div class="sgc-meta">
				<span><b>Contratante:</b> ${esc(c.contratante || "—")}</span>
				<span><b>Unidade:</b> ${esc(c.unidade || "—")}</span>
				<span><b>Responsável:</b> ${esc(c.responsavel || "—")}</span>
				<span><b>Etapa:</b> ${esc(c.etapa_atual || "—")}</span>
				<span><b>Vencimento:</b> ${venc}</span>
			</div>
			${barraEtapas(c.etapas)}
			<div class="sgc-acao"><b>Próxima ação:</b> ${esc(c.proxima_acao)} ${badges}</div>
		</div>`;
	}

	function renderLista() {
		const arr = aplicarFiltros();
		$root.find(".sgc-count").text(`${arr.length} de ${DATA.contratos.length} contratos`);
		const html = arr.length
			? arr.map(cardContrato).join("")
			: `<div class="sgc-vazio">Nenhum contrato corresponde aos filtros. <a href="#" class="sgc-limpar">Limpar filtros</a></div>`;
		$root.find(".sgc-lista").html(html);
	}

	// ----------------------------------------------------------------- render full
	function render() {
		$root.html(
			renderTopo() +
			`<div class="sgc-bloco">
				<h5>Contratos — visão contrato a contrato</h5>
				${renderToolbar()}
				<div class="sgc-legenda">` +
				Object.keys(LABEL).map((c) => `<span><span class="sgc-dot" style="background:${CORES[c]}"></span>${LABEL[c]}</span>`).join("") +
			`</div><div class="sgc-lista"></div></div>`
		);
		renderLista();
		bind();
	}

	function bind() {
		$root.off(".sgc");
		$root.on("input.sgc", ".sgc-busca", frappe.utils.debounce((e) => { state.q = e.target.value; renderLista(); }, 200));
		$root.on("change.sgc", ".sgc-fetapa", (e) => { state.etapa = e.target.value; renderTopo_refresh(); });
		$root.on("change.sgc", ".sgc-fsem", (e) => { state.semaforo = e.target.value; renderLista(); });
		$root.on("change.sgc", ".sgc-sort", (e) => { state.sort = e.target.value; renderLista(); });
		$root.on("change.sgc", ".sgc-pres", (e) => { state.soPres = e.target.checked; renderLista(); });
		$root.on("click.sgc", ".sgc-limpar", (e) => { e.preventDefault(); Object.assign(state, { q: "", etapa: "", semaforo: "", soPres: false, quick: "" }); render(); });
		$root.on("click.sgc keypress.sgc", "[data-quick]", (e) => {
			if (e.type === "keypress" && e.which !== 13 && e.which !== 32) return;
			const q = e.currentTarget.getAttribute("data-quick");
			state.quick = state.quick === q ? "" : q; render();
		});
		$root.on("click.sgc keypress.sgc", "[data-etapa]", (e) => {
			if (e.type === "keypress" && e.which !== 13 && e.which !== 32) return;
			const et = e.currentTarget.getAttribute("data-etapa");
			state.etapa = state.etapa === et ? "" : et; render();
		});
	}
	// re-render topo (para refletir estado ativo de filtros) + lista
	function renderTopo_refresh() { render(); }

	// ----------------------------------------------------------------- CSV
	function exportarCSV() {
		if (!DATA) return;
		const arr = aplicarFiltros();
		const cols = ["numero_contrato", "titulo", "contratante", "unidade", "responsavel", "etapa_atual", "semaforo", "vigencia_fim", "dias_para_vencer", "valor_mensal", "proxima_acao", "depende_presidencia", "atrasado", "riscos_criticos"];
		const head = ["Numero", "Titulo", "Contratante", "Unidade", "Responsavel", "Etapa", "Semaforo", "Vencimento", "Dias", "Valor Mensal", "Proxima Acao", "Depende Presidencia", "Atrasado", "Riscos Criticos"];
		const linhas = arr.map((c) => cols.map((k) => `"${String(c[k] ?? "").replace(/"/g, '""')}"`).join(","));
		const csv = "﻿" + [head.join(","), ...linhas].join("\n");
		const a = document.createElement("a");
		a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
		a.download = `painel_contratos_${DATA.as_of}.csv`;
		a.click();
	}

	// ----------------------------------------------------------------- load
	function skeleton() {
		$root.html('<div class="sgc-skel"></div>'.repeat(1) +
			'<div class="sgc-kpis">' + '<div class="sgc-kpi sgc-loading"></div>'.repeat(8) + "</div>" +
			'<div class="sgc-card sgc-loading" style="height:120px"></div>'.repeat(3));
	}

	function carregar() {
		skeleton();
		frappe.call({
			method: "coaph_contract_ops.coaph_contract_ops.automation.dashboard.get_painel_executivo",
			callback: (r) => { if (r.message) { DATA = r.message; render(); } },
			error: () => $root.html('<div class="sgc-vazio text-danger">Não foi possível carregar o painel. Tente Atualizar.</div>'),
		});
	}

	carregar();
};
