"""Bill of materials — extract a parts list from an assembly (GAP G6).

Closes the "conception -> dossier de fabrication" loop: the pince project
shipped a Nomenclature; a driven design should be able to emit one. Walks the
document's solids, groups identical parts (by label stem + volume signature),
and exports a CSV nomenclature.

Secure by design: CSV export goes through `safe_out_path` (extension enforced,
no silent clobber). Reading only otherwise — no code execution on labels.
"""
from __future__ import annotations

import csv
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from . import safe_out_path

# Objects that are structure, not parts, are skipped.
_SKIP_TYPES = ("App::Part", "App::DocumentObjectGroup", "App::Origin",
               "PartDesign::Body", "Assembly::AssemblyObject",
               "Assembly::JointGroup")


def _label_stem(label: str) -> str:
    """'Bracket001' / 'Bracket_2' -> 'Bracket' so instances group together."""
    import re
    return re.sub(r"[ _]?\d+$", "", label).strip() or label


def collect(doc, include_hidden: bool = True) -> List[Dict[str, Any]]:
    """Grouped parts list. Each row: {item, designation, qty, volume_mm3, refs}."""
    groups: "OrderedDict[tuple, Dict[str, Any]]" = OrderedDict()
    for o in doc.Objects:
        if o.TypeId in _SKIP_TYPES:
            continue
        shp = getattr(o, "Shape", None)
        if shp is None or shp.isNull() or len(shp.Solids) == 0:
            continue
        stem = _label_stem(o.Label)
        key = (stem, round(float(shp.Volume), 1))
        g = groups.get(key)
        if g is None:
            groups[key] = {"designation": stem,
                           "volume_mm3": round(float(shp.Volume), 2),
                           "qty": 1, "refs": [o.Name]}
        else:
            g["qty"] += 1
            g["refs"].append(o.Name)
    rows = []
    for i, g in enumerate(groups.values(), 1):
        rows.append({"item": i, **g})
    return rows


def export_csv(rows: List[Dict[str, Any]], path: str,
               overwrite: bool = False) -> str:
    """Write the BOM to a CSV nomenclature (secure output gate)."""
    out = safe_out_path(path, {".csv"}, overwrite=overwrite)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Designation", "Qty", "Volume_mm3", "Refs"])
        for r in rows:
            w.writerow([r["item"], r["designation"], r["qty"],
                        r["volume_mm3"], ";".join(r["refs"])])
    return str(out)


def bom_for(doc, csv_path: Optional[str] = None,
            overwrite: bool = False) -> Dict[str, Any]:
    """One call: collect the BOM and optionally export CSV. Returns a summary."""
    rows = collect(doc)
    out = export_csv(rows, csv_path, overwrite=overwrite) if csv_path else None
    return {"lines": len(rows),
            "total_parts": sum(r["qty"] for r in rows),
            "rows": rows, "csv": out}


def verdict(summary: Dict[str, Any]) -> str:
    """Token-minimal one-liner."""
    return (f"BOM: {summary['lines']} distinct part(s), "
            f"{summary['total_parts']} total"
            + (f" -> {summary['csv']}" if summary.get("csv") else ""))
