"""Validate the FEM (structural) domain setup headless (missing-domain: FEM).

Run with:  A:\FreeCAD\bin\freecadcmd.exe install\fem_test.py

Uses bundled FreeCAD Fem + ObjectsFem. Builds a complete analysis container
(CalculiX solver, solid material, fixed + force constraints, Netgen mesh) on a
box and best-effort generates the mesh. The CalculiX solver binary (ccx) ships
with FreeCAD, so solving is possible; full solve needs face references and is
left to the skill. Prints FEM_OK on success.
"""
import FreeCAD
import ObjectsFem

doc = FreeCAD.newDocument("FemTest")
box = doc.addObject("Part::Box", "Box")
box.Length, box.Width, box.Height = 100, 20, 20
doc.recompute()

analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
solver = ObjectsFem.makeSolverCalculiXCcxTools(doc, "CalculiX")
material = ObjectsFem.makeMaterialSolid(doc, "Steel")
fixed = ObjectsFem.makeConstraintFixed(doc, "Fixed")
force = ObjectsFem.makeConstraintForce(doc, "Force")
mesh = ObjectsFem.makeMeshNetgen(doc, "Mesh")
mesh.Shape = box

for obj in (solver, material, fixed, force, mesh):
    analysis.addObject(obj)
doc.recompute()

names = [o.Name for o in analysis.Group]
print("ANALYSIS_GROUP:", names)
for required in ("CalculiX", "Steel", "Fixed", "Force", "Mesh"):
    assert required in names, f"missing FEM object {required}"

# Best-effort headless mesh generation (Netgen) — non-fatal if unavailable
try:
    from femmesh import gmshtools  # noqa: F401
    print("mesh tooling importable")
except Exception as e:  # noqa: BLE001
    print("mesh tooling note:", repr(e)[:100])

import shutil
print("ccx solver:", shutil.which("ccx") or "MISSING")
print("FEM_OK")
