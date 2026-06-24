# skill-fem

**Load when:** structural analysis / stress / displacement — "will this part hold", FEM, CalculiX.

## What this is
FEM via **bundled FreeCAD** (`Fem`, `ObjectsFem`) + the **CalculiX `ccx` solver that ships with FreeCAD**
(`A:\FreeCAD\bin\ccx.EXE`). No external install needed to model *or* solve.

## Build an analysis (headless / execute_python)
```python
import ObjectsFem
analysis = ObjectsFem.makeAnalysis(doc, "Analysis")
solver   = ObjectsFem.makeSolverCalculiXCcxTools(doc, "CalculiX")   # note the capital X
material = ObjectsFem.makeMaterialSolid(doc, "Steel")
fixed    = ObjectsFem.makeConstraintFixed(doc, "Fixed")
force    = ObjectsFem.makeConstraintForce(doc, "Force")
mesh     = ObjectsFem.makeMeshNetgen(doc, "Mesh"); mesh.Shape = part
for o in (solver, material, fixed, force, mesh):
    analysis.addObject(o)
doc.recompute()
```
Other factories: solvers `makeSolverElmer/Mystran/Z88`; constraints `makeConstraint{Pressure,Displacement,
Contact,...}`; meshes `makeMeshGmsh`.

## Set up the physics
- **Material:** edit `material.Material` dict (e.g. `{'YoungsModulus':'210000 MPa','PoissonRatio':'0.30','Density':'7900 kg/m^3'}`).
- **References:** assign geometry to constraints — `fixed.References = [(part, "Face1")]`,
  `force.References = [(part, "Face2")]`, `force.Force = 100.0` (N), `force.Reversed`/`Direction` as needed.
  Use `measurement_operations list_faces` (or `part.Shape.Faces`) to pick face ids.
- **Mesh:** generate before solving:
  ```python
  from femmesh.gmshtools import GmshTools
  GmshTools(mesh, analysis).create_mesh()      # or Netgen via the mesh object
  ```

## Solve with CalculiX
```python
from femtools.ccxtools import CcxTools
fea = CcxTools(solver); fea.purge_results(); fea.run()      # ccx ships with FreeCAD
# results land as a *_Results object; read fea.results / result.NodeStress, .DisplacementLengths
```
Report von Mises max / displacement max as a compact text verdict (token-minimal). Gate on a sane
mesh (node count > 0) before solving.

Runnable setup example: `install/fem_test.py`.
