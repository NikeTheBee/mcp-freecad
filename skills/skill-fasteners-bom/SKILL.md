# skill-fasteners-bom

**Load when:** standard fasteners (ISO screws/nuts/washers, threads) or a **bill of materials /
nomenclature** for an assembly (§4.1 fasteners; the pince project's M5 screws + Nomenclature).

## Bill of materials (BOM) — first-party, headless
`server/freecad_layers/bom.py` walks the document's solids, groups identical parts (label stem +
volume signature) and exports a CSV nomenclature.
```python
import sys; sys.path.insert(0, r"<repo>\server")
from freecad_layers import bom
res = bom.bom_for(doc, r"<out>\nomenclature.csv")
print(bom.verdict(res))          # BOM: 3 distinct part(s), 6 total -> ...\nomenclature.csv
# res["rows"]: [{item, designation, qty, volume_mm3, refs}, ...]
```
CSV export is gated (`.csv` only, no silent clobber). Test: `install/bom_test.py` (`BOM_OK`).

## Fasteners (standard screws/nuts/washers/threads) — on-demand graft
The **Fasteners WB** (`shaise`, pinned `v0.5.39`) is cloned by `bootstrap.py --with-grafts` into
`addons/FastenersWB` but **not auto-loaded** (kept on-demand, like AirPlaneDesign/CROSS). Its
`screw_maker` module builds ISO fasteners parametrically:
```python
import sys; sys.path.insert(0, r"<repo>\addons\FastenersWB")
from screw_maker import Screw
sm = Screw()
# e.g. an ISO 4762 socket-head cap screw M5x20 (see the WB docs for type codes)
shape = sm.createFastener("ISO4762", "M5", "20", "simple")
obj = doc.addObject("Part::Feature", "Screw_M5x20"); obj.Shape = shape; doc.recompute()
```
For quick clearance holes without the WB, `skill-assembly`'s `hole_for_shaft` fit helper is enough;
use Fasteners when you need the real screw body (visuals, BOM, interference).

## Verify
`install/bom_test.py` (`BOM_OK`). The Fasteners graft is optional; validate it after
`bootstrap.py --with-grafts` on a machine where it's cloned.
