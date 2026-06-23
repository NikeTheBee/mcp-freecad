# Windows install notes (Phase 0)

Done on this machine:

1. Cloned `https://github.com/blwfish/freecad-mcp` (dev branch) into `/server/freecad-mcp`.
2. Copied `server/freecad-mcp/AICopilot` → `%APPDATA%\FreeCAD\Mod\AICopilot`.
3. Copied `server/freecad-mcp/freecad_mcp_server.py` and `mcp_bridge_framing.py` → `%USERPROFILE%\.freecad-mcp\`.
4. Installed the bridge's Python deps under system Python 3.13:
   `py -3.13 -m pip install "mcp>=1.27.2" "mcp-events>=0.1.0"`
5. Registered the server with Claude Code (user scope, so it's available in every project), with an explicit
   override for the non-default FreeCAD install path:
   ```
   claude mcp add -s user freecad -e FREECAD_MCP_FREECAD_BIN="A:\FreeCAD\bin\freecadcmd.exe" -- \
     "C:\Users\Administrateur\AppData\Local\Programs\Python\Python313\python.exe" \
     "C:\Users\Administrateur\.freecad-mcp\freecad_mcp_server.py"
   ```
6. Verified with `claude mcp get freecad` → status `Connected`.
7. Verified FreeCAD itself headless (`freecadcmd.exe`) creates and recomputes geometry correctly
   (FreeCAD 1.1.1 confirmed, box volume check passed).

## Notes / gotchas
- `claude mcp add`'s `-e` flag is variadic and will swallow following positional args if placed before
  `<name>`. Put it after the server name and before `--`, e.g. `claude mcp add -s user <name> -e KEY=val -- <cmd> <args>`.
- The bridge server runs under a normal Python (≥3.10, needs the `mcp` package) — it is *not* run with
  FreeCAD's bundled interpreter. The `AICopilot` workbench, by contrast, runs inside FreeCAD's own bundled
  Python automatically once installed as an addon.
- FreeCAD isn't on a standard path on this machine (`A:\FreeCAD\bin\`), hence the explicit
  `FREECAD_MCP_FREECAD_BIN` override — without it the bridge's auto-discovery (`_find_freecadcmd` in
  `freecad_mcp_server.py`) would fail.
- On Windows the bridge uses a TCP socket (`localhost:23456` by default, override via `FREECAD_MCP_PORT`)
  instead of the Unix domain socket used on macOS/Linux. The maintainer flags Windows as less-tested than macOS.
- Newly registered MCP servers only become available as callable tools in a *new* Claude Code session —
  restart the session before trying to drive FreeCAD through natural language.

## Next step (Phase 1 validation, requires a fresh session)
Start a new Claude Code session in this project, then ask it to create a simple parametric part
(e.g. a box) purely through the `freecad` MCP tools, and confirm the result via a measurement/bounding-box
tool rather than a screenshot.
