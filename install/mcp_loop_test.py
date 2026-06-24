"""End-to-end MCP-protocol loop test (Part A2).

Drives the bridge `freecad_mcp_server.py` as a real MCP client over stdio — the
exact path an AI client uses — and proves: client -> bridge -> FreeCAD. This
demonstrates the full natural-language loop at the protocol level without needing
a fresh chat session.

Run with the Python that has the `mcp` SDK (the bridge Python):
    py -3.13 install/mcp_loop_test.py

Requires a FreeCAD MCP instance reachable by the bridge (the bridge connects to a
running headless server on localhost:23456, or spawns one). Prints MCP_LOOP_OK.
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HOME = Path.home()
SERVER = HOME / ".freecad-mcp" / "freecad_mcp_server.py"
FREECAD_BIN = os.environ.get("FREECAD_MCP_FREECAD_BIN", r"A:\FreeCAD\bin\freecadcmd.exe")


def _text(result) -> str:
    """Flatten a CallToolResult's content blocks to text."""
    parts = []
    for c in getattr(result, "content", []) or []:
        parts.append(getattr(c, "text", "") or "")
    return "\n".join(parts)


async def run() -> int:
    if not SERVER.exists():
        print(f"FAIL: bridge not found at {SERVER} (run install/bootstrap.py)")
        return 1

    env = dict(os.environ, FREECAD_MCP_FREECAD_BIN=FREECAD_BIN)
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = {t.name for t in (await session.list_tools()).tools}
            print("TOOLS:", sorted(tools)[:8], "...")
            for needed in ("view_control", "part_operations", "measurement_operations"):
                assert needed in tools, f"missing MCP tool {needed}"

            r = await session.call_tool("view_control",
                                        {"operation": "create_document", "name": "McpLoop"})
            print("create_document:", _text(r)[:120])

            r = await session.call_tool("part_operations",
                                        {"operation": "box", "length": 10, "width": 20,
                                         "height": 30, "name": "LoopBox"})
            print("box:", _text(r)[:120])

            r = await session.call_tool("measurement_operations",
                                        {"operation": "get_volume", "object_name": "LoopBox"})
            vol = _text(r)
            print("volume:", vol[:120])
            assert "6000" in vol, f"unexpected volume: {vol}"

    print("MCP_LOOP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
