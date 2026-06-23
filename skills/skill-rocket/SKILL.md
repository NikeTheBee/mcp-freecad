# skill-rocket

**Load when:** the task involves model-rocket / fusée design — nose cones, body tubes, fins, transitions, stages, stability / centre of pressure (CP).

## What this is
The [Rocket Workbench](https://github.com/davesrocketshop/Rocket) (davesrocketshop, LGPL-2.1+, v5.1.1, requires FreeCAD ≥1.0) grafted as Phase 2 domain #1. It's a pure FreeCAD addon — no external runtime. CFD (v4.0+ workflow) optionally needs the CfdOF addon; `.docx` report export needs `python-docx` (NOT in FreeCAD's bundled Python — skip headless).

## Availability
Installed (auto-loading) in FreeCAD 1.1's **versioned** user Mod dir
`%APPDATA%\FreeCAD\v1-1\Mod\Rocket`, so `from Rocket.Feature... import ...` resolves directly in
`freecadcmd` / bridge-spawned instances — no `sys.path` tweak needed. (Source-of-truth clone is the
gitignored `addons/Rocket`; re-clone per `install/WINDOWS-SETUP.md`.)

Mod-dir gotcha: it must be the **versioned** `v1-1\Mod`, not the plain `%APPDATA%\FreeCAD\Mod` —
the latter is not auto-loaded.

## Headless invocation (the key gotcha)
The GUI command wrappers in `Ui/Commands/Cmd*.py` (`makeNoseCone`, `makeBodyTube`, …) do an **unconditional `import FreeCADGui`**, which fails under `freecadcmd`. In headless, build components directly from the `Feature*` proxy classes instead — they import only `FreeCAD`/`Part`:
```python
from Rocket.FeatureBodyTube import FeatureBodyTube
obj = doc.addObject("Part::FeaturePython", "BodyTube")
FeatureBodyTube(obj)        # attaches proxy + ViewObject hooks
obj.Proxy.setDefaults()     # required — sets default dimensions/material
doc.recompute()             # builds obj.Shape (the solid)
```
Then set parametric properties on `obj` (e.g. `obj.Diameter`, `obj.Thickness`, `obj.Length`) and `recompute()` again.

## Component → Feature class
`addObject("Part::FeaturePython", name)` + the matching class from `Rocket.Feature*`:

| Component | Class |
|---|---|
| Nose cone | `FeatureNoseCone` |
| Body tube | `FeatureBodyTube` |
| Transition | `FeatureTransition` |
| Fin / fin can | `FeatureFin` / `FeatureFinCan` |
| Inner tube / coupler / engine block | `FeatureInnerTube` / `FeatureTubeCoupler` / `FeatureEngineBlock` |
| Bulkhead / centering ring | `FeatureBulkhead` / `FeatureCenteringRing` |
| Launch lug / rail button / rail guide | `FeatureLaunchLug` / `FeatureRailButton` / `FeatureRailGuide` |
| Stage / parallel stage / pod | `FeatureStage` / `FeatureParallelStage` / `FeaturePod` |
| Whole rocket assembly | `FeatureRocket` |

## Import / export
`Init.py` registers OpenRocket (`.ork`) and Rocksim (`.rkt`) import, and `.ork` export — usable via `FreeCAD.open`/`importORK` once `addons/Rocket` is on `sys.path`.

## Verify
After building, confirm the solid is sane (token-minimal text check, no screenshot):
`obj.Shape.isValid()`, `len(obj.Shape.Solids)`, `obj.Shape.Volume`, `obj.Shape.BoundBox`.
See `install/rocket_graft_test.py` for a runnable end-to-end example.
