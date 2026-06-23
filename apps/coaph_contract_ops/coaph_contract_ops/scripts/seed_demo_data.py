"""Dados fictícios de demonstração do SGC COAPH — Gestão 360 de Contratos.

Uso:
    bench --site SEU_SITE execute coaph_contract_ops.scripts.seed_demo_data.execute

Características:
- IDEMPOTENTE: verifica existência por chave natural antes de criar; reexecutar
  não duplica registros.
- NÃO usa dados reais da COAPH (todos os nomes/CNPJs/CPFs são fictícios).
- Cria os 7 cenários obrigatórios da especificação.

Para remover os dados de demonstração, use:
    bench --site SEU_SITE execute coaph_contract_ops.scripts.seed_demo_data.limpar
"""

import frappe
from frappe.utils import add_days, add_months, flt, nowdate

PREFIXO = "DEMO"


# ---------------------------------------------------------------- helpers
# Campos usados como estado de workflow — não podem ser definidos direto no
# insert (o Frappe valida a transição). Inserimos no estado inicial e depois
# gravamos o estado desejado via db.set_value (apenas para dados de demo).
WF_STATE_FIELDS = ("status", "status_contrato")


def goc(doctype, chave, valores=None):
    """get-or-create por chave natural. Retorna o name."""
    nome = frappe.db.exists(doctype, chave)
    if nome:
        return nome
    valores = dict(valores or {})
    estados = {k: valores.pop(k) for k in WF_STATE_FIELDS if k in valores}
    doc = frappe.get_doc({"doctype": doctype, **chave, **valores})
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    for campo, valor in estados.items():
        if valor:
            frappe.db.set_value(doctype, doc.name, campo, valor, update_modified=False)
    return doc.name


def _log(msg):
    print(f"  [seed] {msg}")


# ---------------------------------------------------------------- dados base
CONTRATANTES = [
    ("Hospital São Lucas", "Privado", "12.345.678/0001-90", "Fortaleza", "CE"),
    ("UPA Norte Municipal", "Público", "23.456.789/0001-01", "Fortaleza", "CE"),
    ("Clínica Vida Plena", "Privado", "34.567.890/0001-12", "Sobral", "CE"),
    ("Hospital Regional do Sertão", "Público", "45.678.901/0001-23", "Quixadá", "CE"),
    ("Instituto Materno Infantil Esperança", "Filantrópico", "56.789.012/0001-34", "Juazeiro do Norte", "CE"),
    ("Prefeitura Municipal de Boa Vista do Norte", "Público", "67.890.123/0001-45", "Boa Vista do Norte", "CE"),
    ("Hospital Santa Helena", "Privado", "78.901.234/0001-56", "Maracanaú", "CE"),
    ("Fundação Saúde Integrada", "Filantrópico", "89.012.345/0001-67", "Caucaia", "CE"),
]

UNIDADES = [
    ("UPA Norte — Emergência 24h", "UPA Norte Municipal", "UPA"),
    ("Hospital São Lucas — Pronto Atendimento", "Hospital São Lucas", "Hospital"),
    ("Clínica Vida Plena — Ambulatório", "Clínica Vida Plena", "Ambulatório"),
    ("Hospital Regional do Sertão — Urgência e Emergência", "Hospital Regional do Sertão", "Hospital"),
    ("Instituto Materno Infantil Esperança — Pediatria", "Instituto Materno Infantil Esperança", "Hospital"),
    ("Hospital Santa Helena — Clínica Médica", "Hospital Santa Helena", "Hospital"),
    ("Fundação Saúde Integrada — Teleassistência", "Fundação Saúde Integrada", "Teleassistência"),
]

ESPECIALIDADES = ["Clínica Médica", "Pediatria", "Ortopedia", "Cardiologia", "Anestesiologia"]


