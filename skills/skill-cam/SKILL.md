# skill-cam

**Load when:** the task asks for machining/CNC — toolpaths, G-code, milling, "Path/CAM job".

## Honest status on FreeCAD 1.1.x (cahier des charges §12, D5)
Scriptable CAM on 1.1.x is **not supported by this project**: the base MCP server's CAM
dispatchers (`cam_operations`, `cam_tools`, `cam_tool_controllers`) target the reworked CAM
workbench of **FreeCAD 1.2-dev**, which is not yet released (see `docs/COMPATIBILITY.md`).
Do NOT improvise Path scripting against 1.1.x — the API churn is exactly what R6/R10-class
breakage looks like.

## What to do TODAY when a user wants to fabricate
| Need | Route |
|---|---|
| 3D printing | `skill-print3d` — watertight-gated STL export, mesh repair |
| CNC at a shop / external CAM | `skill-exchange` — STEP (preferred) or IGES export; any CAM package imports it |
| Simple laser/plate work | export the face profile as DXF via `importDXF` |

Always state the limitation plainly: "G-code generation needs FreeCAD 1.2; meanwhile here is a
STEP file any CAM software can use."

## When FreeCAD 1.2 ships (upgrade playbook)
1. Follow the upgrade checklist in `docs/COMPATIBILITY.md` (env var, bootstrap, full test suite).
2. The bridge's CAM dispatchers become usable: job → tools → tool controllers → operations
   (profile, pocket, drilling, surfacing) → post-processor (grbl/linuxcnc/mach — multiple ship).
3. Replace this stub with real recipes, validated one operation at a time (§11 règle d'or).
