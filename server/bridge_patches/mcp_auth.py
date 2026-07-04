"""Shared-secret authentication for the FreeCAD MCP socket (NF5 hardening).

The AICopilot socket accepts `execute_python` — arbitrary code execution.
It only binds to localhost, so there is no network exposure, but WITHOUT a
token any local process (another user's process on a shared machine, a
sandboxed app with loopback access) could drive FreeCAD. This module gives
both ends a shared secret:

  - the FreeCAD-side handler REQUIRES `"auth": <token>` in every command;
  - the bridge injects it automatically;
  - the token lives in `~/.freecad-mcp/auth_token` (created on first use,
    chmod 600 on POSIX; on Windows the user-profile ACL already restricts
    it to the owner and administrators).

Deployed next to the bridge AND inside each AICopilot copy by
`install/apply_bridge_patches.py`. Both sides degrade gracefully: an
unpatched peer keeps working during an upgrade window (extra "auth" keys
are ignored by old handlers; enforcement starts once the handler is
patched and restarted).

Rotate the token by deleting the file and restarting FreeCAD + the bridge.
Disable enforcement (NOT recommended) with FREECAD_MCP_NO_AUTH=1.
"""
from __future__ import annotations

import hmac
import os
import secrets
import stat
from pathlib import Path

_TOKEN_FILE = Path.home() / ".freecad-mcp" / "auth_token"


def token_path() -> Path:
    return _TOKEN_FILE


def get_or_create_token() -> str:
    """Read the shared token, creating it (owner-only) on first use."""
    try:
        tok = _TOKEN_FILE.read_text(encoding="ascii").strip()
        if tok:
            return tok
    except FileNotFoundError:
        pass
    _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    tok = secrets.token_hex(32)
    _TOKEN_FILE.write_text(tok, encoding="ascii")
    try:  # POSIX: owner read/write only. Windows: profile ACL already scopes it.
        os.chmod(_TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return tok


def enforcement_enabled() -> bool:
    return os.environ.get("FREECAD_MCP_NO_AUTH", "0") != "1"


def check_command(command: dict) -> bool:
    """Server side: constant-time check of the 'auth' field of a command."""
    if not enforcement_enabled():
        return True
    supplied = command.get("auth")
    if not isinstance(supplied, str):
        return False
    return hmac.compare_digest(supplied, get_or_create_token())


def attach(command: dict) -> dict:
    """Client side: add the token to an outgoing command dict."""
    if enforcement_enabled():
        command["auth"] = get_or_create_token()
    return command
