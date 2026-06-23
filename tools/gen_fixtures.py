#!/usr/bin/env python3
"""Gera as fixtures do app coaph_contract_ops:
  fixtures/role.json
  fixtures/workflow_state.json
  fixtures/workflow_action_master.json
  fixtures/workflow.json
  fixtures/workspace.json

Os estados de cada workflow casam EXATAMENTE com as opções do campo de status
do respectivo DocType (workflow_state_field). Reexecutável.
"""
import json
import os

FIX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apps", "coaph_contract_ops", "coaph_contract_ops", "fixtures",
)
os.makedirs(FIX, exist_ok=True)

# Papéis (sem acento no nome técnico)
ROLES = [
    "SGC Administrador", "SGC Diretoria", "SGC Comercial", "SGC Juridico",
    "SGC Mobilizacao", "SGC Operacao", "SGC Financeiro", "SGC RH Cooperados",
    "SGC Consulta",
]

COMERCIAL, JURIDICO, DIRETORIA = "SGC Comercial", "SGC Juridico", "SGC Diretoria"
MOBIL, OPER, FIN = "SGC Mobilizacao", "SGC Operacao", "SGC Financeiro"

# style por palavra-chave para Workflow State
STYLE = {
    "Aprov": "Success", "Vencid": "Success", "Renovado": "Success",
    "Ativo": "Success", "Concluíd": "Success", "Operação liberada": "Success",
    "Recebid": "Success", "Pago": "Success", "assinado": "Success", "encerrada": "Success",
    "Reprov": "Danger", "Perdid": "Danger", "Cancel": "Danger", "recusado": "Danger",
    "Crítico": "Danger", "Bloquead": "Danger", "Não renovado": "Danger", "Descartad": "Danger",
    "Atenção": "Warning", "Aguardando": "Warning", "Alerta": "Warning", "Atras": "Warning",
    "negociação": "Warning", "Revisão": "Warning", "Suspenso": "Warning",
}


def style_for(state):
    for k, v in STYLE.items():
        if k in state:
            return v
    return "Primary"


# (workflow_name, document_type, state_field, owner_role, states[], transitions[(from, action, to, role)])
WF = []

WF.append((
    "Workflow Oportunidade COAPH", "Oportunidade COAPH", "status", COMERCIAL,
    ["Demanda identificada", "Oportunidade registrada", "Oportunidade qualificada",
     "Em análise de viabilidade", "Aprovada para avanço", "Convertida em disputa/proposta",
     "Descartada"],
    [("Demanda identificada", "Registrar", "Oportunidade registrada", COMERCIAL),
     ("Oportunidade registrada", "Qualificar", "Oportunidade qualificada", COMERCIAL),
     ("Oportunidade qualificada", "Enviar para viabilidade", "Em análise de viabilidade", COMERCIAL),
     ("Em análise de viabilidade", "Aprovar avanço", "Aprovada para avanço", DIRETORIA),
     ("Aprovada para avanço", "Converter em disputa/proposta", "Convertida em disputa/proposta", COMERCIAL),
     ("Oportunidade registrada", "Descartar", "Descartada", COMERCIAL),
     ("Oportunidade qualificada", "Descartar", "Descartada", COMERCIAL),
     ("Em análise de viabilidade", "Descartar", "Descartada", DIRETORIA)],
))

WF.append((
    "Workflow Analise Viabilidade", "Analise Viabilidade", "status", COMERCIAL,
    ["Em análise técnica", "Em análise financeira", "Em análise jurídica", "Aguardando comitê",
     "Aprovada", "Reprovada", "Revisão solicitada"],
    [("Em análise técnica", "Concluir análise técnica", "Em análise financeira", COMERCIAL),
     ("Em análise financeira", "Concluir análise financeira", "Em análise jurídica", FIN),
     ("Em análise jurídica", "Enviar ao comitê", "Aguardando comitê", JURIDICO),
     ("Aguardando comitê", "Aprovar", "Aprovada", DIRETORIA),
     ("Aguardando comitê", "Reprovar", "Reprovada", DIRETORIA),
     ("Aguardando comitê", "Solicitar revisão", "Revisão solicitada", DIRETORIA),
     ("Revisão solicitada", "Retomar análise", "Em análise técnica", COMERCIAL)],
))

