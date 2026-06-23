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

## Phase 1 validation — DONE
The full MCP→FreeCAD pipeline was validated by talking directly to the headless socket server on
`localhost:23456` with the project's own framing protocol (`install/phase1_smoke_test.py`):
create_document → create_box(10×20×30) → get_volume (6000 mm³ ✓) → get_bounding_box (✓). Compact text
feedback, no screenshots — the token-minimal behaviour the spec requires.

Note: the `freecad` MCP *tools* only load in a **fresh** Claude Code session. To validate the natural-language
path specifically, start a new session and ask for a simple part; the smoke test already proves the server
pipeline those tools call.

## Phase 2 graft #1 — Rocket Workbench (cloned, validated, NOT yet auto-loaded)
- Source: `https://github.com/davesrocketshop/Rocket` (LGPL-2.1+, v5.1.1, requires FreeCAD ≥1.0).
- Cloned (shallow) into `addons/Rocket` — **in-project, gitignored, NOT in the FreeCAD `Mod` auto-load dir**
  (per user choice: vet before auto-execution).
- Vetted: `Init.py` is clean (registers materials + `.ork`/`.rkt` import-export + a migration meta_path hook;
  no network/shell-out). Bundled FreeCAD Python already has numpy/scipy/matplotlib/shapely; only `python-docx`
  is missing (affects `.docx` report export only).
- Validated headless on-demand via `install/rocket_graft_test.py` (builds a valid body-tube solid). See
  `skills/skill-rocket/SKILL.md` for the headless invocation pattern (use `Rocket.Feature*` proxies directly;
  the `Ui/Commands/Cmd*.py` wrappers `import FreeCADGui` unconditionally and break under `freecadcmd`).
- **ACTIVATED**: installed into FreeCAD 1.1's **versioned** user Mod dir
  `%APPDATA%\FreeCAD\v1-1\Mod\Rocket` so it auto-loads. Verified: `import Rocket` resolves in
  `freecadcmd` with no manual `sys.path`, and builds valid rocketry solids.

> ⚠️ **Mod dir gotcha:** FreeCAD 1.1's user data dir is version-specific —
> `getUserAppDataDir()` = `%APPDATA%\FreeCAD\v1-1\`. Workbenches must go in
> `%APPDATA%\FreeCAD\v1-1\Mod\` to auto-load. The non-versioned `%APPDATA%\FreeCAD\Mod\`
> (where AGENT-INSTALL.md and the AICopilot step put things) is **not** auto-loaded.
> AICopilot still works only because the bridge runs its `headless_server.py` by explicit
> path (see launch.json), not via Mod auto-load.

### Re-clone the grafts (since `addons/` is gitignored)
```
git clone --depth 1 https://github.com/davesrocketshop/Rocket addons/Rocket
```
