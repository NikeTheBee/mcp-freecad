"""Validate STEP / IGES exchange export (missing-domain: CAD interchange).

Run with:  A:\FreeCAD\bin\freecadcmd.exe install\exchange_test.py
Bundled FreeCAD only. Prints EXCHANGE_OK on success.
"""
import os
import sys
import tempfile

import FreeCAD
import Import

doc = FreeCAD.newDocument("ExchangeTest")
box = doc.addObject("Part::Box", "Box")
box.Length, box.Width, box.Height = 15, 25, 35
doc.recompute()

d = tempfile.mkdtemp(prefix="mcpfc_exch_")
step = os.path.join(d, "part.step")
iges = os.path.join(d, "part.iges")

box.Shape.exportStep(step)
Import.export([box], iges)   # extension-driven (.iges)

for path in (step, iges):
    size = os.path.getsize(path)
    print(f"{os.path.basename(path)}: {size} bytes")
    assert size > 0, f"empty export: {path}"

# round-trip: re-import the STEP and confirm a solid comes back
rt = FreeCAD.newDocument("ExchangeRT")
Import.insert(step, "ExchangeRT")
rt.recompute()
solids = sum(len(o.Shape.Solids) for o in rt.Objects if hasattr(o, "Shape"))
print("reimported solids:", solids)
assert solids >= 1, "STEP round-trip lost the solid"
print("EXCHANGE_OK")
