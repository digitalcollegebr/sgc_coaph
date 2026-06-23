#!/usr/bin/env python3
"""Gera fixtures/notification.json — Notifications nativas do Frappe.

Canal "System Notification" (sino/bell) — NÃO exige configuração de e-mail/SMTP.
Tratam a comunicação como NOTIFICAÇÃO/ALERTA automático (não como etapa).
Reexecutável.
"""
import json
import os

FIX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "coaph_contract_ops", "coaph_contract_ops", "fixtures",
)
MODULE = "COAPH ContractOps"


def notif(name, dt, subject, message, roles, event="Value Change",
          value_changed=None, condition=None):
    return {
        "doctype": "Notification", "name": name, "enabled": 1, "is_standard": 1,
        "module": MODULE, "channel": "System Notification",
        "document_type": dt, "event": event,
        "value_changed": value_changed, "send_to_all_assignees": 0,
        "condition": condition or "", "subject": subject, "message": message,
        "recipients": [{"receiver_by_role": r} for r in roles],
    }


NOTIFS = [
    notif("Notificacao de Producao Validada", "Ciclo Mensal Medicao",
          "Produção validada — {{ doc.name }}",
          "A produção do ciclo {{ doc.competencia }} do contrato {{ doc.contrato }} "
          "foi validada. Liberar faturamento.",
          ["SGC Financeiro", "SGC Operacao"],
          value_changed="status", condition="doc.status == 'Produção validada'"),

    notif("Notificacao de Faturamento Emitido", "Faturamento COAPH",
          "Faturamento emitido — {{ doc.name }}",
          "NF {{ doc.numero_nf }} emitida para o contrato {{ doc.contrato }} "
          "(competência {{ doc.competencia }}).",
          ["SGC Financeiro", "SGC Diretoria"],
          value_changed="status", condition="doc.status == 'NF emitida'"),

    notif("Notificacao de Demonstrativos Publicados", "Repasse Cooperados",
          "Demonstrativos de repasse publicados — {{ doc.name }}",
          "Os Demonstrativos de Repasse da competência {{ doc.competencia }} "
          "foram publicados.",
          ["SGC Financeiro", "SGC RH Cooperados"],
          value_changed="status", condition="doc.status == 'Demonstrativos publicados'"),

    notif("Notificacao de Repasse Concluido", "Repasse Cooperados",
          "Repasse concluído — {{ doc.name }}",
          "O Repasse aos Cooperados da competência {{ doc.competencia }} "
          "foi concluído (pago).",
          ["SGC Financeiro", "SGC Diretoria"],
          value_changed="status", condition="doc.status == 'Pago'"),

    notif("Alerta de Pendencia Critica", "Pendencia Contratual",
          "Pendência crítica aberta — {{ doc.name }}",
          "Pendência crítica no contrato {{ doc.contrato }} (área {{ doc.area }}): "
          "{{ doc.descricao }}.",
          ["SGC Operacao", "SGC Diretoria"],
          event="New", condition="doc.prioridade == 'Crítica'"),

    notif("Alerta de Contrato Critico", "Contrato 360",
          "Saúde do contrato em risco — {{ doc.name }}",
          "O contrato {{ doc.titulo_contrato }} está com saúde "
          "'{{ doc.saude_contrato }}'. Avaliar plano de ação.",
          ["SGC Diretoria", "SGC Operacao"],
          value_changed="saude_contrato",
          condition="doc.saude_contrato in ['Crítico', 'Risco de perda']"),
]

json.dump(NOTIFS, open(os.path.join(FIX, "notification.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("Notifications geradas:", len(NOTIFS))