def seed_contratantes():
    """Retorna mapa nome_contratante -> name (id por série)."""
    cmap = {}
    for nome, tipo, cnpj, cidade, uf in CONTRATANTES:
        cmap[nome] = goc("Contratante COAPH", {"nome_contratante": nome}, {
            "tipo_contratante": tipo, "cnpj": cnpj, "razao_social": nome,
            "cidade": cidade, "estado": uf, "status": "Ativo",
            "email_contato": "contato@exemplo.org", "telefone_contato": "(85) 4000-0000",
        })
    _log(f"{len(CONTRATANTES)} contratantes")
    return cmap


def seed_unidades(cmap):
    """Retorna mapa nome_unidade -> name (id por série)."""
    umap = {}
    for nome, contratante, tipo in UNIDADES:
        umap[nome] = goc("Unidade Atendimento", {"nome_unidade": nome}, {
            "contratante": cmap[contratante], "tipo_unidade": tipo,
            "cidade": "Fortaleza", "estado": "CE", "status": "Ativa",
        })
    _log(f"{len(UNIDADES)} unidades de atendimento")
    return umap


# ---------------------------------------------------------------- pipeline comercial
def seed_pipeline(cmap):
    contratantes = [c[0] for c in CONTRATANTES]
    statuses_op = [
        "Demanda identificada", "Oportunidade registrada", "Oportunidade qualificada",
        "Em análise de viabilidade", "Aprovada para avanço", "Convertida em disputa/proposta",
        "Aprovada para avanço", "Oportunidade qualificada", "Descartada", "Oportunidade registrada",
    ]
    prioridades = ["Alta", "Média", "Crítica", "Baixa"]
    oportunidades = []
    for i in range(10):
        titulo = f"{PREFIXO} Oportunidade {i + 1:02d} — {contratantes[i % len(contratantes)]}"
        nome = goc("Oportunidade COAPH", {"titulo": titulo}, {
            "contratante": cmap[contratantes[i % len(contratantes)]],
            "origem": "Edital" if i % 2 == 0 else "Prospecção",
            "tipo_cliente": "Público" if i % 2 == 0 else "Privado",
            "tipo_servico": "Gestão de plantões médicos",
            "valor_estimado_mensal": 80000 + i * 15000,
            "valor_estimado_anual": (80000 + i * 15000) * 12,
            "data_identificacao": add_days(nowdate(), -120 + i * 5),
            "prioridade": prioridades[i % len(prioridades)],
            "status": statuses_op[i],
        })
        oportunidades.append(nome)
    _log(f"{len(oportunidades)} oportunidades")

    # 6 viabilidades para as 6 primeiras oportunidades
    viab_status = ["Aprovada", "Aprovada", "Aprovada", "Aprovada", "Aprovada", "Reprovada"]
    for i in range(6):
        contratante = frappe.db.get_value("Oportunidade COAPH", oportunidades[i], "contratante")
        goc("Analise Viabilidade", {"oportunidade": oportunidades[i]}, {
            "contratante": contratante,
            "decisao": "Go" if viab_status[i] == "Aprovada" else "No-Go",
            "risco_operacional": "Médio", "risco_juridico": "Baixo", "risco_financeiro": "Médio",
            "margem_estimativa": 18, "status": viab_status[i],
            "data_decisao": add_days(nowdate(), -90 + i * 5),
        })
    _log("6 análises de viabilidade")

    # 6 disputas; as 5 primeiras Vencidas
    disputas = []
    for i in range(6):
        contratante = frappe.db.get_value("Oportunidade COAPH", oportunidades[i], "contratante")
        resultado = "Vencida" if i < 5 else "Perdida"
        titulo = f"{PREFIXO} Disputa {i + 1:02d} — {contratante}"
        nome = goc("Disputa Proposta COAPH", {"titulo": titulo}, {
            "oportunidade": oportunidades[i], "contratante": contratante,
            "tipo_disputa": "Licitação pública" if i % 2 == 0 else "BID privado",
            "valor_estimado": 90000 + i * 10000, "valor_proposto": 88000 + i * 10000,
            "status": resultado, "resultado": resultado,
            "motivo_perda": "Preço do concorrente menor" if resultado == "Perdida" else None,
            "data_resultado": add_days(nowdate(), -75 + i * 5),
        })
        disputas.append(nome)
    _log("6 disputas/propostas")

    # 5 formalizacoes; todas "Contrato assinado"
    formalizacoes = []
    for i in range(5):
        d = frappe.get_doc("Disputa Proposta COAPH", disputas[i])
        nome = goc("Formalizacao Contratual", {"disputa_proposta": disputas[i]}, {
            "contratante": d.contratante,
            "numero_minuta": f"MIN-{i + 1:03d}", "versao_minuta": "v2",
            "status": "Contrato assinado",
            "data_assinatura": add_days(nowdate(), -60 + i * 5),
        })
        formalizacoes.append(nome)
    _log("5 formalizações contratuais")
    return formalizacoes


