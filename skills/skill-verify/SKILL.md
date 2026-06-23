# skill-verify

**Load when:** you need to confirm produced geometry is sound before continuing, gate an STL export, save a checkpoint, or read/update project memory. These are the home-grown robustness layers (cahier des charges §7).

## Availability
Python package at `server/freecad_layers/` (tracked, first-party). Import it inside FreeCAD / the MCP server's `execute_python`:
```python
import sys; sys.path.insert(0, r"<repo>\server")
from freecad_layers import state, verify, checkpoint
```
All three resolve paths to `<repo>/project_state` and `<repo>/checkpoints` (override with the `MCP_FREECAD_PROJECT_DIR` env var).

## verify — compact soundness verdicts (§7.2)
Text-only, token-minimal — no screenshots on the happy path.
```python
verify.verdict("Box")   # -> "OK Box: valid=True solids=1 closed=True V=6e+03"
verify.check("Box")     # -> dict: ok, valid, solids, closed, volume, issues[]
verify.watertight("Box")  # -> bool; GATE THIS before any STL export
```
Flags: invalid shape, degenerate volume, non-closed solid, and best-effort topology/self-intersection (`Shape.check`). Run after each feature you intend to keep.

## state — project memory (§7.1)
Read at session start; update **after each validated step** (never before).
```python
print(state.summary())                       # compact digest to read at session start
state.init_project("quad450", intent="...")  # once, at project creation
state.record_feature("Arm", "Part::Box", {"length": 200})  # after a validated step
state.set_parameter("wheelbase", 450); state.add_constraint("foldable arms")
state.add_decision("450mm wheelbase chosen for 10in props")
```
Backed by a single diff-friendly `project_state/state.json`.

## checkpoint — named saves + rollback (§7.3)
Save before risky/large operations; roll back when a path goes wrong.
```python
checkpoint.save("before_fins", note="clean body+nose", doc=FreeCAD.ActiveDocument)
checkpoint.list_checkpoints()       # [{name, file, at, note}, ...]
checkpoint.restore("before_fins")   # opens that .FCStd, returns the document
```
Saves a named `.FCStd` under `checkpoints/` and records it in the project state.

## Standard loop (token-minimal)
1. `state.summary()` at session start. 2. build a feature. 3. `verify.verdict(obj)` — if it FAILs, fix before continuing (screenshot only on ambiguous failure). 4. `state.record_feature(...)`. 5. `checkpoint.save(...)` before the next risky step.

Runnable example covering all three: `install/layers_test.py`.
