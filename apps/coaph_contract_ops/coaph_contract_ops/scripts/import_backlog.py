"""Importador do backlog de contratos da COAPH (planilha d_contrato).

Lê o CSV exportado da planilha "BACK LOG DOS CONTRATOS" e carrega:
  - Contratos vigentes/vencidos/encerrados/em renovação  -> Contrato 360
  - Linhas em "NEGOCIOS" (pré-contrato)                   -> Oportunidade COAPH

Características:
  - Idempotente: contratos por `codigo_gcoop`; oportunidades por `titulo`.
  - Normaliza moeda ("R$ 1.234,56"), percentual ("7,00%") e natureza.
  - Cria Contratante COAPH faltante (por nome).
  - Não falha a carga inteira por causa de uma linha: erros são coletados e
    impressos em um relatório final.

Uso:
    bench --site <site> execute \
      coaph_contract_ops.scripts.import_backlog.execute \
      --kwargs '{"path": "/tmp/d_contrato.csv"}'

Rodar 2x não duplica (faz upsert).
"""

import csv
import os

import frappe
from frappe.utils import flt, getdate

# Locais padrão onde procurar o CSV se `path` não for informado.
DEFAULT_PATHS = [
    "/tmp/d_contrato.csv",
    "/home/frappe/frappe-bench/sites/d_contrato.csv",
]

# ----------------------------------------------------------------- mapeamentos
NATUREZA = {"PUBLICO": "Público", "PUBLICA": "Público",
            "PRIVADA": "Privado", "PRIVADO": "Privado"}

MODALIDADE = {
    "VENDA DIRETA": "Venda Direta",
    "LICITACAO": "Licitação", "LICITAÇÃO": "Licitação",
    "ADESAO": "Adesão", "ADESÃO": "Adesão",
    "DISPENSA": "Dispensa",
    "CREDENCIAMENTO": "Credenciamento",
}

ESPECIALIDADE = {
    "ENFERMEIRO": "Enfermeiro",
    "MEDICO": "Médico", "MÉDICO": "Médico",
    "TEC DE ENFERMAGEM": "Téc. de Enfermagem",
    "TÉC DE ENFERMAGEM": "Téc. de Enfermagem",
    "FARMACEUTICOS": "Farmacêutico", "FARMACÊUTICOS": "Farmacêutico",
    "FARMACEUTICO": "Farmacêutico",
    "NUTRICIONISTA": "Nutricionista",
    "FISIOTERAPEUTA": "Fisioterapeuta",
    "CATEGORIAS": "Categorias (múltiplas)",
}


# ----------------------------------------------------------------- normalização
def _norm_money(raw):
    """'R$  857.559,20' / '6.324.000,00' / 'R$ -' / '' -> float | None."""
    if raw is None:
        return None
    s = str(raw).replace("R$", "").replace(" ", "").strip()
    if s in ("", "-", "0", "0,00"):
        return 0.0 if s in ("0", "0,00") else None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _norm_pct(raw):
    """'7,00%' / '7,97' / '0' / '' -> float | None."""
    if raw is None:
        return None
    s = str(raw).replace("%", "").replace(" ", "").strip()
    if s == "":
        return None
    s = s.replace(".", "").replace(",", ".") if ("," in s) else s
    try:
        return float(s)
    except ValueError:
        return None


def _norm_date(raw):
    if not raw or not str(raw).strip():
        return None
    try:
        return getdate(str(raw).strip())
    except Exception:
        return None


def _clean(s):
    return (s or "").strip()


def _map(table, raw):
    if not raw:
        return None
    return table.get(str(raw).strip().upper())


# ----------------------------------------------------------------- contratante
_contratante_cache = {}


