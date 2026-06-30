"""Sincronização GCOOP -> SGC.

Consome registros canônicos do GcoopClient e faz upsert idempotente por
`codigo_gcoop` no Contrato 360 (e roteia pré-contratos para Oportunidade COAPH).
O status é gravado via db.set_value (o Workflow bloquearia transição direta).

Uso manual:
    bench --site <site> execute \
      coaph_contract_ops.integrations.gcoop.sync.sincronizar_contratos

Botão "Sincronizar agora" em GCOOP Settings e job diário (se ativo) chamam o
mesmo ponto.
"""

import frappe
from frappe.utils import flt, now_datetime

from coaph_contract_ops.integrations.gcoop import mapping
from coaph_contract_ops.integrations.gcoop.client import SETTINGS, GcoopClient

_contratante_cache = {}


def _get_or_create_contratante(nome, natureza_raw=None, cnpj=None, uf=None, municipio=None):
    nome = (nome or "").strip() or "NÃO INFORMADO"
    if nome in _contratante_cache:
        return _contratante_cache[nome]
    existing = frappe.db.get_value("Contratante COAPH", {"nome_contratante": nome}, "name")
    if existing:
        _contratante_cache[nome] = existing
        return existing
    natureza = mapping.NATUREZA.get((natureza_raw or "").strip().upper())
    tipo = natureza if natureza in ("Público", "Privado") else "Outro"
    doc = frappe.get_doc({
        "doctype": "Contratante COAPH", "nome_contratante": nome,
        "tipo_contratante": tipo, "status": "Ativo",
        "cnpj": (cnpj or "").strip(), "cidade": (municipio or "").strip(),
        "estado": (uf or "").strip(),
    }).insert(ignore_permissions=True)
    _contratante_cache[nome] = doc.name
    return doc.name


def _upsert_contrato(rec, report):
    gcoop = (rec.get("gcoop") or "").strip()
    fields, data_invalida = mapping.to_contrato_fields(rec)
    contratante = _get_or_create_contratante(
        rec.get("contratante_nome"), rec.get("natureza_raw"),
        rec.get("cnpj"), rec.get("uf"), rec.get("municipio"),
    )
    fields["contratante"] = contratante

    nome = frappe.db.get_value("Contrato 360", {"codigo_gcoop": gcoop}, "name") if gcoop else None
    doc = frappe.get_doc("Contrato 360", nome) if nome else frappe.new_doc("Contrato 360")
    doc.update(fields)
    doc.save(ignore_permissions=True)

    alvo = mapping.status_contrato_de(rec)
    if alvo and doc.status_contrato != alvo:
        frappe.db.set_value("Contrato 360", doc.name, "status_contrato", alvo, update_modified=False)

    if data_invalida:
        report["datas_invalidas"].append(f"{gcoop} ({fields['titulo_contrato']})")
    leg = mapping.norm_pct(rec.get("legalidade_origem"))
    if leg is not None and abs(flt(doc.taxa_legalidade) - leg) > 0.05:
        report["legalidade_divergente"].append(
            f"{gcoop}: calculada {doc.taxa_legalidade:.2f} x origem {leg:.2f}")
    return "atualizado" if nome else "criado"


def _upsert_oportunidade(rec, report):
    titulo = (rec.get("titulo") or "").strip() or f"Oportunidade {rec.get('gcoop')}"
    contratante = _get_or_create_contratante(
        rec.get("contratante_nome"), rec.get("natureza_raw"),
        rec.get("cnpj"), rec.get("uf"), rec.get("municipio"))
    natureza = mapping.NATUREZA.get((rec.get("natureza_raw") or "").strip().upper())
    valor = mapping.norm_money(rec.get("valor_global"))
    nome = frappe.db.get_value("Oportunidade COAPH", {"titulo": titulo}, "name")
    doc = frappe.get_doc("Oportunidade COAPH", nome) if nome else frappe.new_doc("Oportunidade COAPH")
    doc.update({
        "titulo": titulo, "contratante": contratante,
        "tipo_cliente": natureza if natureza in ("Público", "Privado") else None,
        "data_identificacao": mapping.norm_date(rec.get("vigencia_inicio")),
        "valor_estimado_anual": valor,
        "valor_estimado_mensal": (valor / 12.0) if valor else None,
    })
    doc.save(ignore_permissions=True)
    if doc.status != "Oportunidade registrada":
        frappe.db.set_value("Oportunidade COAPH", doc.name, "status",
                            "Oportunidade registrada", update_modified=False)
    return "atualizado" if nome else "criado"


@frappe.whitelist()
def sincronizar_contratos():
    """Puxa contratos do GCOOP (via client) e faz upsert no SGC."""
    client = GcoopClient()
    registros = client.listar_contratos()
    report = {"criados": 0, "atualizados": 0, "oportunidades": 0,
              "erros": [], "datas_invalidas": [], "legalidade_divergente": []}
    for i, rec in enumerate(registros, start=1):
        try:
            if mapping.eh_oportunidade(rec):
                _upsert_oportunidade(rec, report)
                report["oportunidades"] += 1
            else:
                res = _upsert_contrato(rec, report)
                report["criados" if res == "criado" else "atualizados"] += 1
        except Exception as e:
            report["erros"].append(f"#{i} (gcoop {rec.get('gcoop')}): {e}")

    frappe.db.set_value(SETTINGS, None, "last_sync", now_datetime())
    frappe.db.commit()
    frappe.logger("coaph_sgc").info(f"[GCOOP] sync: {report['criados']} criados, "
                                    f"{report['atualizados']} atualizados, {len(report['erros'])} erros")
    return report


def sincronizar_agendado():
    """Job diário — só roda se a integração estiver ativa em GCOOP Settings."""
    if not frappe.db.get_single_value(SETTINGS, "ativo"):
        return
    sincronizar_contratos()
