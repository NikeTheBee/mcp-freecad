#!/usr/bin/env python3
"""One-command, cross-platform installer for MCP FREECAD (plug-and-play onboarding).

Removes the multi-step manual install. Detects FreeCAD, resolves the *real*
version-specific user Mod dir (fixing the v1-1 gotcha generically), installs the
base server + AICopilot workbench + bridge, registers with the detected MCP
client(s), optionally activates domain grafts, and runs the test suite.

Usage:
    python install/bootstrap.py [--with-grafts] [--client {auto,code,desktop,both,none}]
                                [--freecad-bin PATH] [--python PATH] [--dry-run]

Idempotent: safe to re-run. Requires: FreeCAD 1.1.x, git, and (for registration)
the target client installed. The AI client must speak MCP — a bare local LLM needs
an MCP-capable agent runner (out of scope).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE_REPO_URL = "https://github.com/blwfish/freecad-mcp"
# (url, autoload, ref) — pin to a tested ref so upstream master drift can't
# silently break grafts; None tracks the default branch (see docs/COMPATIBILITY.md).
GRAFTS = {
    "Rocket": ("https://github.com/davesrocketshop/Rocket", True, "v5.1.1"),
    "AirPlaneDesign": ("https://github.com/FredsFactory/FreeCAD_AirPlaneDesign", False, None),
    # CROSS robotics: dir name must be the namespace `freecad.cross` (see skill-robotics-ros).
    "freecad.cross": ("https://github.com/galou/freecad.cross", False, None),
}
HOME = Path.home()
BRIDGE_DIR = HOME / ".freecad-mcp"


def log(msg: str) -> None:
    print(f"[bootstrap] {msg}", flush=True)


def run(cmd, **kw):
    log("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, **kw)


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------
def find_freecadcmd(explicit: str | None) -> Path:
    """Locate freecadcmd: explicit arg -> env -> PATH -> common per-OS paths."""
    cands = []
    if explicit:
        cands.append(explicit)
    if os.environ.get("FREECAD_MCP_FREECAD_BIN"):
        cands.append(os.environ["FREECAD_MCP_FREECAD_BIN"])
    for name in ("freecadcmd", "FreeCADCmd", "freecad", "FreeCAD"):
        w = shutil.which(name)
        if w:
            cands.append(w)
    if sys.platform == "win32":
        cands += [r"A:\FreeCAD\bin\freecadcmd.exe",
                  r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe"]
    elif sys.platform == "darwin":
        cands.append("/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd")
    else:
        cands += ["/usr/bin/freecadcmd", "/usr/local/bin/freecadcmd"]
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    sys.exit("ERROR: FreeCAD not found. Pass --freecad-bin PATH or set "
             "FREECAD_MCP_FREECAD_BIN.")


def freecad_user_mod_dir(freecadcmd: Path) -> Path:
    """Resolve FreeCAD's REAL version-specific user Mod dir via FreeCAD itself."""
    code = "import FreeCAD;print(FreeCAD.getUserAppDataDir())"
    p = run([str(freecadcmd), "-c", code], capture_output=True, text=True, timeout=120)
    out = (p.stdout or "").strip().splitlines()
    base = next((l.strip() for l in reversed(out) if l.strip() and ("FreeCAD" in l)), "")
    if not base:
        sys.exit(f"ERROR: could not resolve FreeCAD user dir.\n{p.stdout}\n{p.stderr}")
    moddir = Path(base) / "Mod"
    moddir.mkdir(parents=True, exist_ok=True)
    return moddir


# --------------------------------------------------------------------------
# Install steps
# --------------------------------------------------------------------------
def clone_or_update(url: str, dest: Path, dry: bool, ref: str | None = None) -> None:
    if dest.exists():
        log(f"exists, skipping clone: {dest}")
        return
    if dry:
        log(f"DRY: would clone {url}{(' @' + ref) if ref else ''} -> {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1"]
    if ref:                       # pin to a tested tag/branch
        cmd += ["--branch", ref]
    cmd += [url, str(dest)]
    run(cmd, check=True)


def copy_tree(src: Path, dst: Path, dry: bool) -> None:
    log(f"copy {src} -> {dst}")
    if dry:
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))


def install_base(freecadcmd: Path, moddir: Path, dry: bool) -> None:
    base = REPO / "server" / "freecad-mcp"
    clone_or_update(BASE_REPO_URL, base, dry)
    copy_tree(base / "AICopilot", moddir / "AICopilot", dry)
    if not dry:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        for f in ("freecad_mcp_server.py", "mcp_bridge_framing.py"):
            if (base / f).exists():
                shutil.copy2(base / f, BRIDGE_DIR / f)
        # AICopilot is also needed next to the bridge for headless spawning
        copy_tree(base / "AICopilot", BRIDGE_DIR / "AICopilot", dry)
        # First-party bridge patches (Windows TCP autostart — R10); idempotent.
        sys.path.insert(0, str(REPO / "install"))
        from apply_bridge_patches import apply as _apply_patches
        if _apply_patches(BRIDGE_DIR) != 0:
            log("WARNING: bridge patches failed to apply (see above)")


