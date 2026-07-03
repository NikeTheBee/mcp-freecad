# skill-cfd

**Load when:** the task asks for aerodynamic analysis — drag, lift, flow, "CFD", airflow over a
rocket/drone/vehicle. This is the **fallback workflow** of cahier des charges §12: FreeCAD here
prepares and exports; heavy CFD runs outside.

## Decision ladder (cheapest first)
1. **Analytical, in-repo (seconds, no deps)** — often enough for sizing/stability:
   - Rocket stability: Barrowman CP + static margin — see `skill-rocket` and
     `install/rocket_cp_test.py`.
   - Multirotor/fixed-wing sizing: `server/freecad_layers/aero.py` — hover thrust/power
     (momentum theory), T/W, disk loading, endurance, tip Mach, wing loading, stall speed.
     ```python
     import sys; sys.path.insert(0, r"<repo>\server")
     from freecad_layers import aero
     print(aero.verdict_multirotor(mass_kg=1.2, n_motors=4,
           prop_diameter_m=0.254, max_thrust_per_motor_n=8.0, battery_wh=55.5))
     # OK multirotor: T/W=2.72 hover=82.3W disk=58.1N/m2 endurance~27.9min
     ```
2. **External OpenFOAM (prototype CFD)** — export from FreeCAD, mesh & solve outside:
   - Gate the geometry first: `verify.watertight(obj)` must pass (see `skill-verify`).
   - Export **STL** (for `snappyHexMesh`) via `skill-print3d`, or **STEP** via `skill-exchange`.
   - Typical case: incompressible steady RANS (`simpleFoam`, k-ω SST), wind-tunnel-style box
     domain ≥ 10 body-lengths downstream, `forceCoeffs` function object for Cd/Cl.
   - Deliverable to the user: the exported file + a short description of the case setup;
     running OpenFOAM itself is outside this repo's scope.
3. **CfdOF workbench (optional, NOT installed)** — GUI front-end to OpenFOAM inside FreeCAD.
   Requires a local OpenFOAM + ParaView install; only suggest it if the user has them.

## Honest limits (§3.2)
- Momentum theory ignores profile drag & interference: hover power ±15–25 %.
- CfdOF/OpenFOAM prototyping ≠ engineering-grade aero; the CfdOF maintainer himself
  recommends commercial tools for serious work. Say so when it matters.

## Verify
`install/drone_aero_test.py` (sentinel `DRONE_AERO_OK`) validates the analytical layer.
