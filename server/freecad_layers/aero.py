"""Analytical drone aero/sizing — the drone counterpart of the rocket's
Barrowman stability check (cahier des charges §4.3, no CFD required).

Pure Python (no FreeCAD import): usable under freecadcmd, the bridge's
execute_python, or system Python. Momentum-theory estimates good for sanity
checks and first sizing; for serious aero use the skill-cfd external workflow.

Conventions: SI units in/out (kg, m, N, W); compact text verdicts like
`verify.verdict` (token-efficient).
"""
from __future__ import annotations

import math
from typing import Any, Dict

G = 9.81          # m/s²
RHO = 1.225       # kg/m³, sea-level ISA
SOUND = 340.3     # m/s, sea level


# ── multirotor ───────────────────────────────────────────────────────────────
def hover_thrust_per_motor(mass_kg: float, n_motors: int) -> float:
    """Thrust each motor must produce to hover [N]."""
    return mass_kg * G / n_motors


def thrust_to_weight(total_max_thrust_n: float, mass_kg: float) -> float:
    """Total max thrust over weight. ≥2 recommended for a controllable multirotor."""
    return total_max_thrust_n / (mass_kg * G)


def disk_area(prop_diameter_m: float, n_motors: int) -> float:
    """Total rotor disk area [m²]."""
    return n_motors * math.pi * (prop_diameter_m / 2.0) ** 2


def disk_loading(mass_kg: float, prop_diameter_m: float, n_motors: int) -> float:
    """Weight per rotor area [N/m²]. Hover-efficient multirotors: ~50–250 N/m²."""
    return mass_kg * G / disk_area(prop_diameter_m, n_motors)


def hover_power(mass_kg: float, prop_diameter_m: float, n_motors: int,
                figure_of_merit: float = 0.7, rho: float = RHO) -> float:
    """Mechanical hover power [W], momentum theory: P = T^1.5 / (FoM·√(2ρA)) per rotor."""
    t = hover_thrust_per_motor(mass_kg, n_motors)
    a = math.pi * (prop_diameter_m / 2.0) ** 2
    p_ideal = t ** 1.5 / math.sqrt(2.0 * rho * a)
    return n_motors * p_ideal / figure_of_merit


def flight_time_min(battery_wh: float, hover_power_w: float,
                    usable_fraction: float = 0.8,
                    drive_efficiency: float = 0.85) -> float:
    """Hover endurance estimate [min] from battery energy and mech hover power."""
    electrical_w = hover_power_w / drive_efficiency
    return battery_wh * usable_fraction / electrical_w * 60.0


def tip_mach(rpm: float, prop_diameter_m: float) -> float:
    """Prop tip Mach number; keep < ~0.6 to avoid noise/efficiency collapse."""
    tip_speed = math.pi * prop_diameter_m * rpm / 60.0
    return tip_speed / SOUND


# ── fixed wing ───────────────────────────────────────────────────────────────
def wing_loading(mass_kg: float, wing_area_m2: float) -> float:
    """Weight per wing area [N/m²]."""
    return mass_kg * G / wing_area_m2


def stall_speed(mass_kg: float, wing_area_m2: float,
                cl_max: float = 1.3, rho: float = RHO) -> float:
    """V_stall = √(2W / (ρ·S·CLmax)) [m/s]."""
    return math.sqrt(2.0 * mass_kg * G / (rho * wing_area_m2 * cl_max))


# ── verdicts ─────────────────────────────────────────────────────────────────
def check_multirotor(mass_kg: float, n_motors: int, prop_diameter_m: float,
                     max_thrust_per_motor_n: float,
                     battery_wh: float | None = None) -> Dict[str, Any]:
    """Sizing sanity check; returns dict with ok/issues + key numbers."""
    res: Dict[str, Any] = {"issues": []}
    res["hover_thrust_per_motor_n"] = round(hover_thrust_per_motor(mass_kg, n_motors), 2)
    tw = thrust_to_weight(max_thrust_per_motor_n * n_motors, mass_kg)
    res["thrust_to_weight"] = round(tw, 2)
    dl = disk_loading(mass_kg, prop_diameter_m, n_motors)
    res["disk_loading_n_m2"] = round(dl, 1)
    p = hover_power(mass_kg, prop_diameter_m, n_motors)
    res["hover_power_w"] = round(p, 1)
    if battery_wh:
        res["flight_time_min"] = round(flight_time_min(battery_wh, p), 1)

    if tw < 1.0:
        res["issues"].append(f"cannot hover: T/W={tw:.2f} < 1")
    elif tw < 2.0:
        res["issues"].append(f"marginal control authority: T/W={tw:.2f} < 2 recommended")
    if dl > 400.0:
        res["issues"].append(f"very high disk loading ({dl:.0f} N/m²): inefficient hover")
    res["ok"] = not any("cannot hover" in i for i in res["issues"])
    return res


def verdict_multirotor(mass_kg: float, n_motors: int, prop_diameter_m: float,
                       max_thrust_per_motor_n: float,
                       battery_wh: float | None = None) -> str:
    """One-line, token-minimal verdict string."""
    r = check_multirotor(mass_kg, n_motors, prop_diameter_m,
                         max_thrust_per_motor_n, battery_wh)
    head = "OK" if r["ok"] and not r["issues"] else ("WARN" if r["ok"] else "FAIL")
    base = (f"{head} multirotor: T/W={r['thrust_to_weight']} "
            f"hover={r['hover_power_w']}W disk={r['disk_loading_n_m2']}N/m2")
    if "flight_time_min" in r:
        base += f" endurance~{r['flight_time_min']}min"
    if r["issues"]:
        base += " | " + "; ".join(r["issues"])
    return base
