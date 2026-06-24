# skill-gear

**Load when:** gears, gear trains, transmissions — involute spur gears for mechanical/train designs.

## What this is
A self-contained **involute spur-gear generator** in pure `Part` — no third-party workbench, no install.
Parametric on module, teeth, width, pressure angle. Produces a valid, exportable solid.

## Use
The reusable function is `make_spur_gear(doc, module, teeth, width, pressure_angle, name)` in
`install/gear_test.py`. Import it (add `install/` to `sys.path`) or inline the algorithm:
```python
gear, tip_d = make_spur_gear(doc, module=2.0, teeth=20, width=8.0, pressure_angle=20.0)
doc.recompute()
```

## How it works (for adapting)
- Pitch r = `m·z/2`; base r = `r·cos(α)`; tip r = `r + m`; root r = `r − 1.25·m`.
- Tooth outline traced at **strictly increasing angle** (mid-gap → trailing flank rising → leading
  flank falling) so the wire never self-intersects. Flank angle at radius r is
  `half_tooth − inv(r)` where `inv(r)=√((r/r_base)²−1) − atan(√(...))` and
  `half_tooth = π/(2z) + (tan α − α)`.
- `Part.makePolygon → Face → extrude(width)`, then `removeSplitter()`/`fix()` to heal discretisation
  micro-defects → a **valid** solid (the discretised involute otherwise trips OCCT validity).

## Gear trains
Mesh two gears: centre distance = `(m·z1 + m·z2)/2`; ratio = `z2/z1`. Position the second gear with a
`Placement` (see `skill-assembly`) and rotate it half a tooth (`π/z2`) so teeth interleave.

## Verify
`verify.verdict` (valid solid), tip diameter ≈ `m·(z+2)`, width = extrude length.
Runnable example: `install/gear_test.py`.