def _get_or_create_contratante(nome, natureza=None, cnpj=None, uf=None, municipio=None):
    nome = _clean(nome) or "NÃO INFORMADO"
    if nome in _contratante_cache:
        return _contratante_cache[nome]

    existing = frappe.db.get_value("Contratante COAPH", {"nome_contratante": nome}, "name")
    if existing:
        _contratante_cache[nome] = existing
        return existing

    tipo = "Público" if natureza == "Público" else ("Privado" if natureza == "Privado" else "Outro")
    doc = frappe.get_doc({
        "doctype": "Contratante COAPH",
        "nome_contratante": nome,
        "tipo_contratante": tipo,
        "status": "Ativo",
        "cnpj": _clean(cnpj),
        "cidade": _clean(municipio),
        "estado": _clean(uf),
    })
    doc.insert(ignore_permissions=True)
    _contratante_cache[nome] = doc.name
    return doc.name


# ----------------------------------------------------------------- import linha
def _import_contrato(row, natureza, contratante, report):
    gcoop = _clean(row.get("gcoop"))
    titulo = _clean(row.get("nome_contratro_completo")) or f"Contrato {gcoop}"

    nome = frappe.db.get_value("Contrato 360", {"codigo_gcoop": gcoop}, "name") if gcoop else None
    doc = frappe.get_doc("Contrato 360", nome) if nome else frappe.new_doc("Contrato 360")

    ini = _norm_date(row.get("data_inicio_contrato"))
    fim = _norm_date(row.get("data_fim_contrato"))
    # A validação do DocType exige fim > início. Em dados históricos isso às
    # vezes não bate: nesse caso mantemos o início e reportamos, sem travar.
    if ini and fim and fim <= ini:
        report["datas_invalidas"].append(f"{gcoop} ({titulo}): fim {fim} <= início {ini}")
        fim = None

    leg_planilha = _norm_pct(row.get("legalidade"))

    doc.update({
        "codigo_gcoop": gcoop or None,
        "numero_contrato": _clean(row.get("numero_contrato")) or None,
        "titulo_contrato": titulo,
        "sigla_contrato": _clean(row.get("contrato")) or None,
        "cnpj_contratante": _clean(row.get("cnpj")) or None,
        "contratante": contratante,
        "municipio": _clean(row.get("localidades")) or None,
        "uf": _clean(row.get("UF")) or None,
        "tipo_contrato": natureza or None,
        "modalidade_contratacao": _map(MODALIDADE, row.get("tipo_contrato")),
        "vigencia_inicio": ini,
        "vigencia_fim": fim,
        "valor_global": _norm_money(row.get(" valor_inicial_contrato")),
        "quantidade_cooperados_prevista": int(flt(_clean(row.get("qtd_cooperados")) or 0)),
        "taxa_admin_contratual": _norm_pct(row.get("taxa_adm")),
        "taxa_admin_bruta": _norm_pct(row.get("tx_adm_bruta")),
        "percentual_impostos": _norm_pct(row.get("impostos")),
        "taxa_comercial": _norm_pct(row.get("taxa_comercial")),
        "especialidade_principal": _map(ESPECIALIDADE, row.get("especialidade")) or "Outro",
        "especialidades": _clean(row.get("especialidade")) or None,
    })

    # O status NÃO entra no save: o Workflow ativo bloquearia a transição direta.
    # Salvamos no estado atual/inicial e gravamos o estado final via db.set_value
    # (padrão de migração — não dispara o workflow).
    doc.save(ignore_permissions=True)
    alvo = _status_contrato(row.get("status"))
    if alvo and doc.status_contrato != alvo:
        frappe.db.set_value("Contrato 360", doc.name, "status_contrato", alvo, update_modified=False)

    # Confronta a legalidade calculada com a da planilha (auditoria de migração).
    if leg_planilha is not None and abs(flt(doc.taxa_legalidade) - leg_planilha) > 0.05:
        report["legalidade_divergente"].append(
            f"{gcoop} ({titulo}): calculada {doc.taxa_legalidade:.2f} x planilha {leg_planilha:.2f}"
        )
    return "atualizado" if nome else "criado"