WF.append((
    "Workflow Disputa Proposta COAPH", "Disputa Proposta COAPH", "status", COMERCIAL,
    ["Edital/BID recebido", "Em análise", "Documentação em preparação", "Proposta em elaboração",
     "Proposta enviada", "Aguardando resultado", "Vencida", "Perdida", "Cancelada"],
    [("Edital/BID recebido", "Analisar", "Em análise", COMERCIAL),
     ("Em análise", "Preparar documentação", "Documentação em preparação", COMERCIAL),
     ("Documentação em preparação", "Elaborar proposta", "Proposta em elaboração", COMERCIAL),
     ("Proposta em elaboração", "Enviar proposta", "Proposta enviada", COMERCIAL),
     ("Proposta enviada", "Aguardar resultado", "Aguardando resultado", COMERCIAL),
     ("Aguardando resultado", "Registrar vitória", "Vencida", COMERCIAL),
     ("Aguardando resultado", "Registrar derrota", "Perdida", COMERCIAL),
     ("Em análise", "Cancelar", "Cancelada", COMERCIAL),
     ("Aguardando resultado", "Cancelar", "Cancelada", COMERCIAL)],
))

WF.append((
    "Workflow Formalizacao Contratual", "Formalizacao Contratual", "status", JURIDICO,
    ["Aguardando minuta", "Minuta em análise jurídica", "Minuta em negociação", "Ajustes solicitados",
     "Aprovada juridicamente", "Em assinatura", "Contrato assinado", "Contrato recusado", "Cancelada"],
    [("Aguardando minuta", "Receber minuta", "Minuta em análise jurídica", JURIDICO),
     ("Minuta em análise jurídica", "Negociar", "Minuta em negociação", JURIDICO),
     ("Minuta em negociação", "Solicitar ajustes", "Ajustes solicitados", JURIDICO),
     ("Ajustes solicitados", "Reanalisar", "Minuta em análise jurídica", JURIDICO),
     ("Minuta em negociação", "Aprovar juridicamente", "Aprovada juridicamente", JURIDICO),
     ("Aprovada juridicamente", "Enviar para assinatura", "Em assinatura", JURIDICO),
     ("Em assinatura", "Confirmar assinatura", "Contrato assinado", JURIDICO),
     ("Em assinatura", "Recusar contrato", "Contrato recusado", DIRETORIA),
     ("Minuta em análise jurídica", "Cancelar", "Cancelada", JURIDICO)],
))

WF.append((
    "Workflow Contrato 360", "Contrato 360", "status_contrato", OPER,
    ["Em formalização", "Em mobilização", "Operação assistida", "Ativo", "Ativo com atenção",
     "Crítico", "Em renovação", "Suspenso", "Em encerramento", "Encerrado"],
    [("Em formalização", "Iniciar mobilização", "Em mobilização", MOBIL),
     ("Em mobilização", "Liberar operação assistida", "Operação assistida", OPER),
     ("Operação assistida", "Ativar operação regular", "Ativo", OPER),
     ("Ativo", "Sinalizar atenção", "Ativo com atenção", OPER),
     ("Ativo com atenção", "Escalar para crítico", "Crítico", OPER),
     ("Ativo com atenção", "Normalizar", "Ativo", OPER),
     ("Crítico", "Normalizar", "Ativo com atenção", OPER),
     ("Ativo", "Iniciar renovação", "Em renovação", COMERCIAL),
     ("Ativo com atenção", "Iniciar renovação", "Em renovação", COMERCIAL),
     ("Em renovação", "Iniciar encerramento", "Em encerramento", COMERCIAL),
     ("Ativo", "Suspender", "Suspenso", DIRETORIA),
     ("Suspenso", "Reativar", "Ativo", DIRETORIA),
     ("Em encerramento", "Encerrar contrato", "Encerrado", DIRETORIA)],
))

WF.append((
    "Workflow Plano Mobilizacao", "Plano Mobilizacao", "status", MOBIL,
    ["Aguardando kickoff", "Kickoff interno realizado", "Plano de mobilização definido",
     "Contrato parametrizado", "Equipe dimensionada", "Cooperados em mobilização",
     "Cooperados credenciados", "Onboarding concluído", "Operação liberada", "Mobilização cancelada"],
    [("Aguardando kickoff", "Realizar kickoff", "Kickoff interno realizado", MOBIL),
     ("Kickoff interno realizado", "Definir plano", "Plano de mobilização definido", MOBIL),
     ("Plano de mobilização definido", "Parametrizar contrato", "Contrato parametrizado", MOBIL),
     ("Contrato parametrizado", "Dimensionar equipe", "Equipe dimensionada", MOBIL),
     ("Equipe dimensionada", "Mobilizar cooperados", "Cooperados em mobilização", MOBIL),
     ("Cooperados em mobilização", "Credenciar cooperados", "Cooperados credenciados", MOBIL),
     ("Cooperados credenciados", "Concluir onboarding", "Onboarding concluído", MOBIL),
     ("Onboarding concluído", "Liberar operação", "Operação liberada", MOBIL),
     ("Aguardando kickoff", "Cancelar mobilização", "Mobilização cancelada", DIRETORIA)],
))

