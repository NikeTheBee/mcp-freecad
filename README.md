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

## Install (one command)
```
git clone <repo> "MCP FREECAD" && cd "MCP FREECAD"
python install/bootstrap.py --with-grafts        # add --client both for Claude Code + Desktop
```
`bootstrap.py` auto-detects FreeCAD, resolves its real version-specific Mod dir, installs the base
server + workbench + bridge, registers with your MCP client(s), activates grafts, and runs the tests.
It is idempotent and cross-platform. Manual/explained steps: [`install/AGENT-INSTALL.md`](install/AGENT-INSTALL.md);
as-built reference log: [`install/WINDOWS-SETUP.md`](install/WINDOWS-SETUP.md).

> **What "plug-and-play" can and can't mean:** FreeCAD must be installed, and the AI client must speak
> **MCP** (Claude Code, Claude Desktop, any MCP client). A bare local LLM needs an MCP-capable agent
> runner. CAM needs FreeCAD 1.2-dev; CFD needs OpenFOAM; ROS2 simulation needs a ROS2 runtime.

## Verify
```
python install/run_all_tests.py    # grafts + layers + Phase 1 socket + MCP-protocol loop (if :23456 live)
```
The MCP-protocol loop test ([`install/mcp_loop_test.py`](install/mcp_loop_test.py)) drives the bridge as a
real MCP client and proves the full client→bridge→FreeCAD path end-to-end.

## Example
> "Create a 10×20×30mm box."

The AI calls the `freecad` tools, FreeCAD builds the parametric box headless, and the AI reports the
volume / bounding box in plain text — no manual modeling, no screenshot on the happy path.

## Capabilities
| Area | Capability | Status |
|---|---|---|
| Core | Parametric modeling: sketch · Pad/Pocket · spreadsheet-driven variants (loop proven) | ✅ |
| Robustness | Project memory · geometric verification · checkpoints/rollback | ✅ |
| Onboarding | One-command cross-platform installer; Claude Code + Desktop | ✅ |
| Rocketry | Rocket WB graft — nose/body/fins | ✅ |
| Aero | AirPlaneDesign graft — NACA airfoils, fuselage profiles | ✅ |
| Fabrication | STL (3D print, watertight-gated) · STEP/IGES exchange | ✅ |
| Analysis | FEM (CalculiX, ships with FreeCAD) | ✅ setup |
| Mechanism | Multi-part assemblies · involute spur gears | ✅ |
| Robotics | URDF/xacro export (CROSS graft, no ROS2 needed) | ✅ |
| CAM · CFD · Gazebo sim | G-code · OpenFOAM · ROS2 simulation | needs FreeCAD 1.2-dev / external runtimes |

Domain knowledge lives in [`skills/`](skills) — `skill-partdesign`, `skill-rocket`, `skill-drone`,
`skill-print3d`, `skill-exchange`, `skill-fem`, `skill-assembly`, `skill-gear`, `skill-robotics-ros`,
`skill-verify` — loaded on demand to keep token cost low. The full suite
(`python install/run_all_tests.py`) is **14/14**; a core subset also runs in CI
([.github/workflows/tests.yml](.github/workflows/tests.yml)).

## Repository layout
- `CLAUDE.md` — short, loaded each session · `docs/` — full spec (cahier des charges)
- `server/freecad_layers/` — first-party memory/verify/checkpoint layers · `server/freecad-mcp/` — base (gitignored)
- `addons/` — third-party workbench grafts (gitignored) · `skills/` — domain knowledge
- `install/` — install guides + test suite · `project_state/`, `checkpoints/` — runtime data (gitignored)

## License
[MIT](LICENSE) © 2026 NikeTheBee — free to use, but **attribution is required**: keep the copyright
notice and credit this project and its author. See [`CREDITS.md`](CREDITS.md) for the third-party
projects this builds on (FreeCAD and the grafted workbenches are LGPL-2.1 and are not vendored here).
