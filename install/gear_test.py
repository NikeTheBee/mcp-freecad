"""Validate a parametric involute spur-gear generator (missing-domain: train/gears).

Run with:  A:\FreeCAD\bin\freecadcmd.exe install\gear_test.py

Pure FreeCAD Part (no third-party workbench). Generates a true involute spur gear
from module/teeth/pressure-angle, extrudes to a solid, and checks tip diameter and
validity. Prints GEAR_OK on success. The generator (make_spur_gear) is documented
in skill-gear for reuse.
"""
import math

import FreeCAD
import Part
from FreeCAD import Vector


def _involute(rb, r):
    """Point on the involute of base circle rb at radius r (>= rb)."""
    r = max(r, rb)
    a = math.sqrt((r / rb) ** 2 - 1.0)      # tan(pressure angle at r)
    inv = a - math.atan(a)                  # involute roll angle
    return r, inv


def make_spur_gear(doc, module=2.0, teeth=20, width=10.0,
                   pressure_angle=20.0, name="Gear"):
    m, z = float(module), int(teeth)
    alpha = math.radians(pressure_angle)
    r_pitch = m * z / 2.0
    r_base = r_pitch * math.cos(alpha)
    r_add = r_pitch + m                      # addendum (tip)
    r_root = max(r_pitch - 1.25 * m, 0.2)    # dedendum (root)

    # half tooth angle at the base circle: half of circular tooth + involute of alpha
    half_tooth = math.pi / (2 * z) + (math.tan(alpha) - alpha)
    pitch_ang = 2 * math.pi / z
    r_lo = max(r_base, r_root)
    steps = 10

    def P(r, th):
        return Vector(r * math.cos(th), r * math.sin(th), 0)

    # Trace strictly-increasing angle around the gear: per tooth -> gap point,
    # trailing flank (rising), leading flank (falling). Monotonic => no self-cross.
    pts = []
    for i in range(z):
        C = i * pitch_ang
        pts.append(P(r_root, C - pitch_ang / 2))                # mid-gap before tooth
        for s in range(steps + 1):                              # trailing flank, base->tip
            r = r_lo + (r_add - r_lo) * s / steps
            _, inv = _involute(r_base, r)
            pts.append(P(r, C - (half_tooth - inv)))
        for s in range(steps + 1):                              # leading flank, tip->base
            r = r_add - (r_add - r_lo) * s / steps
            _, inv = _involute(r_base, r)
            pts.append(P(r, C + (half_tooth - inv)))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    solid = face.extrude(Vector(0, 0, width))
    # Heal micro-defects from the discretised involute outline so the solid is
    # valid (exportable / boolean-safe).
    solid = solid.removeSplitter()
    if not solid.isValid():
        solid.fix(1e-6, 1e-6, 1e-6)

    obj = doc.addObject("Part::Feature", name)
    obj.Shape = solid
    return obj, 2 * r_add


doc = FreeCAD.newDocument("GearTest")
gear, tip_d = make_spur_gear(doc, module=2.0, teeth=20, width=8.0)
doc.recompute()

shp = gear.Shape
bb = shp.BoundBox
print(f"VALID={shp.isValid()} SOLIDS={len(shp.Solids)} "
      f"tip_d={tip_d:.2f} bbox_d={max(bb.XLength, bb.YLength):.2f} Z={bb.ZLength:.2f}")
assert shp.isValid() and len(shp.Solids) == 1, "gear is not a valid solid"
assert abs(max(bb.XLength, bb.YLength) - tip_d) < 0.6, "tip diameter mismatch"
assert abs(bb.ZLength - 8.0) < 1e-6, "wrong gear width"
print("GEAR_OK")
