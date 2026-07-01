"""Mapeamento e normalização GCOOP <-> SGC (fonte única de verdade).

O GCOOP é o sistema de produção dos cooperados da COAPH e é a origem do
`codigo_gcoop` (hoje alimentado manualmente). Este módulo define:

- normalização de tipos (moeda BR, percentual BR, data);
- as tabelas de mapeamento de domínio (natureza, modalidade, especialidade);
- o **registro canônico**: um dict de chaves limpas que é a fronteira entre as
  fontes de dados (planilha CSV hoje; API/Banco do GCOOP amanhã) e o
  Contrato 360. Tanto o importador da planilha quanto o sync do GCOOP produzem
  registros canônicos e usam `to_contrato_fields`/`status_contrato_de`.

Assim, ligar o GCOOP de verdade é só fazer o client devolver registros
canônicos — nada do mapeamento/gravação muda.
"""

from frappe.utils import flt, getdate

# ----------------------------------------------------------------- domínios
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

# Chaves do registro canônico (esquema limpo, independente da origem).
CANONICAL_KEYS = (
    "gcoop", "numero_contrato", "titulo", "sigla", "cnpj", "contratante_nome",
    "municipio", "uf", "status_raw", "natureza_raw", "modalidade_raw",
    "especialidade_raw", "vigencia_inicio", "vigencia_fim", "valor_global",
    "qtd_cooperados", "taxa_adm_contratual", "taxa_adm_bruta", "impostos",
    "taxa_comercial", "legalidade_origem",
)


# ----------------------------------------------------------------- normalizadores
def norm_money(raw):
    """'R$  857.559,20' / '6.324.000,00' / 'R$ -' / '' / 1234.5 -> float | None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace("R$", "").replace(" ", "").strip()
    if s in ("", "-"):
        return None
    if s in ("0", "0,00", "0.00"):
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def norm_pct(raw):
    """'7,00%' / '7,97' / '0' / '' / 7.97 -> float | None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).replace("%", "").replace(" ", "").strip()
    if s == "":
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


import re as _re

_ISO = _re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_BR = _re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")


def norm_date(raw):
    """Datas do backlog vêm em formatos MISTOS: a maioria ISO (YYYY-MM-DD),
    mas várias em BR (dd/mm/aaaa) e uma malformada ('115-10-2026').

    - ISO: parse direto (sem ambiguidade).
    - Com barra/traço: interpreta como dia-primeiro (padrão BR); se o "mês"
      for > 12, troca dia<->mês (linha veio em m/d/aaaa).
    - Não reconhecida/malformada: None.
    """
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    m = _ISO.match(s)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
    else:
        m = _BR.match(s)
        if not m:
            return None
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        if mo > 12 and d <= 12:  # veio em m/d/aaaa -> corrige
            d, mo = mo, d
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    try:
        return getdate(f"{y:04d}-{mo:02d}-{d:02d}")
    except Exception:
        return None


def clean(s):
    return (s or "").strip() if isinstance(s, str) else (s or "")


def _map(table, raw):
    if not raw:
        return None
    return table.get(str(raw).strip().upper())


# ----------------------------------------------------------------- adaptadores
def canonical_from_planilha(row):
    """Linha do CSV d_contrato (chaves cruas da planilha) -> registro canônico."""
    return {
        "gcoop": clean(row.get("gcoop")),
        "numero_contrato": clean(row.get("numero_contrato")),
        "titulo": clean(row.get("nome_contratro_completo")),
        "sigla": clean(row.get("contrato")),
        "cnpj": clean(row.get("cnpj")),
        "contratante_nome": clean(row.get("contratantes")) or clean(row.get("contrato")),
        "municipio": clean(row.get("localidades")),
        "uf": clean(row.get("UF")),
        "status_raw": clean(row.get("status")),
        "natureza_raw": clean(row.get("natureza")),
        "modalidade_raw": clean(row.get("tipo_contrato")),
        "especialidade_raw": clean(row.get("especialidade")),
        "vigencia_inicio": row.get("data_inicio_contrato"),
        "vigencia_fim": row.get("data_fim_contrato"),
        "valor_global": row.get(" valor_inicial_contrato"),
        "qtd_cooperados": row.get("qtd_cooperados"),
        "taxa_adm_contratual": row.get("taxa_adm"),
        "taxa_adm_bruta": row.get("tx_adm_bruta"),
        "impostos": row.get("impostos"),
        "taxa_comercial": row.get("taxa_comercial"),
        "legalidade_origem": row.get("legalidade"),
    }


# ----------------------------------------------------------------- canônico -> doc
def to_contrato_fields(rec):
    """Registro canônico -> dict de campos do Contrato 360 (sem o status, que
    é tratado à parte por causa do Workflow). Retorna também o início/fim já
    validados (fim > início)."""
    ini = norm_date(rec.get("vigencia_inicio"))
    fim = norm_date(rec.get("vigencia_fim"))
    data_invalida = bool(ini and fim and fim <= ini)
    if data_invalida:
        fim = None

    natureza = NATUREZA.get(clean(rec.get("natureza_raw")).upper())
    fields = {
        "codigo_gcoop": clean(rec.get("gcoop")) or None,
        "numero_contrato": clean(rec.get("numero_contrato")) or None,
        "titulo_contrato": clean(rec.get("titulo")) or f"Contrato {clean(rec.get('gcoop'))}",
        "sigla_contrato": clean(rec.get("sigla")) or None,
        "cnpj_contratante": clean(rec.get("cnpj")) or None,
        "municipio": clean(rec.get("municipio")) or None,
        "uf": clean(rec.get("uf")) or None,
        "tipo_contrato": natureza or None,
        "modalidade_contratacao": _map(MODALIDADE, rec.get("modalidade_raw")),
        "vigencia_inicio": ini,
        "vigencia_fim": fim,
        "valor_global": norm_money(rec.get("valor_global")),
        "quantidade_cooperados_prevista": int(flt(clean(rec.get("qtd_cooperados")) or 0)),
        "taxa_admin_contratual": norm_pct(rec.get("taxa_adm_contratual")),
        "taxa_admin_bruta": norm_pct(rec.get("taxa_adm_bruta")),
        "percentual_impostos": norm_pct(rec.get("impostos")),
        "taxa_comercial": norm_pct(rec.get("taxa_comercial")),
        "especialidade_principal": _map(ESPECIALIDADE, rec.get("especialidade_raw")) or "Outro",
        "especialidades": clean(rec.get("especialidade_raw")) or None,
    }
    return fields, data_invalida


def status_contrato_de(rec):
    s = clean(rec.get("status_raw")).upper()
    if s == "VIGENTE":
        return "Ativo"
    if s == "VENCIDO":
        return "Vencido"
    if s == "ENCERRADO":
        return "Encerrado"
    if s.startswith("EM RENOV"):
        return "Em renovação"
    return "Ativo"


def eh_oportunidade(rec):
    """No backlog, 'NEGOCIOS' é pré-contrato (funil) -> Oportunidade COAPH."""
    return clean(rec.get("status_raw")).upper() == "NEGOCIOS"
