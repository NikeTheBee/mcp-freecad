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


def apply(bridge_dir: Path = BRIDGE_DIR) -> int:
    server_py = bridge_dir / "freecad_mcp_server.py"
    if not server_py.is_file():
        print(f"[patches] bridge not deployed at {server_py} — nothing to patch")
        return 0

    module_src = REPO / "server" / "bridge_patches" / "freecad_autostart.py"
    shutil.copy2(module_src, bridge_dir / "freecad_autostart.py")
    print(f"[patches] deployed freecad_autostart.py -> {bridge_dir}")

    text = server_py.read_text(encoding="utf-8")
    changed = False
    failed = []
    for name, old, new in PATCHES:
        if new in text:
            print(f"[patches] {name}: already applied")
            continue
        if old not in text:
            failed.append(name)
            print(f"[patches] {name}: ANCHOR NOT FOUND (upstream changed?)")
            continue
        text = text.replace(old, new, 1)
        changed = True
        print(f"[patches] {name}: applied")

    if changed:
        server_py.write_text(text, encoding="utf-8")
        print(f"[patches] wrote {server_py}")
    if failed:
        print(f"[patches] FAILED: {', '.join(failed)} — re-fit anchors in "
              f"install/apply_bridge_patches.py against the new upstream")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(Path(sys.argv[1]) if len(sys.argv) > 1 else BRIDGE_DIR))
