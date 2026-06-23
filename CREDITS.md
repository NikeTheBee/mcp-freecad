# Credits & third-party projects

This project builds on the following open-source work. Their code is **not** vendored into this
repository (it is cloned locally at install time); it is integrated/driven at runtime. All trademarks
and copyrights belong to their respective authors.

| Project | Author(s) | License | Role here |
|---|---|---|---|
| [FreeCAD](https://www.freecad.org) | FreeCAD contributors | LGPL-2.1-or-later | CAD kernel & application being driven (v1.1.1) |
| [freecad-mcp](https://github.com/blwfish/freecad-mcp) | Brian L. Wong (blwfish) | LGPL-2.1-or-later | Base MCP server bridging an AI client to FreeCAD (~32 tools) |
| [Rocket Workbench](https://github.com/davesrocketshop/Rocket) | David Carter (davesrocketshop) | LGPL-2.1-or-later · MIT (PyAtmos) | Rocketry domain graft (nose/body/fins) |
| [AirPlaneDesign Workbench](https://github.com/FredsFactory/FreeCAD_AirPlaneDesign) | FredsFactory | LGPL-2.1 | Aero domain graft (NACA airfoils, fuselage profiles) |
| [Model Context Protocol](https://modelcontextprotocol.io) / `mcp` Python SDK | Anthropic & MCP contributors | MIT | The protocol and SDK used by the bridge |

The original design specification for this system is in [`docs/CAHIER_DES_CHARGES.md`](docs/CAHIER_DES_CHARGES.md).

If you use this project, attribution is appreciated — see [`LICENSE`](LICENSE).
