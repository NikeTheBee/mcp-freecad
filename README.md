# MCP FREECAD

Design mechanical, aero & robotics projects in **FreeCAD** using **natural language** — no manual coding — through any AI client that speaks **MCP**. Built for minimal token cost and long, robust design sessions.

> Describe intent ("a 450mm quad frame with foldable arms", "a 3-fin rocket with an ogive nose"); the AI models it, verifies the geometry, checkpoints progress, and prepares it for fabrication.

## How it works
```
You (natural language)
  → AI client (Claude Code / any MCP client)
    → freecad MCP server  (base: blwfish/freecad-mcp, ~32 tools)
      → FreeCAD 1.1.1  (+ domain workbench grafts)
        → home-grown layers: project memory · geometry verification · checkpoints
```
- **Token-minimal:** text-only feedback by default (no auto-screenshots), compact tool results, a
  short `CLAUDE.md` loaded each session, and heavy domain knowledge kept in on-demand **skills**.
- **Robust:** OCCT crash capture in the base, plus first-party verification + checkpoint/rollback layers.

## Prerequisites
- **FreeCAD 1.1.x** · **Python 3.10+** (for the MCP bridge) · **git** · an MCP client (e.g. Claude Code).
- Current target OS: **Windows** (uses TCP `localhost:23456`); the architecture is cross-platform — see
  [`docs/CAHIER_DES_CHARGES.md`](docs/CAHIER_DES_CHARGES.md).

## Install
Follow [`install/AGENT-INSTALL.md`](install/AGENT-INSTALL.md) (general, reproducible recipe). The as-built
log for the reference machine is [`install/WINDOWS-SETUP.md`](install/WINDOWS-SETUP.md).

## Verify
```
python install/run_all_tests.py        # graft + layer tests (Phase 1 socket test runs if :23456 is live)
```

## Example
> "Create a 10×20×30mm box."

The AI calls the `freecad` tools, FreeCAD builds the parametric box headless, and the AI reports the
volume / bounding box in plain text — no manual modeling, no screenshot on the happy path.

## Capabilities (by phase)
| Phase | Capability | Status |
|---|---|---|
| 0 | Base MCP server installed & registered | ✅ |
| 1 | Natural-language → parametric part, validated end-to-end | ✅ |
| 2 | **Rocketry** graft (Rocket WB) — nose/body/fins | ✅ auto-loading |
| 3 | **Aero** graft (AirPlaneDesign WB) — NACA airfoils, fuselage profiles | ✅ on-demand |
| 4 | **Project memory · geometric verification · checkpoints** | ✅ |
| 5 | Public publication (license, CI, polish) | in progress |
| — | Robotics/ROS2, CFD, FEM, CAM | roadmap (`docs/`) |

Domain knowledge lives in [`skills/`](skills) (`skill-rocket`, `skill-drone`, `skill-verify`), loaded
on demand to keep token cost low.

## Repository layout
- `CLAUDE.md` — short, loaded each session · `docs/` — full spec (cahier des charges)
- `server/freecad_layers/` — first-party memory/verify/checkpoint layers · `server/freecad-mcp/` — base (gitignored)
- `addons/` — third-party workbench grafts (gitignored) · `skills/` — domain knowledge
- `install/` — install guides + test suite · `project_state/`, `checkpoints/` — runtime data (gitignored)

## License
Not yet finalized (open decision; FreeCAD core and both grafted workbenches are LGPL-2.1).
