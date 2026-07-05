"""BOM / nomenclature test (GAP G6) — runs under freecadcmd.

Builds an assembly with repeated parts, extracts the grouped nomenclature and
exports CSV. Checks identical parts collapse into one line with the right qty,
and the secure output gate. Sentinel: BOM_OK
"""
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "server"))

import FreeCAD as App  # noqa: E402
from freecad_layers import bom, safe_out_path  # noqa: E402


def main() -> int:
    doc = App.newDocument("BOMTest")
    # 1 base + 4 identical screws (same size) + 1 lever
    base = doc.addObject("Part::Box", "Base")
    base.Length, base.Width, base.Height = 40, 40, 5
    for i in range(4):
        s = doc.addObject("Part::Cylinder", f"Screw{i+1}")
        s.Radius, s.Height = 2.5, 12
        s.Placement.Base = App.Vector(5 + i * 8, 5, 0)
    lever = doc.addObject("Part::Box", "Lever")
    lever.Length, lever.Width, lever.Height = 30, 6, 6
    # CSV-injection probe: a label that would be a formula in Excel.
    evil = doc.addObject("Part::Box", "Evil")
    evil.Label = "=HYPERLINK(evil)"
    evil.Length, evil.Width, evil.Height = 2, 2, 2
    doc.recompute()

    rows = bom.collect(doc)
    print([(r["designation"], r["qty"]) for r in rows])
    by_name = {r["designation"]: r for r in rows}
    assert by_name["Screw"]["qty"] == 4, rows        # 4 identical screws -> one line
    assert by_name["Base"]["qty"] == 1 and by_name["Lever"]["qty"] == 1, rows
    assert len(rows) == 4, rows                       # Base, Screw, Lever, Evil

    with tempfile.TemporaryDirectory() as td:
        csv_path = str(Path(td) / "nomenclature.csv")
        summary = bom.bom_for(doc, csv_path)
        print(bom.verdict(summary))
        assert summary["total_parts"] == 7, summary   # 1+4+1+1
        text = Path(csv_path).read_text(encoding="utf-8")
        assert "Designation" in text and "Screw" in text, text
        # formula neutralized: the cell must be quoted, never bare "=..."
        assert "'=HYPERLINK(evil)" in text and '\n"=HYPERLINK' not in text \
            and ",=HYPERLINK" not in text, text
        print("CSV formula injection neutralized: OK")

        # secure-by-design: wrong extension + clobber refused
        try:
            safe_out_path(str(Path(td) / "x.bat"), {".csv"})
            print("FAIL: wrong extension accepted"); return 1
        except ValueError:
            print("wrong extension refused: OK")
        try:
            bom.export_csv(summary["rows"], csv_path)   # exists, no overwrite
            print("FAIL: clobber allowed"); return 1
        except FileExistsError:
            print("clobber refused without overwrite=True: OK")

    print("BOM_OK")
    return 0


# No __main__ guard: freecadcmd executes scripts with a different __name__.
rc = main()
if rc:
    sys.exit(rc)