def pip_install(python: Path, dry: bool) -> None:
    # Bound the MCP SDK: a breaking 2.x could desync the bridge/loop test.
    pkgs = ["mcp>=1.27.2,<2", "mcp-events>=0.1.0,<1"]
    if dry:
        log(f"DRY: would pip install {pkgs} into {python}")
        return
    run([str(python), "-m", "pip", "install", "--upgrade", *pkgs])


def install_grafts(freecadcmd: Path, moddir: Path, dry: bool) -> None:
    for name, (url, autoload, ref) in GRAFTS.items():
        dest = REPO / "addons" / name
        clone_or_update(url, dest, dry, ref=ref)
        if autoload:
            copy_tree(dest, moddir / name, dry)
            log(f"activated graft {name} (auto-load)")
        else:
            log(f"graft {name} kept on-demand (not auto-loaded)")


# --------------------------------------------------------------------------
# Client registration
# --------------------------------------------------------------------------
def register_claude_code(python: Path, freecadcmd: Path, dry: bool) -> bool:
    if not shutil.which("claude"):
        return False
    server = BRIDGE_DIR / "freecad_mcp_server.py"
    if dry:
        log("DRY: would register with Claude Code via `claude mcp add`")
        return True
    subprocess.run(["claude", "mcp", "remove", "-s", "user", "freecad"],
                   capture_output=True, text=True)
    r = run(["claude", "mcp", "add", "-s", "user", "freecad",
             "-e", f"FREECAD_MCP_FREECAD_BIN={freecadcmd}",
             "--", str(python), str(server)], capture_output=True, text=True)
    ok = r.returncode == 0
    log(("registered" if ok else "FAILED to register") + " with Claude Code")
    if not ok:
        log(r.stderr.strip()[:400])
    return ok


def claude_desktop_config_path() -> Path:
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    if sys.platform == "darwin":
        return HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return HOME / ".config" / "Claude" / "claude_desktop_config.json"


def register_claude_desktop(python: Path, freecadcmd: Path, dry: bool) -> bool:
    cfg = claude_desktop_config_path()
    if not cfg.parent.exists():
        return False  # Claude Desktop not installed
    server = BRIDGE_DIR / "freecad_mcp_server.py"
    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("mcpServers", {})["freecad"] = {
        "command": str(python),
        "args": [str(server)],
        "env": {"FREECAD_MCP_FREECAD_BIN": str(freecadcmd)},
    }
    if dry:
        log(f"DRY: would write Claude Desktop config at {cfg}")
        return True
    cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log(f"registered with Claude Desktop ({cfg})")
    return True


def create_desktop_shortcut(dry: bool) -> None:
    """Windows: drop a desktop shortcut to start-freecad-server.bat (smooth fallback)."""
    if sys.platform != "win32":
        return
    bat = REPO / "start-freecad-server.bat"
    if not bat.exists():
        return
    if dry:
        log("DRY: would create desktop shortcut 'Demarrer FreeCAD pour Claude'")
        return
    ps = (
        "$w=New-Object -ComObject WScript.Shell;"
        "$d=[Environment]::GetFolderPath('Desktop');"
        "$s=$w.CreateShortcut(\"$d\\Demarrer FreeCAD pour Claude.lnk\");"
        f"$s.TargetPath='{bat}';$s.WorkingDirectory='{REPO}';$s.Save()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=30)
        log("desktop shortcut created: 'Demarrer FreeCAD pour Claude'")
    except Exception as e:  # noqa: BLE001
        log(f"desktop shortcut skipped: {e}")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-grafts", action="store_true")
    ap.add_argument("--client", choices=["auto", "code", "desktop", "both", "none"],
                    default="auto")
    ap.add_argument("--freecad-bin")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    freecadcmd = find_freecadcmd(args.freecad_bin)
    python = Path(args.python)
    log(f"FreeCAD: {freecadcmd}")
    log(f"Bridge Python: {python}")

    moddir = freecad_user_mod_dir(freecadcmd)
    log(f"User Mod dir: {moddir}")

    install_base(freecadcmd, moddir, dry)
    pip_install(python, dry)
    if args.with_grafts:
        install_grafts(freecadcmd, moddir, dry)

    registered = []
    if args.client in ("auto", "code", "both"):
        if register_claude_code(python, freecadcmd, dry):
            registered.append("Claude Code")
    if args.client in ("desktop", "both") or (args.client == "auto" and not registered):
        if register_claude_desktop(python, freecadcmd, dry):
            registered.append("Claude Desktop")
    log(f"Registered clients: {registered or 'none (use --client)'}")

    create_desktop_shortcut(dry)

    if not dry:
        log("Running test suite...")
        run([str(python), str(REPO / "install" / "run_all_tests.py")])

    log("DONE. Open a NEW client session and ask in natural language, e.g. "
        "'create a 10x20x30mm box and give me its volume'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
