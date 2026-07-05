"""End-to-end test of the home-grown layers (Phase 4): state, verify, checkpoint.

Run with:  A:\FreeCAD\bin\freecadcmd.exe install\layers_test.py
Uses a temp MCP_FREECAD_PROJECT_DIR so it never touches the repo's real
project_state/ or checkpoints/. Prints LAYERS_TEST_OK on success.
"""
import os
import sys
import tempfile

_repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_repo, "server"))

# Isolate all layer I/O into a temp dir BEFORE importing the layers.
_tmp = tempfile.mkdtemp(prefix="mcpfc_layers_")
os.environ["MCP_FREECAD_PROJECT_DIR"] = _tmp

import FreeCAD
import Part
from freecad_layers import state, verify, checkpoint

# --- project memory --------------------------------------------------------
state.init_project("LayerTest", intent="validate the three home-grown layers")
state.add_constraint("max envelope 100mm")
state.set_parameter("box_len", 10)
state.record_feature("Box", "Part::Box", {"length": 10, "width": 20, "height": 30})
state.add_decision("use a simple box as the test feature")
print("STATE_SUMMARY:\n" + state.summary())
assert "Box(Part::Box)" in state.summary()

# --- geometric verification ------------------------------------------------
doc = FreeCAD.newDocument("LayerTest")
box = doc.addObject("Part::Box", "Box")
box.Length, box.Width, box.Height = 10, 20, 30
doc.recompute()

v = verify.verdict("Box")
print("VERDICT:", v)
assert verify.check("Box")["ok"] is True
assert verify.watertight("Box") is True

# a bare wire is not a watertight solid -> verification must say so
w = doc.addObject("Part::Feature", "OpenWire")
w.Shape = Part.makePolygon([FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(10, 0, 0),
                            FreeCAD.Vector(10, 10, 0)])
doc.recompute()
print("WIRE_VERDICT:", verify.verdict("OpenWire"))
assert verify.watertight("OpenWire") is False

# --- checkpoints / rollback ------------------------------------------------
path = checkpoint.save("before_changes", note="box only", doc=doc)
print("CHECKPOINT_SAVED:", os.path.basename(path))
assert os.path.exists(path)
assert any(c["name"] == "before_changes" for c in checkpoint.list_checkpoints())

restored = checkpoint.restore("before_changes")
names = [o.Name for o in restored.Objects]
print("RESTORED_OBJECTS:", names)
assert "Box" in names

# --- secure-by-design: a tampered state.json must not escape /checkpoints --
s = state.load()
s["checkpoints"].append({"name": "evil", "file": "..\\..\\outside.FCStd",
                         "at": "now", "note": ""})
state.save(s)
try:
    checkpoint.restore("evil")
    print("FAIL: traversal filename accepted")
    sys.exit(1)
except ValueError as e:
    print("tampered checkpoint path refused: OK")

print("LAYERS_TEST_OK")