# ---------------------------------------------------------------- contratos (7 cenários)
def seed_contratos(cmap, umap, formalizacoes):
    hoje = nowdate()
    # (titulo, contratante, unidade, status, saude, vigencia_inicio, vigencia_fim, valor_mensal, tipo)
    cenarios = [
        # 1. Contrato público em mobilização
        ("Contrato Público em Mobilização — UPA Norte", "UPA Norte Municipal",
         "UPA Norte — Emergência 24h", "Em mobilização", "Saudável",
         add_days(hoje, -20), add_days(hoje, 700), 120000, "Público"),
        # 2. Contrato privado ativo saudável
        ("Contrato Privado Ativo — Hospital São Lucas", "Hospital São Lucas",
         "Hospital São Lucas — Pronto Atendimento", "Ativo", "Saudável",
         add_days(hoje, -300), add_days(hoje, 400), 180000, "Privado"),
        # 3. Ativo com atenção (recebimento atrasado)
        ("Contrato com Atenção — Clínica Vida Plena", "Clínica Vida Plena",
         "Clínica Vida Plena — Ambulatório", "Ativo com atenção", "Atenção",
         add_days(hoje, -250), add_days(hoje, 300), 95000, "Privado"),
        # 4. Crítico por pendências operacionais
        ("Contrato Crítico — Hospital Regional do Sertão", "Hospital Regional do Sertão",
         "Hospital Regional do Sertão — Urgência e Emergência", "Crítico", "Crítico",
         add_days(hoje, -400), add_days(hoje, 200), 210000, "Público"),
        # 5. Vencendo em 90 dias
        ("Contrato Vencendo 90 dias — Instituto Esperança", "Instituto Materno Infantil Esperança",
         "Instituto Materno Infantil Esperança — Pediatria", "Ativo", "Risco de perda",
         add_days(hoje, -640), add_days(hoje, 90), 140000, "Filantrópico" if False else "Privado"),
        # 6. Em renovação
        ("Contrato em Renovação — Hospital Santa Helena", "Hospital Santa Helena",
         "Hospital Santa Helena — Clínica Médica", "Em renovação", "Atenção",
         add_days(hoje, -700), add_days(hoje, 45), 160000, "Privado"),
        # 7. Recém-assinado em operação assistida
        ("Contrato Recém-assinado — Fundação Saúde Integrada", "Fundação Saúde Integrada",
         "Fundação Saúde Integrada — Teleassistência", "Operação assistida", "Saudável",
         add_days(hoje, -10), add_days(hoje, 720), 110000, "Privado"),
    ]
    contratos = []
    for i, (titulo, contratante, unidade, status, saude, vi, vf, vm, tipo) in enumerate(cenarios):
        valores = {
            "contratante": cmap[contratante], "unidade_atendimento": umap[unidade],
            "tipo_contrato": tipo, "numero_contrato": f"{PREFIXO}-C{i + 1:03d}",
            "vigencia_inicio": vi, "vigencia_fim": vf,
            "valor_mensal": vm, "valor_global": vm * 24,
            "indice_reajuste": "IPCA", "status_contrato": status, "saude_contrato": saude,
            "data_assinatura": vi,
            "servicos": [
                {"servico": "Plantão médico", "especialidade": ESPECIALIDADES[i % len(ESPECIALIDADES)],
                 "unidade_medida": "Plantão", "quantidade_prevista": 60,
                 "valor_unitario": 1500, "valor_mensal_previsto": 90000},
            ],
        }
        if i < len(formalizacoes):
            valores["formalizacao_contratual"] = formalizacoes[i]
        nome = goc("Contrato 360", {"titulo_contrato": titulo}, valores)
        contratos.append(nome)
    _log(f"{len(contratos)} contratos 360 (7 cenários obrigatórios)")
    return contratos


