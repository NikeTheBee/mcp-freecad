# skill-drone

**Load when:** the task involves fixed-wing / VTOL / drone aero surfaces — airfoils (NACA), wings, fuselage/nacelle profiles. (Quadcopter *frames* — arms, motor mounts, electronics bays — are plain PartDesign; use `skill-partdesign` for those.)

## What this is
The [AirPlaneDesign workbench](https://github.com/FredsFactory/FreeCAD_AirPlaneDesign) (FredsFactory, LGPL-2.1, v0.4.1, min FreeCAD 0.18). Grafted as Phase 3 domain #2.

## Availability & headless gotchas (important)
This workbench is **GUI-only** (`InitGui.py`, no `Init.py`): the wing/rib/panel/nacelle builders all `import FreeCADGui` and won't run under `freecadcmd`. The reusable **headless** core is `libAeroShapes.py` — pure aero-coordinate math.

Cloned at `addons/AirPlaneDesign` (gitignored). It is **NOT** auto-loaded from the Mod dir (pending explicit authorization to activate). Use it on demand:
```python
import sys, types
sys.path.insert(0, r"<repo>\addons\AirPlaneDesign")   # or v1-1\Mod\AirPlaneDesign if activated
# libAeroShapes does `import DraftTools` at load (GUI-only) -> stub it; the coord
# generators are pure math and don't use it:
sys.modules.setdefault("DraftTools", types.ModuleType("DraftTools"))
import libAeroShapes
```

## Coordinate generators (all return a list of `FreeCAD.Vector`)
| Function | Shape |
|---|---|
| `getNACACoords(longueur, diametre, nbPoints=100)` | NACA-4 airfoil (upper surface) |
| `getLyonCoords(longueur, diametre, nbPoints=100)` | Lyon fuselage/nacelle profile |
| `getHoernerCoords(longueur, diametre, xRelEpaisseurMax, nbPoints=100)` | Hoerner profile |
| `getDuhamelCoords(longueur, diametre, nbPoints=100)` | Duhamel profile |

Build geometry from the points with `Part` (no Draft needed):
```python
import Part
coords = libAeroShapes.getNACACoords(longueur=200.0, diametre=30.0, nbPoints=60)
wire = Part.makePolygon(coords)        # or Part.BSplineCurve().interpolate(coords)
obj = doc.addObject("Part::Feature", "Airfoil"); obj.Shape = wire; doc.recompute()
```

## Verify
`obj.Shape.isValid()`, `len(obj.Shape.Edges)`, `obj.Shape.Length`, `obj.Shape.BoundBox`.
Runnable end-to-end example: `install/drone_graft_test.py`.
