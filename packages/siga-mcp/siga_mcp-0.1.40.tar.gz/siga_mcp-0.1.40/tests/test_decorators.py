import os

os.environ.setdefault("MCP_TRANSPORT", "http")

import inspect
from typing import Any, Callable, Awaitable, TypeVar, cast

import pytest  # type: ignore

from siga_mcp.decorators import resolve_matricula, tool
import siga_mcp.constants as constants

T = TypeVar("T")


class DummyServer:
    def __init__(self) -> None:
        self.registered: list[Callable[..., Awaitable[Any]]] = []

    def tool(self, f: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        # Simula o registro e retorna a própria função
        self.registered.append(f)
        return f


@pytest.mark.asyncio
async def test_resolve_matricula_replaces_current_user_when_stdio(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(constants, "MCP_TRANSPORT", "stdio", raising=False)

    @resolve_matricula
    async def fn(a: Any, b: Any) -> tuple[Any, Any]:
        return a, b

    res = await fn("x", {"m": "CURRENT_USER"})
    # Deve substituir por alguma string diferente de CURRENT_USER
    assert isinstance(res[1]["m"], str)
    assert res[1]["m"] != "CURRENT_USER"


@pytest.mark.asyncio
async def test_resolve_matricula_raises_when_not_stdio(monkeypatch: Any) -> None:
    monkeypatch.setattr(constants, "MCP_TRANSPORT", "http", raising=False)

    @resolve_matricula
    async def fn(a: Any) -> Any:
        return a

    with cast(Any, pytest).raises(ValueError):
        await fn("CURRENT_USER")


@pytest.mark.asyncio
async def test_tool_wraps_with_resolve_matricula_stdio(monkeypatch: Any) -> None:
    # Força stdio
    monkeypatch.setattr(constants, "MCP_TRANSPORT", "stdio", raising=False)

    # Cria server e um docstring module fake
    server = DummyServer()

    # Criamos um módulo docs dinâmico para a função
    import types as _types

    mod = _types.ModuleType("siga_mcp.docstrings.sample")
    cast(Any, mod).docs = lambda: "Sample docs"  # type: ignore[attr-defined]

    # Injeta no sys.modules para importlib encontrar
    import sys

    sys.modules["siga_mcp.docstrings.sample"] = mod

    @tool(cast(Any, server), transport="stdio")  # type: ignore[arg-type]
    async def sample(a: Any):
        return a

    assert callable(sample)

    # A função registrada deve ser a versão resolvida
    assert len(server.registered) == 1
    registered = server.registered[0]

    # Deve usar a docstring do docs()
    assert inspect.getdoc(registered) == "Sample docs"

    # CURRENT_USER deve ser resolvido quando executado
    res = await registered({"m": "CURRENT_USER"})
    assert isinstance(res["m"], str)
    assert res["m"] != "CURRENT_USER"


@pytest.mark.asyncio
async def test_tool_strips_current_user_in_http_and_enforces(monkeypatch: Any) -> None:
    # Força http
    monkeypatch.setattr(constants, "MCP_TRANSPORT", "http", raising=False)

    server = DummyServer()

    # criar docs para nome da função
    import types as _types

    mod = _types.ModuleType("siga_mcp.docstrings.myfunc")
    cast(Any, mod).docs = (
        lambda: """Args:\n    a (str | Literal[\"CURRENT_USER\"]): valor\n    Returns: str\n    """
    )  # type: ignore[attr-defined]

    import sys

    sys.modules["siga_mcp.docstrings.myfunc"] = mod

    @tool(cast(Any, server), transport="http")  # type: ignore[arg-type]
    async def myfunc(a: str | None = "CURRENT_USER") -> str:
        return str(a)

    assert callable(myfunc)

    assert len(server.registered) == 1
    registered = server.registered[0]

    # Assinatura não deve conter o default CURRENT_USER
    sig = inspect.signature(registered)
    params = list(sig.parameters.values())
    assert params[0].default is inspect.Signature.empty

    # Docstring não deve mencionar CURRENT_USER
    doc = inspect.getdoc(registered) or ""
    assert "CURRENT_USER" not in doc

    # Execução com CURRENT_USER deve falhar (pois MCP_TRANSPORT != stdio)
    with cast(Any, pytest).raises(ValueError):
        await registered("CURRENT_USER")
