"""Robotics helpers — surface CROSS's inverse kinematics (GAP G4).

CROSS ships an IK solver (`freecad.cross.ik`, Pinocchio-backed: single/NR/
DLS/transpose/closed-form) that was installed by our graft but never exposed.
This layer makes it discoverable and callable with a clean availability
story: Pinocchio is a heavy binary dependency (conda/ROS, mostly Linux), so
callers must be able to ASK before they try.

Secure by design: this module only reads; it writes nothing. The addons path
is anchored to the repo (no caller-supplied paths are imported).
"""
from __future__ import annotations

import importlib
import sys
from typing import List, Optional, Tuple

from . import project_dir


def _ensure_cross_on_path() -> None:
    p = str(project_dir() / "addons" / "freecad.cross")
    if p not in sys.path:
        sys.path.insert(0, p)


def ik_available() -> Tuple[bool, str]:
    """Can we actually solve IK here? Returns (ok, why) — ask this FIRST."""
    _ensure_cross_on_path()
    try:
        importlib.import_module("pinocchio")
    except ImportError:
        return False, ("pinocchio not installed — IK needs the Pinocchio "
                       "binary package (conda-forge/ROS; Linux-friendly, "
                       "exotic on Windows). Geometry export (URDF) still works.")
    try:
        importlib.import_module("freecad.cross.ik")
    except ImportError as e:
        return False, f"freecad.cross.ik not importable: {e}"
    return True, "pinocchio + freecad.cross.ik available"


def solve_ik(robot, from_link: str, to_link: str, target,
             algorithm: str = "PINOCCHIO_SINGLE",
             seed: Optional[List[float]] = None,
             **tuning) -> List[List[float]]:
    """Joint values (mm/deg) bringing `to_link` to `target` (a Placement).

    Thin delegation to CROSS `ik()`; `robot` is a Cross::Robot document
    object. Raises RuntimeError with the availability reason when the solver
    stack is missing — call ik_available() first for a soft check.
    """
    ok, why = ik_available()
    if not ok:
        raise RuntimeError(f"IK unavailable: {why}")
    from freecad.cross.ik import ik, IKAlgorithm
    algo = IKAlgorithm[algorithm] if isinstance(algorithm, str) else algorithm
    return ik(robot, from_link, to_link, target,
              algorithm=algo, seed=seed, **tuning)
