"""Tarefas agendadas (scheduler diário) de governança contratual.

1. verificar_renovacoes:
   - identifica Contratos 360 vencendo em 180/120/90/60/30 dias;
   - cria/atualiza um documento Renovacao Contratual (sem duplicar);
   - registra alerta/log e ajusta status do contrato para "Em renovacao".

2. verificar_mobilizacoes_atrasadas:
   - identifica Etapas de Mobilização com prazo vencido e status não concluído;
   - marca a etapa como "Atrasado";
   - gera Pendencia Contratual quando o SLA estiver vencido (sem duplicar).

Idempotente: sempre verifica existência antes de criar.
"""

import frappe
from frappe.utils import add_days, date_diff, getdate, nowdate

MARCOS_ALERTA = [180, 120, 90, 60, 30]


def verificar_renovacoes():
    hoje = getdate(nowdate())
    contratos = frappe.get_all(
        "Contrato 360",
        filters={
            "status_contrato": ["in", [
                "Ativo", "Ativo com atenção", "Operação assistida", "Crítico",
            ]],
            "vigencia_fim": ["is", "set"],
        },
        fields=["name", "contratante", "vigencia_fim", "status_contrato"],
    )

    for c in contratos:
        dias = date_diff(getdate(c.vigencia_fim), hoje)
        if dias < 0:
            continue
        marco = next((m for m in MARCOS_ALERTA if dias <= m), None)
        if marco is None:
            continue
        _garantir_renovacao(c, dias)


def _garantir_renovacao(contrato, dias):
    nome = frappe.db.get_value("Renovacao Contratual", {"contrato": contrato.name}, "name")
    vigencia_fim = getdate(contrato.vigencia_fim)
    valores = {
        "vigencia_atual_fim": vigencia_fim,
        "dias_para_vencimento": dias,
        "data_alerta_180": add_days(vigencia_fim, -180),
        "data_alerta_120": add_days(vigencia_fim, -120),
        "data_alerta_90": add_days(vigencia_fim, -90),
        "data_alerta_60": add_days(vigencia_fim, -60),
        "data_alerta_30": add_days(vigencia_fim, -30),
    }

    if nome:
        ren = frappe.get_doc("Renovacao Contratual", nome)
        ren.update(valores)
        ren.save(ignore_permissions=True)
    else:
        ren = frappe.get_doc({
            "doctype": "Renovacao Contratual",
            "contrato": contrato.name,
            "status": "Monitorando vigência",
            "estrategia": "Aguardar",
            **valores,
        })
        ren.insert(ignore_permissions=True)

    # Sinaliza o contrato como em renovação quando entra no marco de 90 dias.
    if dias <= 90 and contrato.status_contrato not in ("Em renovação", "Encerrado"):
        frappe.db.set_value("Contrato 360", contrato.name, "status_contrato", "Em renovação")

    frappe.logger("coaph_sgc").info(
        f"[Renovacao] Contrato {contrato.name} a {dias} dias do vencimento."
    )


def verificar_mobilizacoes_atrasadas():
    hoje = getdate(nowdate())
    planos = frappe.get_all("Plano Mobilizacao", fields=["name", "contrato"])
    for plano in planos:
        doc = frappe.get_doc("Plano Mobilizacao", plano.name)
        alterou = False
        for etapa in doc.get("etapas", []):
            if (
                etapa.data_fim_prevista
                and etapa.status not in ("Concluído", "Concluido", "Cancelado")
                and getdate(etapa.data_fim_prevista) < hoje
            ):
                if etapa.status != "Atrasado":
                    etapa.status = "Atrasado"
                    alterou = True
                _gerar_pendencia_sla(doc, etapa, hoje)
        if alterou:
            doc.save(ignore_permissions=True)


def _gerar_pendencia_sla(plano, etapa, hoje):
    if not etapa.sla_dias or not etapa.data_inicio_prevista:
        return
    limite = add_days(getdate(etapa.data_inicio_prevista), int(etapa.sla_dias))
    if getdate(hoje) <= limite:
        return

    descricao = f"SLA vencido na etapa de mobilização: {etapa.etapa or etapa.idx}"
    existe = frappe.db.exists("Pendencia Contratual", {
        "contrato": plano.contrato,
        "descricao": descricao,
        "status": ["in", ["Aberta", "Em andamento", "Aguardando terceiro", "Bloqueada"]],
    })
    if existe:
        return

    frappe.get_doc({
        "doctype": "Pendencia Contratual",
        "contrato": plano.contrato,
        "area": etapa.area_responsavel or "Operação",
        "tipo_pendencia": "SLA de mobilização",
        "descricao": descricao,
        "prioridade": "Alta",
        "status": "Aberta",
        "data_abertura": hoje,
    }).insert(ignore_permissions=True)
