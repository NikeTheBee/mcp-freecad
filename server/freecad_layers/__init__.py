"""MCP FREECAD home-grown layers (cahier des charges §7).

Three token-efficient robustness layers, usable from the MCP server's
execute_python (inside FreeCAD) or standalone via freecadcmd:

- state      : persistent project memory (read at session start, updated per step)
- verify     : compact geometric verification verdicts
- checkpoint : named .FCStd saves + rollback

All paths resolve relative to the repo root (parent of /server), overridable
with the MCP_FREECAD_PROJECT_DIR environment variable.
"""
import os
from pathlib import Path


def project_dir() -> Path:
    """Repo root that holds /project_state and /checkpoints."""
    env = os.environ.get("MCP_FREECAD_PROJECT_DIR")
    if env:
        return Path(env)
    # server/freecad_layers/__init__.py -> repo root is two parents up
    return Path(__file__).resolve().parents[2]
