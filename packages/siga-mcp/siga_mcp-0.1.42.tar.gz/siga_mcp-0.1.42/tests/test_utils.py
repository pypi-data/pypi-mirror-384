import re
from typing import Any

import siga_mcp.utils as utils
from siga_mcp.utils import converter_data_siga, verificar_permissao_acesso_matricula


def test_converter_data_siga_basic_dates():
    # DD/MM/YYYY
    assert re.match(r"\d{2}/\d{2}/\d{4}$", converter_data_siga("01/02/2024"))
    # ISO
    assert re.match(r"\d{2}/\d{2}/\d{4}$", converter_data_siga("2024-02-01"))


def test_converter_data_siga_keywords():
    # hoje/ontem
    hoje = converter_data_siga("hoje")
    ontem = converter_data_siga("ontem")
    assert re.match(r"\d{2}/\d{2}/\d{4}$", hoje)
    assert re.match(r"\d{2}/\d{2}/\d{4}$", ontem)


def test_converter_data_siga_linguagem_natural():
    # fim de semana -> retorna uma data válida
    ds = converter_data_siga("fim de semana")
    assert re.match(r"\d{2}/\d{2}/\d{4}$", ds)


def test_converter_data_siga_manter_horas():
    ds = converter_data_siga("agora", manter_horas=True)
    assert re.match(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}$", ds)


def test_verificar_permissao_acesso_matricula_stdio(monkeypatch: Any) -> None:
    # Evita tocar em siga_mcp.constants; patch direto no módulo utils
    monkeypatch.setattr(utils, "MCP_TRANSPORT", "stdio", raising=False)
    monkeypatch.setattr(utils, "MATRICULA_USUARIO_ATUAL", "MINHA_MAT", raising=False)

    assert verificar_permissao_acesso_matricula("MINHA_MAT") is True
    assert verificar_permissao_acesso_matricula("OUTRA_MAT") is False


def test_verificar_permissao_acesso_matricula_http(monkeypatch: Any) -> None:
    # Em http retorna None (sem checagem local)
    monkeypatch.setattr(utils, "MCP_TRANSPORT", "http", raising=False)
    assert verificar_permissao_acesso_matricula("QUALQUER") is None
