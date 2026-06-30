"""Cliente de acesso ao GCOOP (sistema de produção dos cooperados da COAPH).

Camada de TRANSPORTE: sabe *como* obter os dados do GCOOP. O resto do sistema
só conhece o **registro canônico** (ver mapping.py), então trocar o transporte
(arquivo -> API REST -> banco) não afeta a gravação no Contrato 360.

Modos (campo `modo` em GCOOP Settings):
  - "Arquivo"        : lê um CSV/export local (já funciona; útil para o backlog
                       inicial e para testes).
  - "API REST"       : consome a API do GCOOP. PONTO DE EXTENSÃO — implementar
                       `_listar_contratos_api` quando tivermos URL/credenciais.
  - "Banco de dados" : lê direto do banco do GCOOP. PONTO DE EXTENSÃO.

Contrato de cada método: devolve uma lista de **registros canônicos**
(dicts com as chaves de mapping.CANONICAL_KEYS).
"""

import csv

import frappe

from coaph_contract_ops.integrations.gcoop import mapping

SETTINGS = "GCOOP Settings"


class GcoopClient:
    def __init__(self, settings=None):
        self.settings = settings or frappe.get_single(SETTINGS)

    # ------------------------------------------------------------------ público
    def listar_contratos(self):
        """Registros canônicos de contratos vindos do GCOOP."""
        modo = (self.settings.get("modo") or "Arquivo").strip()
        if modo == "Arquivo":
            return self._listar_contratos_arquivo()
        if modo == "API REST":
            return self._listar_contratos_api()
        if modo == "Banco de dados":
            return self._listar_contratos_banco()
        frappe.throw(f"Modo GCOOP desconhecido: {modo}")

    def listar_producao(self, competencia=None):
        """Produção dos cooperados por competência (para o Ciclo Mensal).
        PONTO DE EXTENSÃO — depende do que o GCOOP expõe."""
        raise NotImplementedError(
            "Importação de produção do GCOOP ainda não implementada. "
            "Definir endpoint/consulta e o mapeamento para Producao/Ciclo Mensal."
        )

    # ------------------------------------------------------------- modo Arquivo
    def _listar_contratos_arquivo(self):
        path = (self.settings.get("arquivo_path") or "").strip()
        if not path:
            frappe.throw("Defina 'Caminho do arquivo' em GCOOP Settings (modo Arquivo).")
        with open(path, encoding="utf-8-sig") as fh:
            return [mapping.canonical_from_planilha(row) for row in csv.DictReader(fh)]

    # --------------------------------------------------------- modo API (stub)
    def _listar_contratos_api(self):
        """Implementar quando o GCOOP fornecer a API.

        Esperado:
          base_url = self.settings.base_url
          token    = self.settings.get_password('api_key')
          GET {base_url}/contratos  -> [ {campos do GCOOP} ]
        e converter cada item para o registro canônico (mapping.CANONICAL_KEYS),
        preenchendo ao menos 'gcoop' e os campos disponíveis. Use
        `frappe.integrations.utils.make_get_request` ou `requests`.
        """
        raise NotImplementedError(
            "Modo 'API REST' do GCOOP ainda não implementado. "
            "Forneça base_url + credencial e o formato de resposta para concluir o transporte."
        )

    # -------------------------------------------------------- modo Banco (stub)
    def _listar_contratos_banco(self):
        """Implementar quando tivermos acesso ao banco do GCOOP
        (string de conexão em base_url / credencial em api_key)."""
        raise NotImplementedError(
            "Modo 'Banco de dados' do GCOOP ainda não implementado. "
            "Forneça a conexão e o SQL/visão de origem para concluir o transporte."
        )
