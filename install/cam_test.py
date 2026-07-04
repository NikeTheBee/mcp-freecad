"""CAM / G-code test (GAP G3) — runs under freecadcmd.

Drills the holes of a plate and posts real grbl G-code, headless, on
FreeCAD 1.1. Also checks the secure-by-design output gate (extension +
clobber). Sentinel: CAM_OK
"""
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "server"))

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
from freecad_layers import cam, safe_out_path  # noqa: E402


def main() -> int:
    doc = App.newDocument("CAMTest")
    stock = doc.addObject("Part::Box", "Stock")
    stock.Length, stock.Width, stock.Height = 50, 40, 10
    hole = doc.addObject("Part::Cylinder", "H")
    hole.Radius, hole.Height = 2.5, 14
    hole.Placement.Base = App.Vector(25, 20, -2)
    part = doc.addObject("Part::Cut", "Plate")
    part.Base, part.Tool = stock, hole
    doc.recompute()

    with tempfile.TemporaryDirectory() as td:
        nc = str(Path(td) / "plate.nc")
        # single Job (a part belongs to one Job); keep the handle for reuse.
        job = cam.make_job(part)
        d = cam.drill_holes(job, part)
        assert d["holes"] >= 1 and d["commands"] > 0, d
        out = cam.post_gcode(job, nc, "grbl")
        print(cam.verdict({**d, "processor": "grbl", "gcode": out}))
        text = Path(nc).read_text(encoding="utf-8")
        assert Path(nc).stat().st_size > 0 and any(g in text for g in ("G0", "G1", "G90")), text[:200]
        print("G-code head:", text.splitlines()[0])

        # secure-by-design: refuse a non-CNC extension and silent clobber
        try:
            safe_out_path(str(Path(td) / "x.exe"), cam.GCODE_EXTS)
            print("FAIL: non-CNC extension accepted"); return 1
        except ValueError:
            print("non-CNC extension refused: OK")
        try:
            cam.post_gcode(job, nc, "grbl")            # exists, no overwrite
            print("FAIL: clobber allowed"); return 1
        except FileExistsError:
            print("clobber refused without overwrite=True: OK")
        cam.post_gcode(job, nc, "grbl", overwrite=True)  # explicit is fine

    print("CAM_OK")
    return 0


# No __main__ guard: freecadcmd executes scripts with a different __name__.
rc = main()
if rc:
    sys.exit(rc)
