"""Run all MCP FREECAD verification tests and report (Phase 5 reproducibility).

Usage (system Python):  py -3.13 install/run_all_tests.py

- The graft/layer tests run standalone under freecadcmd.
- The Phase 1 smoke test needs the headless MCP socket server live on
  localhost:23456; it is run only if that port is open, otherwise skipped.

Exit code 0 iff every test that ran passed.
"""
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def resolve_freecadcmd() -> str:
    """env override -> PATH -> known fallback. Survives a FreeCAD path change."""
    return (os.environ.get("FREECAD_MCP_FREECAD_BIN")
            or shutil.which("freecadcmd") or shutil.which("FreeCADCmd")
            or r"A:\FreeCAD\bin\freecadcmd.exe")


FREECADCMD = resolve_freecadcmd()

# (script, success sentinel) — run under freecadcmd
# Graft tests need the third-party workbench clones under addons/. Set
# MCPFC_SKIP_GRAFTS=1 (e.g. in CI with only bundled FreeCAD) to skip them.
GRAFT_TESTS = [
    ("rocket_graft_test.py", "ROCKET_GRAFT_OK"),
    ("drone_graft_test.py", "DRONE_GRAFT_OK"),
    ("robotics_urdf_test.py", "ROBOTICS_URDF_OK"),
]
CORE_TESTS = [
    ("partdesign_test.py", "PARTDESIGN_OK"),
    ("partdesign_dressup_test.py", "DRESSUP_OK"),
    ("spreadsheet_variants_test.py", "SPREADSHEET_OK"),
    ("tolerances_test.py", "TOLERANCES_OK"),
    ("mesh_repair_test.py", "MESH_REPAIR_OK"),
    ("urdf_package_test.py", "URDF_PACKAGE_OK"),
    ("layers_test.py", "LAYERS_TEST_OK"),
    ("print3d_test.py", "PRINT3D_OK"),
    ("exchange_test.py", "EXCHANGE_OK"),
    ("fem_test.py", "FEM_OK"),
    ("memory_recovery_test.py", "MEMORY_RECOVERY_OK"),
    ("assembly_test.py", "ASSEMBLY_OK"),
    ("gear_test.py", "GEAR_OK"),
]
FREECAD_TESTS = (CORE_TESTS if os.environ.get("MCPFC_SKIP_GRAFTS")
                 else GRAFT_TESTS + CORE_TESTS)


def _port_open(host="localhost", port=23456) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _run(cmd) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return p.returncode == 0, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001
        return False, f"<runner error: {e}>"


def main() -> int:
    results = []

    if not Path(FREECADCMD).exists():
        print(f"!! freecadcmd not found at {FREECADCMD} "
              f"(set FREECAD_MCP_FREECAD_BIN)")
        return 2

    for script, sentinel in FREECAD_TESTS:
        ok, out = _run([FREECADCMD, str(HERE / script)])
        passed = ok and sentinel in out
        results.append((script, passed))
        print(f"[{'PASS' if passed else 'FAIL'}] {script}")
        if not passed:
            print("    " + out.strip().replace("\n", "\n    ")[:800])

    # Phase 1 smoke test needs the live socket server
    if _port_open():
        ok, out = _run([sys.executable, str(HERE / "phase1_smoke_test.py")])
        passed = ok and '"result"' in out and "6000" in out
        results.append(("phase1_smoke_test.py", passed))
        print(f"[{'PASS' if passed else 'FAIL'}] phase1_smoke_test.py")
        if not passed:
            print("    " + out.strip().replace("\n", "\n    ")[:800])
    else:
        print("[SKIP] phase1_smoke_test.py (no server on localhost:23456 — "
              "start the 'freecad-headless' server first)")

    # MCP-protocol loop test needs the `mcp` SDK + a reachable FreeCAD instance
    have_mcp = subprocess.run([sys.executable, "-c", "import mcp"],
                              capture_output=True).returncode == 0
    if have_mcp and _port_open():
        ok, out = _run([sys.executable, str(HERE / "mcp_loop_test.py")])
        passed = ok and "MCP_LOOP_OK" in out
        results.append(("mcp_loop_test.py", passed))
        print(f"[{'PASS' if passed else 'FAIL'}] mcp_loop_test.py")
        if not passed:
            print("    " + out.strip().replace("\n", "\n    ")[:800])
    else:
        print("[SKIP] mcp_loop_test.py (needs the `mcp` SDK and a server on :23456)")

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed"
          + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
