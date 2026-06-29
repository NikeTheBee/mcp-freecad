# FreeCAD compatibility audit

Audit of version-/update-compatibility risks for this project and the mitigations applied.
Target: **FreeCAD 1.1.1** (current stable, released 2026-03-25). Last reviewed: 2026-06.

## Version landscape (fact-checked)
- **1.1.x** — current stable. This project targets it. Python **3.11** bundled; OpenCASCADE 7.x.
- **1.2.0-dev** — in active development, **not yet released**. Brings two upstream breaks:
  - **OpenCASCADE 7.9 → 8.0** (LibPack 3.5.0): OCCT 8.0 *removes/deprecates a number of public APIs*.
    Geometry-kernel behaviour (validity, healing, boolean tolerances) can shift.
  - **Python 3.11 → 3.13** likely (was 3.13, reverted to 3.11 to match Blender; Blender has since moved
    to 3.13).
- `.FCStd` **forward-incompatibility**: files saved by a newer FreeCAD can **lose objects** (e.g. datum
  planes) when reopened in an older one ([FreeCAD#27447](https://github.com/freecad/freecad/issues/27447)).

## Risk register

| # | Risk | Impact | Status / mitigation |
|---|---|---|---|
| R1 | Hard-coded `A:\FreeCAD\bin\freecadcmd.exe` in runners | tests break if FreeCAD moves/updates | **Fixed** — resolve via `FREECAD_MCP_FREECAD_BIN` → `shutil.which` → fallback (`run_all_tests.py`, `memory_recovery_test.py`, `mcp_loop_test.py`); `bootstrap.py` already auto-detects. |
| R2 | Versioned user Mod dir (`v1-1` now, `v1-2` next) | wrong install path on upgrade | **Handled** — `bootstrap.py` resolves it at runtime via `FreeCAD.getUserAppDataDir()`; never hard-coded in code. Docs/skills that name `v1-1` are 1.1-specific. |
| R3 | Graft clones tracked upstream `master` (`--depth 1`) | upstream API drift silently breaks graft tests (`rocket`/`drone`/`robotics_urdf`) | **Fixed** — `bootstrap.py` pins Rocket to `v5.1.1`; AirPlaneDesign and CROSS (`freecad.cross`) track default branch (no stable tag — re-pin when one ships). |
| R4 | `mcp` SDK unbounded (`>=1.27.2`) | a breaking `2.x` desyncs the bridge / `mcp_loop_test` | **Fixed** — bounded `mcp>=1.27.2,<2`, `mcp-events>=0.1.0,<1` in `bootstrap.py`. |
| R5 | `.FCStd` checkpoints are version-tied (R/W across versions can drop objects) | restoring an old/new checkpoint after a FreeCAD upgrade may lose geometry | **Mitigated** — `checkpoint.save()` now records `freecad_version` in `state.json`. Restore on a *different* major version with care; re-checkpoint after upgrading. |
| R6 | OCCT 8.0 (FreeCAD 1.2) changes healing/validity | `gear_test` relies on `removeSplitter()`/`fix()`; tolerances may shift | **Watched** — the suite is the canary: run `python install/run_all_tests.py` after any FreeCAD upgrade; fix per failure. No code change until 1.2 is testable. |
| R7 | FEM factory name `makeSolverCalculiXCcxTools` | renamed historically (`makeSolverCalculix*`); could change again | **Watched** — validated on 1.1; `skill-fem` notes the alternates. Add a name-fallback if it breaks on 1.2. |
| R8 | New **Assembly** WB API churn (young, 1.0+) | `assembly_test` uses `Assembly::AssemblyObject` | **Watched** — placement-based assembly (what we use) is the stable subset; joints are deliberately left to the GUI. |
| R9 | `Support` → `AttachmentSupport` rename (done in 1.0) | breaks sketch-attachment scripts on <1.0 | **N/A** — our sketches use the default plane; if you add attachment, use `AttachmentSupport` (1.0+). |
| R10 | Base bridge `spawn_freecad_instance` is Unix-socket-only (`/tmp/*.sock`) | the bridge can't auto-launch FreeCAD on Windows (rejects the `A:\tmp` path) | **Worked around** — on Windows FreeCAD uses TCP `localhost:23456`; ensure the instance via the background headless launch (CLAUDE.md "Ensure FreeCAD is running") or `start-freecad-server.bat`, not `spawn_freecad_instance`. Upstream fix would TCP-enable the spawn path. |

## Upgrade checklist (when moving FreeCAD versions)
1. Set `FREECAD_MCP_FREECAD_BIN` to the new `freecadcmd` (or put it on PATH).
2. Re-run `python install/bootstrap.py --with-grafts` (resolves the new versioned Mod dir, re-registers).
3. Run `python install/run_all_tests.py` — the suite is the regression gate; triage any failure by area
   (it maps 1:1 to a skill/domain).
4. For a **major** jump (e.g. 1.1 → 1.2 / OCCT 8.0), expect possible geometry-healing/validity deltas
   (R6); re-checkpoint important work after upgrading (R5).