WF.append((
    "Workflow Ciclo Mensal Medicao", "Ciclo Mensal Medicao", "status", OPER,
    ["Competência aberta", "Produção em registro", "Produção em conferência", "Produção fechada",
     "Produção validada", "Prazo de contestação", "Liberada para faturamento", "NF emitida",
     "Aguardando recebimento", "Recebida", "Repasse calculado", "Demonstrativos publicados",
     "Repasse executado", "Competência encerrada", "Bloqueada"],
    [("Competência aberta", "Iniciar registro", "Produção em registro", OPER),
     ("Produção em registro", "Enviar para conferência", "Produção em conferência", OPER),
     ("Produção em conferência", "Fechar produção", "Produção fechada", OPER),
     ("Produção fechada", "Validar produção", "Produção validada", OPER),
     ("Produção validada", "Abrir prazo de contestação", "Prazo de contestação", OPER),
     ("Prazo de contestação", "Liberar para faturamento", "Liberada para faturamento", OPER),
     ("Produção validada", "Liberar para faturamento", "Liberada para faturamento", OPER),
     ("Liberada para faturamento", "Emitir NF", "NF emitida", FIN),
     ("NF emitida", "Aguardar recebimento", "Aguardando recebimento", FIN),
     ("Aguardando recebimento", "Registrar recebimento", "Recebida", FIN),
     ("Recebida", "Calcular repasse", "Repasse calculado", FIN),
     ("Repasse calculado", "Publicar demonstrativos", "Demonstrativos publicados", FIN),
     ("Demonstrativos publicados", "Executar repasse", "Repasse executado", FIN),
     ("Repasse executado", "Encerrar competência", "Competência encerrada", OPER),
     ("Produção em conferência", "Bloquear", "Bloqueada", OPER)],
))

WF.append((
    "Workflow Renovacao Contratual", "Renovacao Contratual", "status", COMERCIAL,
    ["Monitorando vigência", "Alerta 180 dias", "Alerta 120 dias", "Alerta 90 dias",
     "Em análise de renovação", "Em negociação", "Minuta de renovação", "Renovado",
     "Não renovado", "Encerrado"],
    [("Monitorando vigência", "Disparar alerta 180", "Alerta 180 dias", COMERCIAL),
     ("Alerta 180 dias", "Disparar alerta 120", "Alerta 120 dias", COMERCIAL),
     ("Alerta 120 dias", "Disparar alerta 90", "Alerta 90 dias", COMERCIAL),
     ("Alerta 90 dias", "Analisar renovação", "Em análise de renovação", COMERCIAL),
     ("Em análise de renovação", "Negociar", "Em negociação", COMERCIAL),
     ("Em negociação", "Elaborar minuta", "Minuta de renovação", JURIDICO),
     ("Minuta de renovação", "Confirmar renovação", "Renovado", DIRETORIA),
     ("Em análise de renovação", "Não renovar", "Não renovado", DIRETORIA),
     ("Em negociação", "Encerrar", "Encerrado", DIRETORIA)],
))

# ---- gera role.json ----
roles = [{"doctype": "Role", "name": r, "role_name": r, "desk_access": 1} for r in ROLES]
json.dump(roles, open(os.path.join(FIX, "role.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

# ---- coleta estados e ações ----
all_states, all_actions = set(), set()
for _, _, _, _, states, transitions in WF:
    all_states.update(states)
    all_actions.update(t[1] for t in transitions)

ws = [{"doctype": "Workflow State", "name": s, "workflow_state_name": s, "style": style_for(s)}
      for s in sorted(all_states)]
json.dump(ws, open(os.path.join(FIX, "workflow_state.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

wam = [{"doctype": "Workflow Action Master", "name": a, "workflow_action_name": a}
       for a in sorted(all_actions)]
json.dump(wam, open(os.path.join(FIX, "workflow_action_master.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

# ---- gera workflow.json ----
workflows = []
for name, dt, field, owner, states, transitions in WF:
    state_rows = []
    for s in states:
        state_rows.append({
            "state": s, "doc_status": "0", "allow_edit": owner,
            "is_optional_state": 0,
        })
    trans_rows = []
    for frm, action, to, role in transitions:
        trans_rows.append({
            "state": frm, "action": action, "next_state": to,
            "allowed": role, "allow_self_approval": 1,
        })
    workflows.append({
        "doctype": "Workflow", "name": name, "workflow_name": name,
        "document_type": dt, "is_active": 1, "override_status": 0,
        "send_email_alert": 0, "workflow_state_field": field,
        "states": state_rows, "transitions": trans_rows,
    })
json.dump(workflows, open(os.path.join(FIX, "workflow.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("Fixtures geradas:", sorted(os.listdir(FIX)))
print(f"  roles={len(roles)} states={len(ws)} actions={len(wam)} workflows={len(workflows)}")
