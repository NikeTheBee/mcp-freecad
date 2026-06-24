"""Validate the 3D-printing / STL-export path (Part B1).

Run with:  A:\FreeCAD\bin\freecadcmd.exe install\print3d_test.py

Uses only bundled FreeCAD (Part/Mesh) — no external install. Builds a solid,
gates export on the home-grown watertight check (reuse of freecad_layers.verify),
exports STL, and asserts a non-empty file. Prints PRINT3D_OK on success.
"""
import os
import sys
import tempfile

_repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_repo, "server"))

import FreeCAD
from freecad_layers import verify

doc = FreeCAD.newDocument("Print3DTest")
box = doc.addObject("Part::Box", "Box")
box.Length, box.Width, box.Height = 20, 20, 20
doc.recompute()

# Gate export on watertightness (the §7.2 rule)
assert verify.watertight("Box"), "refusing to export non-watertight shape"
print("WATERTIGHT:", verify.verdict("Box"))

out = os.path.join(tempfile.mkdtemp(prefix="mcpfc_stl_"), "box.stl")
box.Shape.exportStl(out)
size = os.path.getsize(out)
print(f"STL: {out} ({size} bytes)")
assert size > 0, "STL export produced an empty file"
print("PRINT3D_OK")
