"""Autostart (R10 fix) test — runs under system Python, no FreeCAD import.

Checks that:
  1. the deployed bridge carries all R10 patches (markers present);
  2. `freecad_autostart` resolves freecadcmd and the headless script;
  3. `ensure_freecad()` actually brings localhost:23456 up (spawning FreeCAD
     if needed) — which also self-provisions the live server for the
     phase1/mcp-loop tests that follow in run_all_tests.py.

Sentinel: AUTOSTART_OK
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRIDGE = Path.home() / ".freecad-mcp"

sys.path.insert(0, str(REPO / "server" / "bridge_patches"))
import freecad_autostart as auto  # noqa: E402


def main() -> int:
    server_py = BRIDGE / "freecad_mcp_server.py"
    if not server_py.is_file():
        print(f"FAIL: bridge not deployed at {server_py}")
        return 1
    text = server_py.read_text(encoding="utf-8")
    if sys.platform == "win32":
        needed = ["MCP FREECAD project patch (R10)", "_win_ensure_freecad",
                  "autostart_note"]
        missing = [n for n in needed if n not in text]
        if missing:
            print(f"FAIL: bridge missing patches {missing} — run "
                  f"install/apply_bridge_patches.py")
            return 1
        if not (BRIDGE / "freecad_autostart.py").is_file():
            print("FAIL: freecad_autostart.py not deployed next to the bridge")
            return 1

    fc = auto.find_freecadcmd()
    if not fc:
        print("FAIL: find_freecadcmd() found nothing")
        return 1
    print(f"freecadcmd: {fc}")

    script = auto.find_headless_script()
    if not script:
        print("FAIL: find_headless_script() found nothing")
        return 1
    print(f"headless script: {script}")

    ok, why = auto.ensure_freecad()
    print(f"ensure_freecad: ok={ok} — {why}")
    if not ok or not auto.tcp_alive():
        print("FAIL: localhost:23456 did not come up")
        return 1

    print("AUTOSTART_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
