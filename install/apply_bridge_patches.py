#!/usr/bin/env python3
"""Apply first-party patches to the deployed MCP bridge (idempotent).

The base bridge (`blwfish/freecad-mcp`) is cloned at install time and NOT
tracked by this repo, so our fixes must be re-appliable after every
bootstrap. This script:

  1. copies `server/bridge_patches/freecad_autostart.py` next to the deployed
     bridge (`~/.freecad-mcp/`), and
  2. applies anchored, exact-string patches to `freecad_mcp_server.py`
     (Windows TCP autostart — closes docs/COMPATIBILITY.md R10).

Run directly (`python install/apply_bridge_patches.py`) or via
`install/bootstrap.py`, which calls it after deploying the base.
Exit 0 = patched or already patched; exit 1 = an anchor no longer matches
(upstream changed — re-fit the patch below).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRIDGE_DIR = Path.home() / ".freecad-mcp"
MARKER = "MCP FREECAD project patch (R10)"

# (name, anchor_old, replacement_new) — replacement must contain the anchor's
# behaviour plus ours, and must be detectable via MARKER or its own text.
PATCHES = [
    (
        "P1-import",
        "from mcp_events import event_context, emit_event\n",
        """from mcp_events import event_context, emit_event

# --- MCP FREECAD project patch (R10): Windows TCP autostart ------------------
try:
    from freecad_autostart import tcp_alive as _win_tcp_alive, \\
        ensure_freecad as _win_ensure_freecad
except ImportError:  # module deployed by install/apply_bridge_patches.py
    _win_tcp_alive = None
    _win_ensure_freecad = None
# -----------------------------------------------------------------------------
""",
    ),
    (
        "P6a-auth-import",
        """except ImportError:  # module deployed by install/apply_bridge_patches.py
    _win_tcp_alive = None
    _win_ensure_freecad = None""",
        """except ImportError:  # module deployed by install/apply_bridge_patches.py
    _win_tcp_alive = None
    _win_ensure_freecad = None
try:  # NF5 patch: shared-secret auth for the FreeCAD socket
    import mcp_auth as _mcp_auth
except ImportError:
    _mcp_auth = None""",
    ),
    (
        "P6b-auth-attach",
        """            # Send command with length-prefixed protocol (v2.1.1)
            command = json.dumps({"tool": tool_name, "args": args})""",
        """            # Send command with length-prefixed protocol (v2.1.1)
            _cmd = {"tool": tool_name, "args": args}
            if _mcp_auth is not None:  # NF5 patch: attach shared-secret token
                _mcp_auth.attach(_cmd)
            command = json.dumps(_cmd)""",
    ),
    (
        "P2-honest-availability",
        """        if platform.system() == "Windows":
            return True
        if not self.socket_path:""",
        """        if platform.system() == "Windows":
            if _win_tcp_alive is not None:  # R10 patch: report the truth
                return _win_tcp_alive()
            return True
        if not self.socket_path:""",
    ),
    (
        "P3-autostart-on-refused",
        """            if platform.system() == "Windows":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', 23456))""",
        """            if platform.system() == "Windows":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect(('localhost', 23456))
                except OSError:  # R10 patch: try to start FreeCAD ourselves
                    sock.close()
                    if _win_ensure_freecad is None:
                        raise
                    _ok, _why = _win_ensure_freecad()
                    if not _ok:
                        raise ConnectionRefusedError(
                            f"FreeCAD not running and autostart failed: {_why}")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', 23456))""",
    ),
    (
        "P4-check-connection-autostarts",
        """            resolved, resolve_err = _ctx.resolve_target()
            available = _ctx.freecad_available
            status = {""",
        """            resolved, resolve_err = _ctx.resolve_target()
            available = _ctx.freecad_available
            autostart_note = None  # R10 patch: session-start check boots FreeCAD
            if (not available and platform.system() == "Windows"
                    and _win_ensure_freecad is not None):
                _ok, autostart_note = _win_ensure_freecad()
                available = _ctx.freecad_available
            status = {
                "autostart": autostart_note,""",
    ),
    (
        "P5-spawn-delegates-on-windows",
        """        elif name == "spawn_freecad_instance":
            args = arguments or {}
            label = args.get("label")""",
        """        elif name == "spawn_freecad_instance":
            args = arguments or {}
            if platform.system() == "Windows":  # R10 patch: TCP, not Unix sockets
                if _win_ensure_freecad is None:
                    return [types.TextContent(type="text", text=json.dumps({
                        "error": "spawn is Unix-socket based upstream; install "
                                 "the autostart patch (install/apply_bridge_patches.py)"}))]
                _ok, _why = _win_ensure_freecad()
                return [types.TextContent(type="text", text=json.dumps({
                    "status": "ok" if _ok else "error",
                    "detail": _why + " (Windows spawns are headless; use the GUI "
                              "app manually if a GUI is needed)",
                    "socket_path": "localhost:23456",
                }))]
            label = args.get("label")""",
    ),
]