def seed_planos_e_cooperados(contratos):
    # 5 planos de mobilização (contratos 0..4)
    planos = []
    fases = [
        ("Kickoff interno do contrato", "Operação"),
        ("Cadastro e parametrização do contrato", "TI"),
        ("Dimensionamento da equipe", "RH"),
        ("Credenciamento dos cooperados", "RH"),
        ("Onboarding cooperativo", "RH"),
        ("Liberação para início da operação", "Operação"),
    ]
    plano_status = ["Cooperados em mobilização", "Operação liberada", "Equipe dimensionada",
                    "Contrato parametrizado", "Onboarding concluído"]
    for i in range(5):
        c = frappe.get_doc("Contrato 360", contratos[i])
        etapas = []
        for j, (etapa, area) in enumerate(fases):
            st = "Concluído" if j < 2 else ("Atrasado" if (i == 3 and j == 3) else "Em andamento")
            etapas.append({
                "etapa": etapa, "area_responsavel": area, "status": st, "sla_dias": 7,
                "data_inicio_prevista": add_days(nowdate(), -30 + j * 3),
                "data_fim_prevista": add_days(nowdate(), -23 + j * 3),
            })
        nome = goc("Plano Mobilizacao", {"contrato": contratos[i]}, {
            "contratante": c.contratante, "unidade_atendimento": c.unidade_atendimento,
            "status": plano_status[i], "progresso_percentual": 40 + i * 10,
            "etapas": etapas,
        })
        planos.append(nome)
    _log(f"{len(planos)} planos de mobilização")

    # 15 cooperados distribuídos nos 5 contratos (3 por contrato)
    n = 0
    cred_status = ["Apto", "Credenciado", "Em análise"]
    for i in range(5):
        for k in range(3):
            n += 1
            nome_coop = f"{PREFIXO} Cooperado {n:02d}"
            goc("Cooperado Mobilizado", {"nome_cooperado": nome_coop}, {
                "cpf": f"000.000.000-{n:02d}",
                "especialidade": ESPECIALIDADES[n % len(ESPECIALIDADES)],
                "registro_profissional": f"CRM-CE {10000 + n}",
                "contrato": contratos[i], "plano_mobilizacao": planos[i],
                "status_credenciamento": cred_status[k % len(cred_status)],
                "apto_para_operacao": 1 if cred_status[k % len(cred_status)] == "Apto" else 0,
                "treinamento_realizado": 1 if k == 0 else 0,
            })
    _log(f"{n} cooperados mobilizados")
    return planos


