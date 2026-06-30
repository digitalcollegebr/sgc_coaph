"""Importador one-off do backlog de contratos (planilha d_contrato).

A planilha é tratada como UMA das origens do GCOOP (o sistema de produção dos
cooperados). Todo o mapeamento e a gravação são compartilhados com a camada de
integração (`integrations/gcoop`), então este script é só um "adaptador de
arquivo" conveniente, com relatório de auditoria.

Uso:
    bench --site <site> execute \
      coaph_contract_ops.scripts.import_backlog.execute \
      --kwargs '{"path": "/tmp/d_contrato.csv"}'

Idempotente (upsert por codigo_gcoop / titulo da oportunidade).
"""

import csv
import os

import frappe

from coaph_contract_ops.integrations.gcoop import mapping
from coaph_contract_ops.integrations.gcoop import sync

DEFAULT_PATHS = ["/tmp/d_contrato.csv", "/home/frappe/frappe-bench/sites/d_contrato.csv"]


def execute(path=None):
    path = path or next((p for p in DEFAULT_PATHS if os.path.exists(p)), None)
    if not path or not os.path.exists(path):
        frappe.throw(f"CSV não encontrado. Passe --kwargs '{{\"path\": \"...\"}}'. Tentados: {DEFAULT_PATHS}")

    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    report = {"criados": 0, "atualizados": 0, "oportunidades": 0,
              "erros": [], "datas_invalidas": [], "legalidade_divergente": []}

    for i, row in enumerate(rows, start=2):  # linha 1 = cabeçalho
        rec = mapping.canonical_from_planilha(row)
        try:
            if mapping.eh_oportunidade(rec):
                sync._upsert_oportunidade(rec, report)
                report["oportunidades"] += 1
            else:
                res = sync._upsert_contrato(rec, report)
                report["criados" if res == "criado" else "atualizados"] += 1
        except Exception as e:
            report["erros"].append(f"linha {i} (gcoop {rec.get('gcoop')}): {e}")

    frappe.db.commit()
    _print_report(report, len(rows))
    return report


def _print_report(r, total):
    print("\n" + "=" * 64)
    print("IMPORTAÇÃO DO BACKLOG — RESUMO")
    print("=" * 64)
    print(f"Linhas processadas               : {total}")
    print(f"Contratos criados / atualizados  : {r['criados']} / {r['atualizados']}")
    print(f"Oportunidades (NEGOCIOS)         : {r['oportunidades']}")
    print(f"Datas inválidas (fim <= início)  : {len(r['datas_invalidas'])}")
    print(f"Legalidade divergente da origem  : {len(r['legalidade_divergente'])}")
    print(f"Erros                            : {len(r['erros'])}")
    for bloco in ("datas_invalidas", "legalidade_divergente", "erros"):
        if r[bloco]:
            print(f"\n-- {bloco} --")
            for linha in r[bloco][:25]:
                print("   ", linha)
            if len(r[bloco]) > 25:
                print(f"    ... (+{len(r[bloco]) - 25})")
    print("=" * 64 + "\n")
