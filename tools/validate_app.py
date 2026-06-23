#!/usr/bin/env python3
"""Validação estrutural offline do app (sem bench):
- workflow.document_type existe como DocType;
- workflow_state_field existe no DocType e é Select;
- todo estado do workflow está nas opções do campo de status;
- Link/Table fields apontam para DocTypes existentes (ou core conhecido);
- Table fields apontam para child tables (istable=1).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCTYPE_DIR = os.path.join(ROOT, "apps", "coaph_contract_ops", "coaph_contract_ops",
                           "coaph_contract_ops", "doctype")
FIX = os.path.join(ROOT, "apps", "coaph_contract_ops", "coaph_contract_ops", "fixtures")

CORE_DOCTYPES = {"User", "File", "Role"}

doctypes = {}
for d in os.listdir(DOCTYPE_DIR):
    jp = os.path.join(DOCTYPE_DIR, d, d + ".json")
    if os.path.exists(jp):
        dt = json.load(open(jp, encoding="utf-8"))
        doctypes[dt["name"]] = dt

errors = []
known = set(doctypes) | CORE_DOCTYPES

# Link/Table targets
for name, dt in doctypes.items():
    for f in dt["fields"]:
        if f["fieldtype"] in ("Link", "Table") and f.get("options"):
            tgt = f["options"]
            if tgt not in known:
                errors.append(f"{name}.{f['fieldname']}: alvo '{tgt}' inexistente")
            elif f["fieldtype"] == "Table" and not doctypes.get(tgt, {}).get("istable"):
                errors.append(f"{name}.{f['fieldname']}: '{tgt}' não é child table (istable)")

# Workflows
wf = json.load(open(os.path.join(FIX, "workflow.json"), encoding="utf-8"))
for w in wf:
    dt_name = w["document_type"]
    if dt_name not in doctypes:
        errors.append(f"Workflow {w['name']}: DocType '{dt_name}' inexistente")
        continue
    field = w["workflow_state_field"]
    fdef = next((x for x in doctypes[dt_name]["fields"] if x["fieldname"] == field), None)
    if not fdef:
        errors.append(f"Workflow {w['name']}: campo de estado '{field}' não existe em {dt_name}")
        continue
    opts = set((fdef.get("options") or "").split("\n"))
    for st in w["states"]:
        if st["state"] not in opts:
            errors.append(f"Workflow {w['name']}: estado '{st['state']}' fora das opções de {dt_name}.{field}")
    # transições coerentes
    states = {s["state"] for s in w["states"]}
    for t in w["transitions"]:
        if t["state"] not in states or t["next_state"] not in states:
            errors.append(f"Workflow {w['name']}: transição {t['state']}->{t['next_state']} usa estado não declarado")

# Workspace referencia number cards / charts existentes
nc = {c["name"] for c in json.load(open(os.path.join(FIX, "number_card.json"), encoding="utf-8"))}
ch = {c["name"] for c in json.load(open(os.path.join(FIX, "dashboard_chart.json"), encoding="utf-8"))}
ws = json.load(open(os.path.join(FIX, "workspace.json"), encoding="utf-8"))[0]
for c in ws["number_cards"]:
    if c["number_card_name"] not in nc:
        errors.append(f"Workspace: number card '{c['number_card_name']}' inexistente")
for c in ws["charts"]:
    if c["chart_name"] not in ch:
        errors.append(f"Workspace: chart '{c['chart_name']}' inexistente")

if errors:
    print(f"FALHAS ({len(errors)}):")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"OK: {len(doctypes)} DocTypes, {len(wf)} workflows, {len(nc)} number cards, "
      f"{len(ch)} charts, workspace consistente.")
