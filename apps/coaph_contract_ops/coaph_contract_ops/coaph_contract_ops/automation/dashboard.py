"""Dados do Painel Executivo de Contratos (presidência/diretoria).

Um único método whitelisted, permission-aware (usa frappe.get_list para o
Contrato 360, respeitando as permissões do usuário) e com poucas queries
agregadas — sem N+1.

Semáforo:
  verde   = dentro do prazo / concluído
  amarelo = atenção (prazo próximo, pendência moderada)
  vermelho= atraso / bloqueio / vencido / risco alto
  cinza   = não iniciado / sem informação
  azul    = etapa atual em andamento
"""

import frappe
from frappe.utils import date_diff, flt, getdate, nowdate

# Conjuntos de status reaproveitados do DocType/workflow existentes
ENCERRADOS = ("Encerrado",)
NAO_OPERANTES = ("Encerrado", "Suspenso")
EM_ANDAMENTO = ("Em mobilização", "Operação assistida")
OPERACAO_REGULAR = ("Ativo", "Ativo com atenção", "Crítico")
CRITICO_STATUS = ("Crítico", "Suspenso")
SAUDE_RUIM = ("Crítico", "Risco de perda")

PEND_ABERTAS = ("Aberta", "Em andamento", "Aguardando terceiro", "Bloqueada")
RISCO_ATIVOS = ("Identificado", "Em monitoramento", "Mitigação em andamento", "Materializado")

# Macroetapas do ciclo de vida (visual) e o índice de cada status do contrato
ETAPAS_CICLO = ["Formalização", "Mobilização", "Op. Assistida",
                "Op. Regular", "Renovação", "Encerramento"]
STATUS_PARA_ETAPA = {
    "Em formalização": 0,
    "Em mobilização": 1,
    "Operação assistida": 2,
    "Ativo": 3, "Ativo com atenção": 3, "Crítico": 3, "Suspenso": 3,
    "Em renovação": 4,
    "Em encerramento": 5,
    "Encerrado": 5,
}

# Próxima ação sugerida por etapa (derivada — sem novo campo)
PROXIMA_ACAO = {
    "Em formalização": "Concluir assinatura e iniciar mobilização",
    "Em mobilização": "Credenciar cooperados e liberar operação",
    "Operação assistida": "Estabilizar operação e ativar regime regular",
    "Ativo": "Monitorar produção e ciclos mensais",
    "Ativo com atenção": "Tratar pendências e normalizar saúde",
    "Crítico": "Plano de ação imediato (decisão da diretoria)",
    "Em renovação": "Conduzir negociação/decisão de renovação",
    "Suspenso": "Avaliar retomada ou encerramento",
    "Em encerramento": "Concluir encerramento e prestação de contas",
    "Encerrado": "Arquivar e registrar lições aprendidas",
}


def _semaforo(c, dias, atrasado):
    """Cor geral do contrato."""
    vencido = dias is not None and dias < 0 and c.status_contrato not in ENCERRADOS
    if c.status_contrato == "Encerrado":
        return "verde"
    if (vencido or atrasado or c.status_contrato in CRITICO_STATUS
            or c.saude_contrato in SAUDE_RUIM):
        return "vermelho"
    if c.status_contrato == "Em formalização":
        return "cinza"
    if (dias is not None and dias <= 90) or c.saude_contrato == "Atenção":
        return "amarelo"
    return "verde"


def _etapas_visuais(c, semaforo):
    """Lista de etapas do ciclo com cor (semáforo por etapa)."""
    atual = STATUS_PARA_ETAPA.get(c.status_contrato, 0)
    encerrado = c.status_contrato == "Encerrado"
    cores = []
    for i, label in enumerate(ETAPAS_CICLO):
        if encerrado or i < atual:
            cor = "verde"            # já concluída
        elif i == atual:
            if semaforo in ("vermelho", "amarelo"):
                cor = semaforo       # etapa atual com problema
            else:
                cor = "azul"         # etapa atual em andamento
        else:
            cor = "cinza"            # ainda não iniciada
        cores.append({"label": label, "cor": cor, "atual": i == atual and not encerrado})
    return cores


