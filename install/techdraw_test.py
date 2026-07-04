"""TechDraw 2D drawing test (GAP G1) — runs under freecadcmd.

Builds a dimensioned multi-view sheet for a part via freecad_layers.drawing
and exports DXF headless. Also exercises the secure-by-design refusal paths
(template traversal, silent clobber, wrong extension). Sentinel: TECHDRAW_OK
"""
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "server"))

import FreeCAD as App  # noqa: E402
from freecad_layers import drawing, safe_out_path  # noqa: E402


def main() -> int:
    doc = App.newDocument("TDTest")
    b = doc.addObject("Part::Box", "Bracket")
    b.Length, b.Width, b.Height = 40, 20, 10
    doc.recompute()

    with tempfile.TemporaryDirectory() as td:
        dxf = os.path.join(td, "bracket.dxf")
        res = drawing.sheet_for(b, dxf_path=dxf,
                                views=("front", "top", "right"), scale=2.0)
        print(res)
        assert len(res["views"]) == 3, res
        assert res["dims"] >= 4, res            # 2 extent dims on 2 views
        assert Path(dxf).stat().st_size > 1000, "DXF suspiciously small"

        page = doc.getObject(res["page"])
        v = drawing.verdict(page)
        print(v)
        assert v.startswith("OK"), v

        # point-to-point dimension API
        view = doc.getObject(res["views"][0])
        d = drawing.add_distance_dim(view, (0, 0), (40, 0), "DistanceX")
        assert d is not None

        # --- secure-by-design refusal paths ---
        try:
            drawing.export_dxf(page, dxf)       # exists, no overwrite flag
            print("FAIL: clobber was allowed")
            return 1
        except FileExistsError:
            print("clobber refused without overwrite=True: OK")
        drawing.export_dxf(page, dxf, overwrite=True)   # explicit is fine
        try:
            safe_out_path(os.path.join(td, "evil.dll"), {".dxf"})
            print("FAIL: wrong extension accepted")
            return 1
        except ValueError:
            print("wrong extension refused: OK")
        try:
            from freecad_layers import safe_under
            safe_under(Path(td), "..\\..\\evil.svg")
            print("FAIL: traversal accepted")
            return 1
        except ValueError:
            print("path traversal refused: OK")

        # per-view SVG fragment (text-friendly preview)
        svg = drawing.view_svg(view)
        assert svg.strip().startswith("<") and len(svg) > 50

    print("TECHDRAW_OK")
    return 0


# No __main__ guard: freecadcmd executes scripts with a different __name__.
rc = main()
if rc:
    sys.exit(rc)
