"""Rocket centre-of-pressure & stability via the Barrowman method (cahier §4.3).

Run with:  A:/FreeCAD/bin/freecadcmd.exe install/rocket_cp_test.py

Analytical (subsonic) aerodynamics — NO CFD/OpenFOAM needed. Computes the centre
of pressure (CP) from nose + body-transitions + fins, and the static stability
margin in calibers given the centre of gravity (CG). Prints ROCKET_CP_OK.
"""
import math
from dataclasses import dataclass, field
from typing import List

NOSE_K = {"ogive": 0.466, "cone": 0.666, "parabolic": 0.5, "haack": 0.437}


@dataclass
class Nose:
    length: float
    diameter: float
    shape: str = "ogive"


@dataclass
class Transition:
    x: float          # position of fore end from tip
    length: float
    d_fore: float
    d_aft: float


@dataclass
class FinSet:
    x_root_le: float  # root leading-edge position from nose tip
    root_chord: float
    tip_chord: float
    semispan: float
    sweep: float      # LE sweep distance (root LE to tip LE, axial)
    count: int
    body_d: float     # body diameter at the fins


@dataclass
class Rocket:
    d_ref: float
    nose: Nose
    transitions: List[Transition] = field(default_factory=list)
    fins: FinSet = None


def barrowman_cp(r: Rocket):
    """Return (cp_from_tip_mm, total_CN). Classic Barrowman component sum."""
    terms = []  # (CN, X)

    # Nose: CN = 2 (referenced to d_ref via area ratio; nose d == d_ref assumed)
    cn_nose = 2.0 * (r.nose.diameter / r.d_ref) ** 2
    x_nose = NOSE_K.get(r.nose.shape, 0.466) * r.nose.length
    terms.append((cn_nose, x_nose))

    # Conical transitions
    for t in r.transitions:
        cn = 2.0 * ((t.d_aft / r.d_ref) ** 2 - (t.d_fore / r.d_ref) ** 2)
        xt = t.x + (t.length / 3.0) * (1 + (1 - t.d_fore / t.d_aft) /
                                       (1 - (t.d_fore / t.d_aft) ** 2)) \
            if t.d_aft != t.d_fore else t.x + t.length / 2.0
        terms.append((cn, xt))

    # Fins (Barrowman)
    f = r.fins
    if f:
        R = f.body_d / 2.0
        s = f.semispan
        # mid-chord sweep length
        lf = math.sqrt(s ** 2 + (f.sweep + (f.tip_chord - f.root_chord) / 2.0) ** 2)
        cn_fins = (1 + R / (s + R)) * (
            (4 * f.count * (s / r.d_ref) ** 2) /
            (1 + math.sqrt(1 + (2 * lf / (f.root_chord + f.tip_chord)) ** 2))
        )
        x_fins = f.x_root_le \
            + (f.sweep / 3.0) * (f.root_chord + 2 * f.tip_chord) / (f.root_chord + f.tip_chord) \
            + (1.0 / 6.0) * ((f.root_chord + f.tip_chord)
                             - (f.root_chord * f.tip_chord) / (f.root_chord + f.tip_chord))
        terms.append((cn_fins, x_fins))

    total_cn = sum(cn for cn, _ in terms)
    cp = sum(cn * x for cn, x in terms) / total_cn
    return cp, total_cn


def stability_calibers(cp_mm: float, cg_mm: float, d_ref: float) -> float:
    return (cp_mm - cg_mm) / d_ref


# --- A plausible 3-fin model rocket ---
rocket = Rocket(
    d_ref=24.0,
    nose=Nose(length=70, diameter=24, shape="ogive"),
    fins=FinSet(x_root_le=300, root_chord=50, tip_chord=25,
                semispan=30, sweep=25, count=3, body_d=24),
)
cp, cn = barrowman_cp(rocket)
cg = 200.0  # assumed centre of gravity from tip (mm)
margin = stability_calibers(cp, cg, rocket.d_ref)
print(f"CP = {cp:.1f} mm from tip | total CN_alpha = {cn:.2f}")
print(f"CG = {cg:.1f} mm | stability margin = {margin:.2f} calibers")

assert 70 < cp < 350, "CP outside the rocket body — calc wrong"
assert cn > 0, "non-physical normal-force slope"
assert margin > 0, "CP ahead of CG -> unstable"  # stable rockets: CP behind CG
# typical model-rocket stability is ~1-2 calibers; sanity-bound it
assert 0.2 < margin < 5, f"implausible stability margin {margin:.2f}"
print("ROCKET_CP_OK")