@frappe.whitelist()
def get_painel_executivo():
    hoje = getdate(nowdate())

    contratos = frappe.get_list(
        "Contrato 360",
        fields=["name", "numero_contrato", "titulo_contrato", "contratante",
                "unidade_atendimento", "gestor_contrato", "responsavel_operacional",
                "status_contrato", "saude_contrato", "risco_renovacao",
                "vigencia_fim", "valor_mensal", "valor_global"],
        limit_page_length=0,
        order_by="vigencia_fim asc",
    )
    if not contratos:
        return {"as_of": str(hoje), "kpis": _kpis_vazias(), "contratos": [], "gargalos": []}

    names = [c.name for c in contratos]

    # --- flags agregadas (poucas queries, sem N+1) ---
    atraso_por_contrato = _contratos_atrasados(names)
    riscos_por_contrato = _riscos_criticos(names)
    nomes_contratante = _map_nomes("Contratante COAPH", "nome_contratante",
                                   {c.contratante for c in contratos if c.contratante})
    nomes_unidade = _map_nomes("Unidade Atendimento", "nome_unidade",
                               {c.unidade_atendimento for c in contratos if c.unidade_atendimento})

    linhas, kpis, gargalos = [], _kpis_vazias(), {}
    for c in contratos:
        dias = date_diff(c.vigencia_fim, hoje) if c.vigencia_fim else None
        atrasado = c.name in atraso_por_contrato
        riscos = riscos_por_contrato.get(c.name, 0)
        semaforo = _semaforo(c, dias, atrasado)
        depende_presidencia = (
            c.status_contrato in ("Crítico", "Suspenso", "Em renovação", "Em encerramento")
            or c.saude_contrato in SAUDE_RUIM
        )

        linhas.append({
            "name": c.name,
            "numero_contrato": c.numero_contrato or c.name,
            "titulo": c.titulo_contrato,
            "contratante": nomes_contratante.get(c.contratante, c.contratante),
            "unidade": nomes_unidade.get(c.unidade_atendimento, c.unidade_atendimento),
            "responsavel": c.gestor_contrato or c.responsavel_operacional,
            "etapa_atual": c.status_contrato,
            "saude": c.saude_contrato,
            "vigencia_fim": str(c.vigencia_fim) if c.vigencia_fim else None,
            "dias_para_vencer": dias,
            "valor_mensal": flt(c.valor_mensal),
            "valor_global": flt(c.valor_global),
            "proxima_acao": PROXIMA_ACAO.get(c.status_contrato, "—"),
            "risco": semaforo if (semaforo == "vermelho" or riscos) else c.saude_contrato,
            "riscos_criticos": riscos,
            "atrasado": atrasado,
            "depende_presidencia": depende_presidencia,
            "semaforo": semaforo,
            "etapas": _etapas_visuais(c, semaforo),
        })

        # --- KPIs ---
        ativo = c.status_contrato not in NAO_OPERANTES and c.status_contrato != "Em formalização"
        vmensal = flt(c.valor_mensal)
        if ativo:
            kpis["ativos"] += 1
            kpis["valor_total_ativos"] += vmensal
        if c.status_contrato in EM_ANDAMENTO:
            kpis["em_andamento"] += 1
        if c.status_contrato == "Em formalização":
            kpis["aguardando_aprovacao"] += 1
        if dias is not None and c.status_contrato not in ENCERRADOS:
            if dias < 0:
                kpis["vencidos"] += 1
            elif dias <= 30:
                kpis["vencendo_30"] += 1
            elif dias <= 60:
                kpis["vencendo_60"] += 1
            elif dias <= 90:
                kpis["vencendo_90"] += 1
        if atrasado:
            kpis["atrasados"] += 1
        if c.status_contrato in CRITICO_STATUS or c.saude_contrato in SAUDE_RUIM:
            kpis["bloqueados_criticos"] += 1
            kpis["valor_total_criticos"] += vmensal

        gargalos[c.status_contrato] = gargalos.get(c.status_contrato, 0) + 1

    gargalos_list = sorted(
        [{"etapa": k, "qtd": v} for k, v in gargalos.items()],
        key=lambda x: x["qtd"], reverse=True,
    )

    # Ordena por severidade (ação primeiro): vermelho > amarelo > azul > cinza > verde;
    # dentro do mesmo nível, por vencimento mais próximo.
    rank = {"vermelho": 0, "amarelo": 1, "azul": 2, "cinza": 3, "verde": 4}
    INF = 10 ** 9
    for l in linhas:
        l["severidade"] = rank.get(l["semaforo"], 9)
    linhas.sort(key=lambda l: (l["severidade"],
                               l["dias_para_vencer"] if l["dias_para_vencer"] is not None else INF))

    total = len(linhas)
    saudaveis = sum(1 for l in linhas if l["semaforo"] == "verde")
    resumo = {
        "total": total,
        "valor_sob_gestao": sum(l["valor_mensal"] for l in linhas),
        "pct_saudavel": round(saudaveis / total * 100) if total else 0,
        "criticos": kpis["bloqueados_criticos"],
        "requer_presidencia": sum(1 for l in linhas if l["depende_presidencia"]),
    }

    return {"as_of": str(hoje), "resumo": resumo, "kpis": kpis,
            "contratos": linhas, "gargalos": gargalos_list}


