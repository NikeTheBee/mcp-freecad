"""Socket-auth test (NF5 hardening) — runs under system Python.

Proves the FreeCAD-side server REJECTS unauthenticated commands and accepts
token-bearing ones. If the live server predates the auth patch (started from
an unpatched AICopilot), it is restarted via the autostart layer so the
patched handler is actually what gets tested. Sentinel: AUTH_OK
"""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path.home() / ".freecad-mcp"))
sys.path.insert(0, str(REPO / "server" / "bridge_patches"))
from mcp_bridge_framing import send_message, receive_message  # noqa: E402
import freecad_autostart as auto  # noqa: E402
import mcp_auth  # noqa: E402


def _send(payload: dict, timeout=15.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(("localhost", 23456))
    try:
        send_message(s, json.dumps(payload))
        resp = receive_message(s, timeout=timeout)
        return json.loads(resp) if resp else None
    finally:
        s.close()


def _enforcing() -> bool:
    r = _send({"tool": "test_echo", "args": {"message": "noauth-probe"}})
    return isinstance(r, dict) and "unauthorized" in str(r.get("error", ""))


def main() -> int:
    ok, why = auto.ensure_freecad()
    if not ok:
        print(f"FAIL: no FreeCAD server: {why}")
        return 1

    if not _enforcing():
        # Live server predates the handler patch — restart it (headless only).
        print("live server does not enforce auth yet -> restarting headless FreeCAD")
        subprocess.run(["taskkill", "/IM", "freecadcmd.exe", "/F"],
                       capture_output=True)
        time.sleep(2)
        ok, why = auto.ensure_freecad()
        if not ok:
            print(f"FAIL: could not restart FreeCAD: {why}")
            return 1

    # 1. No token -> must be rejected.
    r = _send({"tool": "test_echo", "args": {"message": "no-token"}})
    if not (isinstance(r, dict) and "unauthorized" in str(r.get("error", ""))):
        print(f"FAIL: unauthenticated command was ACCEPTED: {r}")
        return 1
    print("unauthenticated command rejected: OK")

    # 2. Wrong token -> rejected.
    r = _send({"tool": "test_echo", "args": {"message": "bad"}, "auth": "0" * 64})
    if not (isinstance(r, dict) and "unauthorized" in str(r.get("error", ""))):
        print(f"FAIL: wrong-token command was ACCEPTED: {r}")
        return 1
    print("wrong-token command rejected: OK")

    # 3. Correct token -> accepted (get_instance_info is a FreeCAD-side tool).
    r = _send(mcp_auth.attach({"tool": "get_instance_info", "args": {}}))
    if not (isinstance(r, dict) and "error" not in r):
        print(f"FAIL: authenticated command failed: {r}")
        return 1
    print("authenticated command accepted: OK")

    # 4. Token file exists and is non-trivial.
    tok = mcp_auth.token_path()
    if not (tok.is_file() and len(tok.read_text().strip()) >= 32):
        print(f"FAIL: token file missing/too short: {tok}")
        return 1
    print(f"token file OK: {tok}")

    print("AUTH_OK")
    return 0


# No __main__ guard needed (system python), but keep top-level pattern uniform.
rc = main()
if rc:
    sys.exit(rc)