# Patches for the FreeCAD-side handler (AICopilot/freecad_mcp_handler.py):
# require the shared token on every incoming command (NF5).
HANDLER_PATCHES = [
    (
        "HA-auth-import",
        "from typing import Dict, Any, Optional\n",
        """from typing import Dict, Any, Optional

# --- MCP FREECAD project patch (NF5): shared-secret socket auth --------------
try:
    import mcp_auth as _mcp_auth
except ImportError:  # robust fallback: load from this file's directory
    try:
        import importlib.util as _ilu
        _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_auth.py")
        _spec = _ilu.spec_from_file_location("mcp_auth", _p)
        _mcp_auth = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mcp_auth)
    except Exception:
        _mcp_auth = None
# -----------------------------------------------------------------------------
""",
    ),
    (
        "HB-auth-check",
        """            command = json.loads(command_str)
            tool_name = command.get("tool", "")""",
        """            command = json.loads(command_str)
            if _mcp_auth is not None and not _mcp_auth.check_command(command):
                return json.dumps({"error": "unauthorized: missing or invalid "
                                   "auth token (~/.freecad-mcp/auth_token; see SECURITY.md)"})
            command.pop("auth", None)
            tool_name = command.get("tool", "")""",
    ),
]


def _find_mod_aicopilot_dirs() -> list[Path]:
    """All deployed AICopilot copies FreeCAD may load (plus the bridge's)."""
    dirs = [BRIDGE_DIR / "AICopilot"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        fc = Path(appdata) / "FreeCAD"
        dirs.append(fc / "Mod" / "AICopilot")
        if fc.is_dir():
            dirs += sorted(fc.glob("v*/Mod/AICopilot"))
    else:  # POSIX
        for base in (Path.home() / ".local/share/FreeCAD",
                     Path.home() / ".FreeCAD"):
            dirs.append(base / "Mod" / "AICopilot")
            if base.is_dir():
                dirs += sorted(base.glob("v*/Mod/AICopilot"))
    return [d for d in dirs if d.is_dir()]


def _patch_file(path: Path, patches, label: str) -> tuple[bool, list]:
    text = path.read_text(encoding="utf-8")
    changed, failed = False, []
    for name, old, new in patches:
        if new in text:
            print(f"[patches] {label} {name}: already applied")
            continue
        if old not in text:
            failed.append(name)
            print(f"[patches] {label} {name}: ANCHOR NOT FOUND (upstream changed?)")
            continue
        text = text.replace(old, new, 1)
        changed = True
        print(f"[patches] {label} {name}: applied")
    if changed:
        path.write_text(text, encoding="utf-8")
        print(f"[patches] wrote {path}")
    return changed, failed


def apply(bridge_dir: Path = BRIDGE_DIR) -> int:
    server_py = bridge_dir / "freecad_mcp_server.py"
    if not server_py.is_file():
        print(f"[patches] bridge not deployed at {server_py} — nothing to patch")
        return 0

    src = REPO / "server" / "bridge_patches"
    shutil.copy2(src / "freecad_autostart.py", bridge_dir / "freecad_autostart.py")
    shutil.copy2(src / "mcp_auth.py", bridge_dir / "mcp_auth.py")
    print(f"[patches] deployed freecad_autostart.py + mcp_auth.py -> {bridge_dir}")

    failed: list = []
    _, f = _patch_file(server_py, PATCHES, "bridge")
    failed += f

    # FreeCAD-side handler: every deployed AICopilot copy gets the auth module
    # and the enforcement patch.
    for d in _find_mod_aicopilot_dirs():
        handler = d / "freecad_mcp_handler.py"
        if not handler.is_file():
            continue
        shutil.copy2(src / "mcp_auth.py", d / "mcp_auth.py")
        _, f = _patch_file(handler, HANDLER_PATCHES, f"handler[{d.parent.parent.name or d}]")
        failed += f

    if failed:
        print(f"[patches] FAILED: {', '.join(failed)} — re-fit anchors in "
              f"install/apply_bridge_patches.py against the new upstream")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(Path(sys.argv[1]) if len(sys.argv) > 1 else BRIDGE_DIR))
