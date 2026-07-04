# skill-cam

**Load when:** machining / CNC — toolpaths, G-code, drilling/milling, "Path/CAM job" (§4.5).

## Status: CAM works on FreeCAD 1.1 (gap-analysis correction)
Earlier notes said "wait for 1.2". The opposite is true: **1.1 is the right target** — Path/CAM is
scriptable **headless** here (Job + operations + post-processor), whereas **1.2 has a custom
post-processor regression** ([FreeCAD#26006](https://github.com/FreeCAD/FreeCAD/issues/26006)).
Stay on 1.1 for scripted CAM.

## Drill + post G-code in one call
```python
import sys; sys.path.insert(0, r"<repo>\server")
from freecad_layers import cam
res = cam.drill_and_post(part, r"<out>\part.nc", processor="grbl")
print(cam.verdict(res))   # OK CAM: holes=1 cmds=10 post=grbl -> ...\part.nc
```
`drill_and_post` finds every cylindrical hole on the part, drills it, and posts real G-code.

## Building blocks
| Call | Does |
|---|---|
| `make_job(part, name)` | create a CAM Job (a part belongs to ONE job) with a default tool controller |
| `drill_holes(job, part, tool_controller=None)` | Drilling op on all cylindrical faces → `{op, holes, commands}` |
| `post_gcode(job, path, processor="grbl", overwrite=False)` | post to a `.nc/.gcode/.ngc/.tap/.cnc/.g` file (refuses other extensions & silent clobber) |

Installed post-processors include `grbl`, `linuxcnc`, `mach3_4`, etc. — pass the name to `processor`.

## Limits (honest)
- Covered here: **drilling** (the most common, robust op). Profile/Pocket/MillFace ops exist
  (`Path.Op.*`) and can be added the same way — extend `cam.py`, validated one op at a time (§11).
- Always sanity-check the G-code against your machine/post before cutting metal. Simulate first.

## Verify
`install/cam_test.py` (`CAM_OK`) — drills a plate, posts grbl G-code, and checks the secure output
gate (extension + clobber refusal).