def seed_ciclos_financeiro(contratos):
    # 12 ciclos: distribui entre contratos ativos (1..6), competências recentes
    ciclos = []
    plano_ciclos = [
        (1, "04/2026", "Repasse executado", 165000),
        (1, "05/2026", "Demonstrativos publicados", 170000),
        (2, "04/2026", "Recebida", 92000),
        (2, "05/2026", "NF emitida", 95000),
        (3, "03/2026", "Aguardando recebimento", 205000),
        (3, "04/2026", "Produção validada", 208000),
        (4, "04/2026", "Repasse executado", 138000),
        (4, "05/2026", "Liberada para faturamento", 140000),
        (5, "05/2026", "Produção validada", 158000),
        (6, "05/2026", "Competência aberta", 110000),
        (3, "05/2026", "Produção em conferência", 207000),
        (1, "06/2026", "Competência aberta", 172000),
    ]
    for idx_contrato, comp, status, valor in plano_ciclos:
        c = frappe.get_doc("Contrato 360", contratos[idx_contrato])
        nome = goc("Ciclo Mensal Medicao",
                   {"contrato": contratos[idx_contrato], "competencia": comp}, {
                       "contratante": c.contratante, "unidade_atendimento": c.unidade_atendimento,
                       "status": status, "valor_producao": valor,
                       "data_abertura": add_days(nowdate(), -40),
                   })
        ciclos.append((nome, idx_contrato, comp, valor, status))
    _log(f"{len(ciclos)} ciclos mensais de medição")

    # 8 faturamentos (primeiros 8 ciclos com produção)
    faturamentos = []
    for nome, idx, comp, valor, status in ciclos[:8]:
        c = frappe.get_doc("Ciclo Mensal Medicao", nome)
        fat = goc("Faturamento COAPH", {"ciclo_mensal": nome}, {
            "contrato": c.contrato, "contratante": c.contratante, "competencia": comp,
            "numero_nf": f"{PREFIXO}-NF-{len(faturamentos) + 1:04d}",
            "valor_bruto": valor, "retencoes": flt(valor) * 0.05,
            "valor_liquido": flt(valor) * 0.95,
            "data_emissao": add_days(nowdate(), -25),
            "data_vencimento": add_days(nowdate(), 5),
            "status": "NF emitida",
        })
        faturamentos.append(fat)
    _log(f"{len(faturamentos)} faturamentos")

    # 6 recebimentos (primeiros 6 faturamentos)
    receb = 0
    for fat in faturamentos[:6]:
        f = frappe.get_doc("Faturamento COAPH", fat)
        atrasado = (receb == 2)  # cenário 3: recebimento atrasado
        goc("Recebimento COAPH", {"faturamento": fat}, {
            "contrato": f.contrato, "ciclo_mensal": f.ciclo_mensal,
            "valor_previsto": f.valor_liquido, "data_prevista": f.data_vencimento,
            "valor_recebido": 0 if atrasado else f.valor_liquido,
            "data_recebimento": None if atrasado else add_days(nowdate(), -2),
            "status": "Atrasado" if atrasado else "Recebido integral",
        })
        receb += 1
    _log(f"{receb} recebimentos")

    # 6 repasses (6 primeiros ciclos)
    rep = 0
    for nome, idx, comp, valor, status in ciclos[:6]:
        c = frappe.get_doc("Ciclo Mensal Medicao", nome)
        goc("Repasse Cooperados", {"ciclo_mensal": nome}, {
            "contrato": c.contrato, "competencia": comp,
            "valor_total_producao": valor, "valor_total_repasse": flt(valor) * 0.7,
            "data_calculo": add_days(nowdate(), -10),
            "status": "Pago" if rep < 2 else "Calculado",
            "itens_repasse": [
                {"servico": "Plantão médico", "quantidade": 30,
                 "valor_bruto": flt(valor) * 0.35, "valor_liquido": flt(valor) * 0.33,
                 "status": "Pago" if rep < 2 else "Calculado"},
            ],
        })
        rep += 1
    _log(f"{rep} repasses aos cooperados")
    return ciclos