def _import_oportunidade(row, natureza, contratante, report):
    titulo = _clean(row.get("nome_contratro_completo")) or f"Oportunidade {_clean(row.get('gcoop'))}"
    nome = frappe.db.get_value("Oportunidade COAPH", {"titulo": titulo}, "name")
    doc = frappe.get_doc("Oportunidade COAPH", nome) if nome else frappe.new_doc("Oportunidade COAPH")

    valor_global = _norm_money(row.get(" valor_inicial_contrato"))
    doc.update({
        "titulo": titulo,
        "contratante": contratante,
        "tipo_cliente": natureza if natureza in ("Público", "Privado") else None,
        "data_identificacao": _norm_date(row.get("data_inicio_contrato")),
        "valor_estimado_anual": valor_global,
        "valor_estimado_mensal": (valor_global / 12.0) if valor_global else None,
        "descricao": f"Importado do backlog (gcoop {_clean(row.get('gcoop'))}). "
                     f"Modalidade: {_clean(row.get('tipo_contrato'))}; "
                     f"Especialidade: {_clean(row.get('especialidade'))}; "
                     f"Localidade: {_clean(row.get('localidades'))}/{_clean(row.get('UF'))}.",
    })
    doc.save(ignore_permissions=True)
    if doc.status != "Oportunidade registrada":
        frappe.db.set_value("Oportunidade COAPH", doc.name, "status",
                            "Oportunidade registrada", update_modified=False)
    return "atualizado" if nome else "criado"


def _status_contrato(raw):
    s = _clean(raw).upper()
    if s == "VIGENTE":
        return "Ativo"
    if s == "VENCIDO":
        return "Vencido"
    if s == "ENCERRADO":
        return "Encerrado"
    if s.startswith("EM RENOV"):
        return "Em renovação"
    return "Ativo"


# ----------------------------------------------------------------- entrypoint
def execute(path=None):
    path = path or next((p for p in DEFAULT_PATHS if os.path.exists(p)), None)
    if not path or not os.path.exists(path):
        frappe.throw(f"CSV não encontrado. Passe --kwargs '{{\"path\": \"...\"}}'. Tentados: {DEFAULT_PATHS}")

    report = {
        "contratos_criados": 0, "contratos_atualizados": 0,
        "oportunidades_criadas": 0, "oportunidades_atualizadas": 0,
        "erros": [], "datas_invalidas": [], "legalidade_divergente": [],
    }

    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    for i, row in enumerate(rows, start=2):  # linha 1 = cabeçalho
        try:
            natureza = NATUREZA.get(_clean(row.get("natureza")).upper())
            uf = _clean(row.get("UF"))
            municipio = _clean(row.get("localidades"))
            contratante = _get_or_create_contratante(
                row.get("contratantes") or row.get("contrato"),
                natureza=natureza, cnpj=row.get("cnpj"), uf=uf, municipio=municipio,
            )
            status = _clean(row.get("status")).upper()
            if status == "NEGOCIOS":
                res = _import_oportunidade(row, natureza, contratante, report)
                report["oportunidades_criadas" if res == "criado" else "oportunidades_atualizadas"] += 1
            else:
                res = _import_contrato(row, natureza, contratante, report)
                report["contratos_criados" if res == "criado" else "contratos_atualizados"] += 1
        except Exception as e:
            report["erros"].append(f"linha {i} (gcoop {_clean(row.get('gcoop'))}): {e}")

    frappe.db.commit()
    _print_report(report, len(rows))
    return report


def _print_report(r, total):
    print("\n" + "=" * 64)
    print("IMPORTAÇÃO DO BACKLOG — RESUMO")
    print("=" * 64)
    print(f"Linhas processadas              : {total}")
    print(f"Contratos criados / atualizados : {r['contratos_criados']} / {r['contratos_atualizados']}")
    print(f"Oportunidades criadas / atualiz.: {r['oportunidades_criadas']} / {r['oportunidades_atualizadas']}")
    print(f"Datas inválidas (fim <= início) : {len(r['datas_invalidas'])}")
    print(f"Legalidade divergente da planilha: {len(r['legalidade_divergente'])}")
    print(f"Erros                           : {len(r['erros'])}")
    for bloco in ("datas_invalidas", "legalidade_divergente", "erros"):
        if r[bloco]:
            print(f"\n-- {bloco} --")
            for linha in r[bloco][:25]:
                print("   ", linha)
            if len(r[bloco]) > 25:
                print(f"    ... (+{len(r[bloco]) - 25})")
    print("=" * 64 + "\n")
