"""TechDraw 2D drawings — pages, projected views, dimensions, export (GAP G1).

Closes the workshop-deliverable gap (cahier des charges §4.6; the pince test
required per-part 2D plans): build a dimensioned drawing page from any solid
and export it, fully headless under freecadcmd.

Headless facts (probed on FreeCAD 1.1.1):
  - pages/views/dimensions recompute fine without a GUI;
  - `TechDraw.writeDXFPage` works headless -> DXF is the native export here.
    PDF/SVG page export is GUI-coupled; for PDF, open the .FCStd in the GUI
    and print, or convert the DXF externally.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import FreeCAD as App
import TechDraw

from . import safe_out_path, safe_under

# Standard projections: view name -> (Direction, XDirection). An explicit,
# non-parallel XDirection avoids TechDraw's "failed to create projection CS"
# fallback on side views.
DIRECTIONS = {
    "front": ((0, -1, 0), (1, 0, 0)),
    "back": ((0, 1, 0), (-1, 0, 0)),
    "top": ((0, 0, 1), (1, 0, 0)),
    "bottom": ((0, 0, -1), (1, 0, 0)),
    "left": ((-1, 0, 0), (0, -1, 0)),
    "right": ((1, 0, 0), (0, 1, 0)),
    "iso": ((1, -1, 1), (0, 0, 1)),
}


def _find_template(name: str = "A4_Landscape") -> str:
    """Resolve a template NAME to an SVG inside FreeCAD's template dir.

    Secure by design: the caller's string is a name fragment, never a path —
    every candidate is re-anchored under the template dir (anti-traversal),
    so "..\\..\\evil.svg" cannot escape it.
    """
    tdir = Path(App.getResourceDir()) / "Mod" / "TechDraw" / "Templates"
    hits = (glob.glob(str(tdir / f"*{Path(name).name}*.svg"))
            or glob.glob(str(tdir / "*.svg")))
    if not hits:
        raise FileNotFoundError(f"no TechDraw SVG template under {tdir}")
    return str(safe_under(tdir, Path(hits[0]).name))


def make_page(doc, name: str = "Page", template: str = "A4_Landscape"):
    """Create a DrawPage with an SVG template. Returns the page object."""
    page = doc.addObject("TechDraw::DrawPage", name)
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", name + "Template")
    tmpl.Template = _find_template(template)
    page.Template = tmpl
    return page


def add_view(page, objects, direction: str | Tuple[float, float, float] = "front",
             scale: float = 1.0, x: float = 0.0, y: float = 0.0,
             name: str = "View"):
    """Add a projected view of `objects` (object or list) to the page."""
    doc = page.Document
    if not isinstance(objects, (list, tuple)):
        objects = [objects]
    xdir = None
    if isinstance(direction, str):
        vec, xdir = DIRECTIONS.get(direction, ((0, -1, 0), (1, 0, 0)))
    else:
        vec = direction
    view = doc.addObject("TechDraw::DrawViewPart", name)
    page.addView(view)
    view.Source = list(objects)
    view.Direction = App.Vector(*vec)
    if xdir is not None:
        view.XDirection = App.Vector(*xdir)
    view.Scale = scale
    if x or y:
        view.X, view.Y = x, y
    doc.recompute()
    return view


def add_extent_dims(view, horizontal: bool = True, vertical: bool = True) -> List:
    """Overall-size dimensions (the minimum any workshop plan needs)."""
    dims = []
    if horizontal:
        dims.append(TechDraw.makeExtentDim(view, [], 0))
    if vertical:
        dims.append(TechDraw.makeExtentDim(view, [], 1))
    view.Document.recompute()
    return dims


def add_distance_dim(view, from_pt: Tuple[float, float], to_pt: Tuple[float, float],
                     dim_type: str = "Distance"):
    """Point-to-point dimension. Points are unscaled 2D view coordinates.
    dim_type: Distance | DistanceX | DistanceY."""
    d = TechDraw.makeDistanceDim(view, dim_type,
                                 App.Vector(from_pt[0], from_pt[1], 0),
                                 App.Vector(to_pt[0], to_pt[1], 0))
    view.Document.recompute()
    return d


def export_dxf(page, path: str, overwrite: bool = False) -> str:
    """Export the full page (views + dimensions) to DXF. Headless-safe.

    Secure by design: extension enforced, resolved path, no silent clobber
    (pass overwrite=True to replace an existing file) — see safe_out_path.
    """
    out = safe_out_path(path, {".dxf"}, overwrite=overwrite)
    TechDraw.writeDXFPage(page, str(out))
    if not (out.is_file() and out.stat().st_size > 0):
        raise RuntimeError(f"DXF export produced nothing at {out}")
    return str(out)


def view_svg(view) -> str:
    """Edges of one view as an SVG fragment (quick text-friendly preview)."""
    return TechDraw.viewPartAsSvg(view)


def sheet_for(obj, dxf_path: Optional[str] = None,
              views: Sequence[str] = ("front", "top", "right"),
              scale: float = 1.0, dims: bool = True,
              overwrite: bool = False) -> Dict[str, Any]:
    """One call: standard multi-view dimensioned sheet for a part.

    Creates a page with the requested projections (sensible A4 layout),
    overall-extent dimensions on the first two views, and optionally exports
    DXF. Returns a compact summary dict (token-minimal).
    """
    doc = obj.Document
    page = make_page(doc, f"Page_{obj.Name}")
    # simple 2-column layout on A4 landscape (usable area ~270x180 mm)
    slots = [(-70, 40), (70, 40), (-70, -50), (70, -50)]
    made = []
    for i, vname in enumerate(views[:4]):
        x, y = slots[i]
        v = add_view(page, obj, vname, scale=scale, x=x, y=y,
                     name=f"{obj.Name}_{vname}")
        made.append(v)
    ndims = 0
    if dims:
        for v in made[:2]:
            ndims += len(add_extent_dims(v))
    out = None
    if dxf_path:
        out = export_dxf(page, dxf_path, overwrite=overwrite)
    return {"page": page.Name, "views": [v.Name for v in made],
            "dims": ndims, "dxf": out}


def verdict(page) -> str:
    """One-line, token-minimal page summary."""
    views = [v for v in page.Views if v.isDerivedFrom("TechDraw::DrawViewPart")]
    dims = [v for v in page.Views if v.isDerivedFrom("TechDraw::DrawViewDimension")]
    ok = bool(views) and all(len(v.Source) > 0 for v in views)
    return (f"{'OK' if ok else 'FAIL'} {page.Name}: views={len(views)} "
            f"dims={len(dims)} template={'yes' if page.Template else 'no'}")