def seed_governanca(contratos, ciclos):
    # 10 pendências (cenário 4 = contrato crítico tem várias)
    areas = ["Operação", "Financeiro", "Jurídico", "RH", "Comercial"]
    prio = ["Crítica", "Alta", "Média", "Alta", "Crítica"]
    for i in range(10):
        idx = 3 if i < 4 else (i % 7)  # concentra no contrato crítico
        desc = f"{PREFIXO} Pendência {i + 1:02d}"
        goc("Pendencia Contratual", {"descricao": desc}, {
            "contrato": contratos[idx], "area": areas[i % len(areas)],
            "tipo_pendencia": "Operacional", "prioridade": prio[i % len(prio)],
            "status": "Aberta" if i % 2 == 0 else "Em andamento",
            "data_abertura": add_days(nowdate(), -15 + i),
        })
    _log("10 pendências contratuais")

    # 8 riscos
    tipos_risco = ["Renovação", "Financeiro", "Operacional", "Jurídico"]
    crit = ["Crítica", "Alta", "Média", "Alta"]
    for i in range(8):
        idx = 4 if i < 2 else (i % 7)  # contrato vencendo: risco de renovação
        desc = f"{PREFIXO} Risco {i + 1:02d}"
        goc("Risco Contratual", {"descricao": desc}, {
            "contrato": contratos[idx], "tipo_risco": tipos_risco[i % len(tipos_risco)],
            "criticidade": crit[i % len(crit)], "probabilidade": "Alta", "impacto": "Alto",
            "status": "Em monitoramento", "plano_mitigacao": "Acompanhamento semanal.",
        })
    _log("8 riscos contratuais")

    # 5 renovações (contratos 1,3,4,5,6)
    for idx in [1, 3, 4, 5, 6]:
        c = frappe.get_doc("Contrato 360", contratos[idx])
        st = "Em negociação" if idx == 5 else "Monitorando vigência"
        goc("Renovacao Contratual", {"contrato": contratos[idx]}, {
            "vigencia_atual_fim": c.vigencia_fim, "estrategia": "Renovar",
            "status": st, "responsavel_renovacao": None,
        })
    _log("5 renovações contratuais")

    # 3 ocorrências críticas
    for i in range(3):
        idx = [3, 2, 4][i]
        desc = f"{PREFIXO} Ocorrência crítica {i + 1:02d}"
        goc("Ocorrencia Contratual", {"descricao": desc}, {
            "contrato": contratos[idx], "tipo_ocorrencia": "Operacional",
            "criticidade": "Crítica", "status": "Aberta",
            "impacto": "Risco de descontinuidade do serviço.",
            "data_abertura": add_days(nowdate(), -7 + i),
        })
    _log("3 ocorrências críticas")

    # 2 aditivos
    for i in range(2):
        idx = [1, 2][i]
        goc("Aditivo Contratual", {"contrato": contratos[idx], "numero_aditivo": f"{PREFIXO}-AD-{i + 1:02d}"}, {
            "tipo_aditivo": "Valor" if i == 0 else "Prazo",
            "status": "Assinado",
            "valor_anterior": 180000, "valor_novo": 198000,
            "data_assinatura": add_days(nowdate(), -30),
            "descricao_alteracao": "Reajuste anual por IPCA." if i == 0 else "Prorrogação de 12 meses.",
        })
    _log("2 aditivos contratuais")


# ---------------------------------------------------------------- entrypoints
def execute():
    print("== Seed de dados demo SGC COAPH ==")
    cmap = seed_contratantes()
    umap = seed_unidades(cmap)
    formalizacoes = seed_pipeline(cmap)
    contratos = seed_contratos(cmap, umap, formalizacoes)
    seed_planos_e_cooperados(contratos)
    ciclos = seed_ciclos_financeiro(contratos)
    seed_governanca(contratos, ciclos)
    frappe.db.commit()
    print("== Concluído. Dados de demonstração carregados (idempotente). ==")


def limpar():
    """Remove os dados de demonstração (prefixo DEMO). Pede confirmação implícita
    pela natureza do comando explícito. Respeita dependências (ordem reversa)."""
    print("== Removendo dados demo SGC COAPH ==")
    ordem = [
        "Aditivo Contratual", "Ocorrencia Contratual", "Renovacao Contratual",
        "Risco Contratual", "Pendencia Contratual", "Repasse Cooperados",
        "Recebimento COAPH", "Faturamento COAPH", "Ciclo Mensal Medicao",
        "Cooperado Mobilizado", "Plano Mobilizacao", "Contrato 360",
        "Formalizacao Contratual", "Disputa Proposta COAPH", "Analise Viabilidade",
        "Oportunidade COAPH", "Unidade Atendimento", "Contratante COAPH",
    ]
    for dt in ordem:
        for nome in frappe.get_all(dt, pluck="name"):
            try:
                frappe.delete_doc(dt, nome, force=True, ignore_permissions=True)
            except Exception as e:  # noqa: BLE001
                print(f"  ! não removido {dt} {nome}: {e}")
    frappe.db.commit()
    print("== Limpeza concluída. ==")