# ----------------------------------------------------------------- helpers
def _kpis_vazias():
    return {
        "ativos": 0, "em_andamento": 0, "aguardando_aprovacao": 0,
        "vencendo_30": 0, "vencendo_60": 0, "vencendo_90": 0,
        "vencidos": 0, "atrasados": 0, "bloqueados_criticos": 0,
        "valor_total_ativos": 0.0, "valor_total_criticos": 0.0,
    }


def _map_nomes(doctype, campo, ids):
    if not ids:
        return {}
    rows = frappe.get_all(doctype, filters={"name": ["in", list(ids)]},
                          fields=["name", campo])
    return {r["name"]: r[campo] for r in rows}


def _riscos_criticos(names):
    rows = frappe.get_all(
        "Risco Contratual",
        filters={"contrato": ["in", names],
                 "criticidade": ["in", ["Alta", "Crítica"]],
                 "status": ["in", RISCO_ATIVOS]},
        fields=["contrato", "count(name) as qtd"],
        group_by="contrato",
    )
    return {r["contrato"]: r["qtd"] for r in rows}


def _contratos_atrasados(names):
    """Contratos com pendência aberta vencida OU etapa de mobilização atrasada."""
    atrasados = set()
    hoje = nowdate()
    # Atenção: o operador "<" do frappe envolve o campo em ifnull(); por isso
    # exigimos prazo preenchido ("is set"), senão pendências sem prazo (NULL)
    # seriam tratadas como data antiga e contariam como atrasadas.
    pend = frappe.get_all(
        "Pendencia Contratual",
        filters=[["contrato", "in", names], ["status", "in", PEND_ABERTAS],
                 ["prazo", "is", "set"], ["prazo", "<", hoje]],
        fields=["distinct contrato as contrato"],
    )
    atrasados.update(p["contrato"] for p in pend if p["contrato"])

    # Atraso de mobilização só é relevante enquanto o contrato ainda está
    # mobilizando; uma etapa marcada explicitamente como "Atrasado" sempre conta.
    etapas = frappe.db.sql(
        """
        SELECT DISTINCT p.contrato
        FROM `tabEtapa Mobilizacao` e
        JOIN `tabPlano Mobilizacao` p ON p.name = e.parent
        JOIN `tabContrato 360` c ON c.name = p.contrato
        WHERE p.contrato IN %(names)s
          AND c.status_contrato IN ('Em mobilização', 'Operação assistida')
          AND e.status NOT IN ('Concluído', 'Cancelado')
          AND (e.status = 'Atrasado' OR e.data_fim_prevista < %(hoje)s)
        """,
        {"names": names, "hoje": hoje}, as_dict=True,
    )
    atrasados.update(r["contrato"] for r in etapas if r["contrato"])
    return atrasados
