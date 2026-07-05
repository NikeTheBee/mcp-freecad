"""Checkpoints / rollback — named .FCStd saves (cahier des charges §7.3).

Return to a clean state when the AI goes astray ("revert to the checkpoint
before the fins"). Each checkpoint is a named .FCStd under /checkpoints plus an
entry in the project state.
"""
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import FreeCAD  # available inside FreeCAD / freecadcmd

from . import project_dir, safe_under
from . import state as _state


def _ckpt_dir() -> Path:
    d = project_dir() / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip())
    return s or "checkpoint"


def _active(doc=None):
    doc = doc or FreeCAD.ActiveDocument
    if doc is None:
        raise ValueError("No active document to checkpoint")
    return doc


def save(name: str, note: str = "", doc=None) -> str:
    """Save the active document as checkpoints/<name>.FCStd and record it."""
    doc = _active(doc)
    fname = f"{_safe(name)}.FCStd"
    path = _ckpt_dir() / fname
    doc.saveCopy(str(path))

    try:
        fc_version = ".".join(str(p) for p in FreeCAD.Version()[:3])
    except Exception:
        fc_version = "unknown"

    s = _state.load()
    s["checkpoints"] = [c for c in s["checkpoints"] if c.get("name") != name]
    s["checkpoints"].append({
        "name": name,
        "file": fname,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "note": note,
        # .FCStd is version-tied: files saved by a newer FreeCAD may lose objects
        # when reopened in an older one (see docs/COMPATIBILITY.md). Record it.
        "freecad_version": fc_version,
    })
    _state.save(s)
    return str(path)


def list_checkpoints() -> List[Dict[str, Any]]:
    return _state.load().get("checkpoints", [])


def restore(name: str):
    """Open the named checkpoint document and return it (becomes active)."""
    entry = next((c for c in list_checkpoints() if c.get("name") == name), None)
    # `entry["file"]` comes from state.json (on-disk, tamperable): anchor it
    # under /checkpoints so a doctored state can't make us open an arbitrary
    # path (secure by design — safe_under).
    fname = entry["file"] if entry else f"{_safe(name)}.FCStd"
    path = safe_under(_ckpt_dir(), fname)
    if not path.exists():
        raise ValueError(f"Checkpoint {name!r} not found at {path}")
    return FreeCAD.openDocument(str(path))


def summary() -> str:
    cks = list_checkpoints()
    if not cks:
        return "No checkpoints."
    return "\n".join(f"- {c['name']} ({c['at']})" + (f": {c['note']}" if c.get("note") else "")
                     for c in cks)
