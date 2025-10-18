# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "aiohttp>=3.12.15",
#     "dateparser>=1.2.2",
#     "fastmcp>=2.11.1",
#     "ujson>=5.10.0",
#     "rock-solid-base>=0.1.13",
#     "langfuse>=3.3.5",
# ]
# ///
import inspect
from os import getenv

from fastmcp import FastMCP
import siga_mcp._start  # pyright: ignore[reportUnusedImport]
import siga_mcp.tools
from siga_mcp.constants import DEFAULT_PORT, MCP_TRANSPORT
from siga_mcp.decorators import tool


mcp = FastMCP(
    "My MCP Server",
    instructions="Responda sempre em CAPS LOCK",
    host=getenv("HOST"),
    port=int(getenv("PORT", DEFAULT_PORT)),
)

tools = [
    func
    for _, func in inspect.getmembers(siga_mcp.tools, inspect.isfunction)
    if func.__module__ == siga_mcp.tools.__name__
]

for mcp_tool in tools:
    tool(server=mcp, transport=MCP_TRANSPORT)(mcp_tool)


def main():
    mcp.run(transport=MCP_TRANSPORT)


if __name__ == "__main__":
    main()
