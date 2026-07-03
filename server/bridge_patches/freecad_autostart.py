"""Windows TCP autostart for the FreeCAD MCP bridge (closes COMPATIBILITY.md R10).

The upstream bridge's `spawn_freecad_instance` is Unix-socket-only, so on
Windows the user had to start FreeCAD by hand. This module lets the bridge
launch the headless AICopilot server itself whenever `localhost:23456` is not
answering, then wait for the port to come up — restoring the "zéro-code"
principle (cahier des charges §1.3).

Deployed next to `freecad_mcp_server.py` (in `~/.freecad-mcp/`) by
`install/apply_bridge_patches.py`; the patched bridge imports it lazily and
degrades gracefully when it is absent.

Env knobs:
  FREECAD_MCP_AUTOSTART=0        disable autostart entirely
  FREECAD_MCP_FREECAD_BIN=path   freecadcmd binary (already set at registration)
  FREECAD_MCP_AUTOSTART_WAIT=s   seconds to wait for the port (default 60)
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = "localhost"
PORT = 23456
_SPAWN_COOLDOWN_S = 120.0  # never spawn more than once per this window

_last_spawn_ts: float = 0.0
_proc: subprocess.Popen | None = None


def tcp_alive(timeout: float = 0.5) -> bool:
    """True if the AICopilot headless server answers on localhost:23456."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((HOST, PORT)) == 0


def find_freecadcmd() -> str | None:
    """env override -> PATH -> common Windows install paths."""
    cands = [os.environ.get("FREECAD_MCP_FREECAD_BIN"),
             shutil.which("freecadcmd"), shutil.which("FreeCADCmd"),
             r"A:\FreeCAD\bin\freecadcmd.exe",
             r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe"]
    for c in cands:
        if c and Path(c).is_file():
            return c
    return None


def find_headless_script() -> str | None:
    """Locate AICopilot/headless_server.py: next to this module, else user Mod dirs."""
    here = Path(__file__).resolve().parent
    cands = [here / "AICopilot" / "headless_server.py"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        fc = Path(appdata) / "FreeCAD"
        cands.append(fc / "Mod" / "AICopilot" / "headless_server.py")
        if fc.is_dir():  # versioned dirs (v1-1, v1-2, ...)
            cands += sorted(fc.glob("v*/Mod/AICopilot/headless_server.py"), reverse=True)
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def _log_file() -> Path:
    d = Path.home() / ".freecad-mcp" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d / "headless_autostart.log"


def ensure_freecad(wait_s: float | None = None) -> tuple[bool, str]:
    """Make sure a FreeCAD headless server is answering; spawn one if needed.

    Returns (ok, detail). Never raises. Blocking (worst case ~wait_s seconds);
    acceptable because the bridge serves a single MCP session.
    """
    global _last_spawn_ts, _proc

    if tcp_alive():
        return True, "FreeCAD already running on localhost:23456"
    if os.environ.get("FREECAD_MCP_AUTOSTART", "1") == "0":
        return False, "autostart disabled (FREECAD_MCP_AUTOSTART=0)"

    wait_s = wait_s or float(os.environ.get("FREECAD_MCP_AUTOSTART_WAIT", "60"))

    now = time.time()
    spawning = _proc is not None and _proc.poll() is None
    if not spawning and (now - _last_spawn_ts) >= _SPAWN_COOLDOWN_S:
        freecadcmd = find_freecadcmd()
        if not freecadcmd:
            return False, "freecadcmd not found (set FREECAD_MCP_FREECAD_BIN)"
        script = find_headless_script()
        if not script:
            return False, "AICopilot/headless_server.py not found (re-run install/bootstrap.py)"
        flags = 0
        if sys.platform == "win32":  # detach: survive the bridge, no console window
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        try:
            with open(_log_file(), "ab") as log:
                log.write(f"\n--- autostart {time.ctime()} ---\n".encode())
                _proc = subprocess.Popen(
                    [freecadcmd, script],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    creationflags=flags, close_fds=True,
                    cwd=str(Path(script).parent),
                )
            _last_spawn_ts = now
        except OSError as e:
            return False, f"failed to launch FreeCAD: {e}"
    elif not spawning:
        return False, (f"previous autostart attempt <{_SPAWN_COOLDOWN_S:.0f}s ago "
                       f"did not come up; see {_log_file()}")

    # Poll until the port opens (FreeCAD cold start is typically 5–30 s).
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if tcp_alive():
            return True, "FreeCAD autostarted (headless) on localhost:23456"
        if _proc is not None and _proc.poll() is not None:
            return False, (f"FreeCAD exited early (code {_proc.returncode}); "
                           f"see {_log_file()}")
        time.sleep(1.0)
    return False, f"timed out after {wait_s:.0f}s waiting for localhost:23456; see {_log_file()}"
