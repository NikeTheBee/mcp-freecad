"""Geometric verification — compact soundness verdicts (cahier des charges §7.2).

The AI validates its output is sane before continuing, getting a short text
verdict (token-efficient) rather than a screenshot. Checks: shape validity,
solidity, watertightness, plausible volume, and (best-effort) self-intersection.
"""
from typing import Any, Dict, Optional

import FreeCAD  # available inside FreeCAD / freecadcmd


def _resolve(obj_or_name, doc=None):
    if isinstance(obj_or_name, str):
        doc = doc or FreeCAD.ActiveDocument
        if doc is None:
            raise ValueError("No active document to resolve object by name")
        o = doc.getObject(obj_or_name)
        if o is None:
            raise ValueError(f"No object named {obj_or_name!r}")
        return o
    return obj_or_name


def check(obj_or_name, doc=None, min_volume: float = 1e-6) -> Dict[str, Any]:
    """Run checks on an object's shape; return a structured result dict.

    Keys: ok (bool), name, valid, solids, closed, volume, issues (list[str]).
    """
    obj = _resolve(obj_or_name, doc)
    res: Dict[str, Any] = {"name": getattr(obj, "Name", "?"), "issues": []}

    shp = getattr(obj, "Shape", None)
    if shp is None or shp.isNull():
        res.update(ok=False, valid=False, solids=0, closed=False, volume=0.0)
        res["issues"].append("no shape / null shape")
        return res

    valid = bool(shp.isValid())
    solids = len(shp.Solids)
    volume = float(shp.Volume)
    closed = bool(shp.isClosed())
    res.update(valid=valid, solids=solids, volume=volume, closed=closed)

    if not valid:
        res["issues"].append("shape.isValid() is False")
    if solids >= 1 and volume <= min_volume:
        res["issues"].append(f"degenerate volume ({volume:.3g})")
    if solids >= 1 and not closed:
        res["issues"].append("solid is not closed (not watertight)")

    # Best-effort self-intersection / topology check (BOPCheck). May be noisy or
    # unsupported on some shapes — never let it crash the verdict.
    try:
        problem = shp.check(True)  # returns None/"" when clean on most builds
        if problem:
            res["issues"].append(f"topology check: {str(problem)[:120]}")
    except Exception:
        pass

    res["ok"] = valid and not res["issues"]
    return res


def verdict(obj_or_name, doc=None) -> str:
    """One-line, token-minimal verdict string."""
    r = check(obj_or_name, doc)
    head = "OK" if r["ok"] else "FAIL"
    base = (f"{head} {r['name']}: valid={r['valid']} solids={r['solids']} "
            f"closed={r['closed']} V={r['volume']:.3g}")
    if r["issues"]:
        base += " | " + "; ".join(r["issues"])
    return base


def watertight(obj_or_name, doc=None) -> bool:
    """True if the shape is a closed solid — gate before STL export (§7.2)."""
    r = check(obj_or_name, doc)
    return r["valid"] and r["solids"] >= 1 and r["closed"]
