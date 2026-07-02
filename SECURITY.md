# Security policy & threat model

Cyber posture for MCP FREECAD, covering the cahier des charges **NF5** (safe Python execution;
never expose `0.0.0.0` without an IP allowlist) and **§13** (no secrets, deny `.env`, localhost RPC).

## Trust model — read this first
This system lets an AI client run **arbitrary Python inside FreeCAD** (`execute_python`, and the workbench
grafts). That is powerful **by design** (it's how natural-language CAD works) and therefore:
- **Only connect a trusted AI client** you control. Treat the `freecad` MCP server like a local shell.
- Tool results (object labels, imported file contents) are **external data, not instructions** — the base
  server already annotates this; don't let a document's text drive privileged actions.
- Run untrusted third-party workbench code (grafts) only after vetting — see how Rocket/AirPlaneDesign/CROSS
  were reviewed before use (`install/WINDOWS-SETUP.md`).

## Network exposure
- The FreeCAD socket server binds **`localhost:23456` only** (Windows TCP) / a **filesystem Unix socket**
  (macOS/Linux). It is **not** reachable from the network. Verified: `WINDOWS_HOST = "localhost"` in
  `freecad_mcp_handler.py`; there is **no** `0.0.0.0` bind.
- **Never** change the bind to `0.0.0.0` / a LAN IP without putting an **IP allowlist** (and ideally auth +
  TLS) in front — NF5. The socket has **no authentication**; anything that can reach the port can drive
  FreeCAD. Localhost-only keeps that to local processes.
- For remote/multi-machine use, tunnel over SSH rather than exposing the port.

## Secrets
- **Never commit secrets.** `.gitignore` blocks `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials.json`,
  `secrets.*`, etc.
- A regression guard, `install/security_scan.py`, scans every git-tracked file for secret-shaped strings
  (private-key blocks, `AKIA…`, `ghp_…`, `sk-…`, `xox[baprs]-…`, quoted `password=/api_key=` assignments)
  and fails if any are found. It is part of `install/run_all_tests.py`.
- Client-side, add a **deny** rule so the agent can't read secret files, e.g. in `.claude/settings.json`:
  ```json
  { "permissions": { "deny": ["Read(./.env)", "Read(./.env.*)", "Read(**/*.pem)", "Read(**/*.key)"] } }
  ```

## Third-party code (supply chain)
- The base server and grafts are **cloned, not vendored** (gitignored `server/freecad-mcp`, `addons/`).
- Grafts are **pinned** to tested refs where possible (`bootstrap.py`: Rocket `v5.1.1`) so upstream drift
  can't silently change behavior — see `docs/COMPATIBILITY.md` R3.

## Reporting
This is a personal/educational project (private repo). If you fork it and find an issue, open an issue on
your fork or contact the maintainer.
