# skill-techdraw

**Load when:** the task asks for 2D drawings/plans — "plan 2D", workshop drawing, dimensioned
sheet, DXF/blueprint of a part (cahier des charges §4.6; e.g. the pince project's "plan 2D pdf
par pièce").

## What this is
First-party layer `server/freecad_layers/drawing.py` over the **TechDraw** workbench (ships with
FreeCAD). Fully **headless** under freecadcmd: pages, projected views, dimensions, DXF export.

## One call for a standard sheet
```python
import sys; sys.path.insert(0, r"<repo>\server")
from freecad_layers import drawing
res = drawing.sheet_for(part, dxf_path=r"<out>\part.dxf",
                        views=("front", "top", "right"), scale=2.0)
# {'page': 'Page_Part', 'views': [...], 'dims': 4, 'dxf': '...\\part.dxf'}
print(drawing.verdict(doc.getObject(res["page"])))   # token-minimal check
```

## Building blocks
| Call | Does |
|---|---|
| `make_page(doc, template="A4_Landscape")` | page + SVG template (name fragment, anti-traversal) |
| `add_view(page, obj, "front"/"top"/"right"/"iso", scale, x, y)` | projected view (XDirection handled) |
| `add_extent_dims(view)` | overall width/height dimensions |
| `add_distance_dim(view, (x1,y1), (x2,y2), "Distance"/"DistanceX"/"DistanceY")` | point-to-point dim (unscaled 2D view coords) |
| `export_dxf(page, path, overwrite=False)` | full page → DXF (refuses clobber without overwrite) |
| `view_svg(view)` | one view's edges as SVG string (cheap text preview) |

## Honest limits
- **PDF/SVG page export is GUI-coupled** in FreeCAD 1.1 — headless deliverable is **DXF**
  (universally accepted by CAD/CAM). For a PDF: open the saved .FCStd in the GUI and print,
  or convert the DXF externally.
- Auto-dimensioning beyond overall extents (each hole, each feature) is per-feature work:
  use `add_distance_dim` with coordinates from the model.

## Verify
`install/techdraw_test.py` (sentinel `TECHDRAW_OK`) — includes the secure-by-design refusal
paths (clobber/extension/traversal).
