"""CAM / G-code — scriptable toolpaths on FreeCAD 1.1 (GAP G3).

Gap analysis correction: the project previously deferred CAM to 1.2, but 1.1
is in fact the right target — Path/CAM is scriptable headless here (Job +
operations + post-processor), while 1.2 has a custom post-processor regression
(FreeCAD#26006). This layer does the basic, robust flow: create a Job on a
part, add a drilling operation on its holes, and post real G-code.

Secure by design: G-code output goes through `safe_out_path` (extension
enforced to CNC types, no silent clobber, resolved path).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import FreeCAD as App

from . import safe_out_path

GCODE_EXTS = {".nc", ".gcode", ".ngc", ".tap", ".cnc", ".g"}


def make_job(part, name: str = "Job"):
    """Create a CAM Job on `part` (a solid document object). Returns the job."""
    from Path.Main import Job as PathJob
    job = PathJob.Create(name, [part])
    part.Document.recompute()
    return job


def _hole_faces(part) -> List[str]:
    """Names of cylindrical faces (drill candidates) on the part."""
    out = []
    for i, f in enumerate(part.Shape.Faces):
        if f.Surface.TypeId == "Part::GeomCylinder":
            out.append(f"Face{i+1}")
    return out


def drill_holes(job, part, tool_controller=None) -> Dict[str, Any]:
    """Add a Drilling op targeting every cylindrical hole of `part`."""
    import Path.Op.Drilling as Drilling
    tc = tool_controller or (job.Tools.Group[0] if job.Tools.Group else None)
    if tc is None:
        raise RuntimeError("job has no tool controller")
    faces = _hole_faces(part)
    if not faces:
        raise ValueError("no cylindrical holes found on the part to drill")
    op = Drilling.Create("Drill")
    op.ToolController = tc
    op.Base = [(part, faces)]
    part.Document.recompute()
    ncmd = len(op.Path.Commands) if op.Path else 0
    return {"op": op.Name, "holes": len(faces), "commands": ncmd}


def post_gcode(job, path: str, processor: str = "grbl",
               overwrite: bool = False) -> str:
    """Post the job's toolpaths to a G-code file with the named processor.

    processor: any installed post (e.g. 'grbl', 'linuxcnc', 'mach3_4').
    """
    out = safe_out_path(path, GCODE_EXTS, overwrite=overwrite)
    from Path.Post.Processor import PostProcessorFactory
    post = PostProcessorFactory.get_post_processor(job, processor)
    res = post.export()
    gtext = res[0][1] if res and isinstance(res[0], (list, tuple)) else str(res)
    out.write_text(gtext, encoding="utf-8")
    if not (out.is_file() and out.stat().st_size > 0):
        raise RuntimeError(f"post produced no G-code at {out}")
    return str(out)


def drill_and_post(part, gcode_path: str, processor: str = "grbl",
                   overwrite: bool = False) -> Dict[str, Any]:
    """One call: Job -> drill all holes -> post G-code. Returns a summary."""
    job = make_job(part)
    d = drill_holes(job, part)
    out = post_gcode(job, gcode_path, processor, overwrite=overwrite)
    return {"job": job.Name, **d, "processor": processor, "gcode": out}


def verdict(summary: Dict[str, Any]) -> str:
    """Token-minimal one-liner for a CAM result."""
    ok = summary.get("commands", 0) > 0 and summary.get("gcode")
    return (f"{'OK' if ok else 'FAIL'} CAM: holes={summary.get('holes')} "
            f"cmds={summary.get('commands')} post={summary.get('processor')} "
            f"-> {summary.get('gcode')}")
