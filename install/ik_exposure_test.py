"""IK exposure test (GAP G4) — runs under freecadcmd or system Python.

The contract under test is the EXPOSURE, not Pinocchio itself: the layer
must answer ik_available() coherently on any machine, and solve_ik must
fail soft (clear reason) when the solver stack is absent — no tracebacks,
no silent wrong answers. Sentinel: IK_EXPOSURE_OK
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "server"))

from freecad_layers import robotics  # noqa: E402


def main() -> int:
    ok, why = robotics.ik_available()
    print(f"ik_available: {ok} — {why}")
    assert isinstance(ok, bool) and isinstance(why, str) and why, (ok, why)

    if ok:
        # Full stack present: the CROSS entry points must be importable.
        from freecad.cross.ik import ik, IKAlgorithm  # noqa: F401
        print("full IK stack importable: OK")
    else:
        # Degraded mode must fail SOFT with the availability reason.
        assert "pinocchio" in why.lower() or "cross" in why.lower(), why
        try:
            robotics.solve_ik(None, "base", "tool", None)
            print("FAIL: solve_ik did not refuse without solver stack")
            return 1
        except RuntimeError as e:
            assert "IK unavailable" in str(e), e
            print("solve_ik refuses cleanly without the stack: OK")

    print("IK_EXPOSURE_OK")
    return 0


# No __main__ guard: freecadcmd executes scripts with a different __name__.
rc = main()
if rc:
    sys.exit(rc)
