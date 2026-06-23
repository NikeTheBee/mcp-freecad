# MCP FREECAD

Design mechanical & robotics projects in FreeCAD using natural language — no manual coding — via an AI client speaking MCP.

## Prerequisites
- FreeCAD 1.1.x
- Windows (current target; see `docs/CAHIER_DES_CHARGES.md` for the broader cross-platform vision)
- Python 3.10+ for the MCP bridge server

## Install
See [`install/WINDOWS-SETUP.md`](install/WINDOWS-SETUP.md) for the exact steps performed during Phase 0 setup
(clone base server, install the `AICopilot` FreeCAD addon, register the MCP server with your AI client).

## Example
> "Create a 10×20×30mm box."

The AI calls the `freecad` MCP server's tools, FreeCAD creates the parametric box headless, and the AI reports
back the resulting volume/bounding box in plain text — no manual modeling, no screenshot needed for the happy path.

## Status
Phase 0 (install) and Phase 1 (base validation) per [`docs/CAHIER_DES_CHARGES.md`](docs/CAHIER_DES_CHARGES.md) §11.
Domain skills (robotics/ROS2, rocket, drone, CFD, FEM, CAM), the home-grown project-memory/verification/checkpoint
layers, and a finalized license are not yet in place — see the spec for the full roadmap.

## License
Not yet finalized (see open decision D2 in the spec).
