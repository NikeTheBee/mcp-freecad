# MCP FREECAD

AI-piloted FreeCAD (natural language → parametric CAD/robotics), via MCP, on Windows.

## Stack
- FreeCAD 1.1.1 at `A:\FreeCAD\bin\` (`freecad.exe` GUI, `freecadcmd.exe` headless, bundled Python 3.11).
- MCP base: `blwfish/freecad-mcp` (dev branch), cloned into `/server/freecad-mcp`.
  - Bridge server: `~/.freecad-mcp/freecad_mcp_server.py`, runs under system Python 3.13 (`mcp` package installed there).
  - FreeCAD-side addon: `AICopilot` workbench installed at `%APPDATA%\FreeCAD\Mod\AICopilot`.
  - Registered with Claude Code as user-scoped MCP server `freecad` (see `claude mcp get freecad`).
  - `FREECAD_MCP_FREECAD_BIN` env var (baked into the MCP server's launch env) points at `A:\FreeCAD\bin\freecadcmd.exe` since FreeCAD isn't in a default install location.

## Key commands
- Start FreeCAD GUI: `A:\FreeCAD\bin\freecad.exe`
- Run a script headless: `A:\FreeCAD\bin\freecadcmd.exe <script.py>`
- Check MCP server health: `claude mcp list` / `claude mcp get freecad`
- Re-register server: see `/install/` notes.

## Architecture
```
User (natural language) → Claude Code → MCP `freecad` server (stdio)
   → bridge spawns/talks to FreeCAD (headless by default, GUI on request)
   → AICopilot workbench executes the operation inside FreeCAD
```

## Token-minimal golden rules
- Text-only feedback by default. No automatic screenshots — only on explicit request or an ambiguous verification failure.
- Read `/project_state/` at the start of a work session before asking the user to re-describe context (once that layer exists — Phase 4, not yet built).
- Update project state after each validated step, not before.
- Prefer the bridge's named tools over ad hoc Python execution for recurring operations.

## Anti-patterns
- Don't take screenshots by default.
- Don't re-describe the scene/history that's already recoverable from project state or the live FreeCAD document.
- Don't add greffes/domains all at once — one workbench/capability at a time, validated before the next (see `@docs/CAHIER_DES_CHARGES.md` §11).

## Pointers
- Full spec: `@docs/CAHIER_DES_CHARGES.md`
- Domain knowledge: `/skills/<domain>/SKILL.md` — load on demand. Available: `skill-rocket` (Rocketry WB graft).
- Project memory: `/project_state/` (not yet populated — Phase 4)
- Checkpoints: `/checkpoints/` (not yet populated — Phase 4)
