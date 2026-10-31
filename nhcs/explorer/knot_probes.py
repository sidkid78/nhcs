"""
Calibration benchmark for knotted 2-spheres in R^4, with a knot-reading slice probe.

Every hidden object is a 2-sphere, so Betti numbers say nothing (always
[1, 0, 1]). What differs is how it sits in R^4. The probe:

  knot_slice(normal, offset)
      The cross-section {normal . x = offset} is a link in R^3. Reported: the
      number of components; for each, its knot type when small enough to name
      (else its invariants: Alexander polynomial, Seifert genus, fiberedness,
      tau, all from knot Floer homology); and the pairwise linking numbers
      (absolute values; components carry no orientation).

The suite is chosen so the answers are theorems:

  unknotted_sphere        spun unknot: unknotted
  spun_trefoil            Artin spin of 3_1: knotted, group = trefoil group
  spun_figure_eight       Artin spin of 4_1: knotted
  twist1_trefoil          1-twist-spun 3_1: UNKNOTTED (Zeeman), slices still show 3_1 # m3_1
  twist1_figure_eight     1-twist-spun 4_1: UNKNOTTED (Zeeman)
  twist2_trefoil          2-twist-spun 3_1: knotted (fibre: punctured lens space L(3,1))
  twist3_trefoil          3-twist-spun 3_1: knotted (fibre: punctured quaternionic manifold)

Measured, unposed: the equatorial slice of every spun or twist-spun trefoil
is 3_1 # m3_1, so the obvious slice cannot tell knotted from unknotted;
slices across the spin axis give circles whose pairwise linking number is
the twist.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from nhcs.explorer import knots as K
from nhcs.explorer.probes import HeldOutSlice, ProbeError, _complement_basis, _unit

KNOT_SUITE = {
    # name: (base curve, twist, knotted, base knot label)
    "unknotted_sphere": ("unknot", 0, False, "unknot"),
    "spun_trefoil": ("trefoil", 0, True, "3_1"),
    "spun_figure_eight": ("figure_eight", 0, True, "4_1"),
    "twist1_trefoil": ("trefoil", 1, False, "3_1"),
    "twist1_figure_eight": ("figure_eight", 1, False, "4_1"),
    "twist2_trefoil": ("trefoil", 2, True, "3_1"),
    "twist3_trefoil": ("trefoil", 3, True, "3_1"),
}

_MESH: dict = {}


@dataclass
class HiddenSurface:
    name: str
    V: np.ndarray            # (N, 4) vertices, centred, max norm 1, randomly posed
    T: np.ndarray            # (M, 3) triangles
    knotted: bool
    construction: str        # "spun" | "twist-spun"
    base_knot: str
    twist: int
    meta: dict = field(default_factory=dict)


def make_surface(name: str, seed: int = 0, n_theta: int = 180) -> HiddenSurface:
    curve, twist, knotted, base = KNOT_SUITE[name]
    key = (name, n_theta)
    if key not in _MESH:
        _MESH[key] = K.spun_sphere(K.CURVES[curve](), twist=twist, n_theta=n_theta)
    V, T = _MESH[key]
    V = V - V.mean(0)
    V = V / np.linalg.norm(V, axis=1).max()
    q, r = np.linalg.qr(np.random.default_rng(seed).standard_normal((4, 4)))
    V = V @ (q * np.sign(np.diag(r))).T
    return HiddenSurface(name, V, T, knotted, "twist-spun" if twist else "spun", base, twist)


def _label(c: dict) -> str:
    if c.get("name"):
        return c["name"]
    return f"knot(alexander={c['alexander']}, genus={c['genus']})"


def _near_touch(loops: list, eps: float) -> bool:
    """
    True if two slice curves, or two stretches of one curve that are far apart
    along it (more than 10 eps of arc length), come within eps of each other.
    """
    from scipy.spatial import cKDTree
    pts = np.vstack(loops)
    comp = np.concatenate([np.full(len(lp), i) for i, lp in enumerate(loops)])
    arc, tot = [], []
    for lp in loops:
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(lp, axis=0), axis=1))]
        L = d[-1] + np.linalg.norm(lp[0] - lp[-1])
        arc.append(d)
        tot.append(np.full(len(lp), L))
    arc, tot = np.concatenate(arc), np.concatenate(tot)
    pr = cKDTree(pts).query_pairs(eps, output_type="ndarray")
    if not len(pr):
        return False
    i, j = pr[:, 0], pr[:, 1]
    other = comp[i] != comp[j]
    g = np.abs(arc[i] - arc[j])
    g = np.minimum(g, tot[i] - g)
    return bool((other | ((comp[i] == comp[j]) & (g > 10 * eps))).any())


class KnotSession:
    """Budgeted knot_slice probes of one hidden sphere, plus held-out slices to predict."""

    def __init__(self, obj: HiddenSurface, budget: int = 20, n_held_out: int = 3, seed: int = 0) -> None:
        self.obj = obj
        self.budget = budget
        self.rng = np.random.default_rng(seed)
        self.log: list[dict] = []
        e = obj.T[:, :2]
        self.eps = 2.0 * float(np.median(np.linalg.norm(obj.V[e[:, 0]] - obj.V[e[:, 1]], axis=1)))
        self.held_out: list[HeldOutSlice] = []
        self._held_truth: list[list[str]] = []
        tries = 0
        while len(self.held_out) < n_held_out and tries < 50:
            tries += 1
            n = _unit(self.rng.standard_normal(4))
            h = obj.V @ n
            lo, hi = np.percentile(h, [10, 90])
            off = float(self.rng.uniform(lo, hi))
            out = self._measure(n, off)
            if out["empty"]:
                continue
            self.held_out.append(HeldOutSlice(n.tolist(), off))
            self._held_truth.append(sorted(_label(c) for c in out["knots"]))

    @property
    def remaining(self) -> int:
        return self.budget - len(self.log)

    def knot_slice(self, normal, offset: float) -> dict:
        n = _unit(normal)
        offset = float(offset)
        if self.remaining <= 0:
            raise ProbeError("probe budget exhausted; submit an answer")
        for h in self.held_out:
            hn = np.asarray(h.normal)
            if np.degrees(np.arccos(np.clip(abs(hn @ n), 0, 1))) < 10 and \
                    any(abs(o - offset) < 0.08 for o in (h.offset, -h.offset)):
                raise ProbeError("that probe is too close to a held-out slice (or its mirror image); probe elsewhere")
        out = self._measure(n, offset)
        self.log.append({"probe": "knot_slice", "normal": n.round(4).tolist(), "offset": round(offset, 4), **out})
        return out

    def _measure(self, n: np.ndarray, offset: float) -> dict:
        """
        Read the slice at ``offset``. A slice a hair away from a critical level
        has curves nearly touching (themselves or each other), where the
        piecewise-linear curves can pass through one another and the link is
        not well defined at mesh resolution. Such cuts are nudged to the
        nearest clean offset within 0.03; "offset_used" reports it.
        """
        for d in (0.0, 0.004, -0.004, 0.008, -0.008, 0.015, -0.015, 0.03, -0.03):
            loops = K.slice_mesh(self.obj.V, self.obj.T, n, offset + d)
            if not loops or not _near_touch(loops, self.eps):
                break
        out = self._read(n, loops)
        out["offset_used"] = round(offset + d, 4)
        return out

    def _read(self, n: np.ndarray, loops: list) -> dict:
        if not loops:
            return {"empty": True, "components": 0, "knots": [], "linking": []}
        B = _complement_basis(n)
        r = K.read_link([lp @ B.T for lp in loops])
        knots = [{"name": c["name"], "alexander": c["alexander"], "genus": c["genus"], "fibered": c["fibered"],
                  "tau": c["tau"], "crossings": c["crossings"]} for c in r["components"]]
        return {"empty": False, "components": len(loops), "knots": knots,
                "linking": [{"pair": [a, b], "lk": v} for a, b, v in r["linking"]]}

    def score(self, answer: dict) -> dict:
        """
        answer = {"knotted": bool, "construction": "unknotted" | "spun" | "twist-spun",
                  "knot": "3_1" | "4_1" | ..., "twist": int | None,
                  "held_out": [[component labels], ...], "description": str}

        score = 0.5 * knotted right + 0.25 * construction right + 0.25 * held-out accuracy.
        Construction right means: "unknotted" for any sphere that is unknotted
        (the spun unknot and the 1-twist-spins), or the family, the base knot
        (mirror images allowed) and for twist-spins the twist.
        """
        o = self.obj
        k = answer.get("knotted")
        knotted_ok = k is not None and bool(k) == o.knotted
        cons = (answer.get("construction") or "").lower()
        base = (answer.get("knot") or "").replace("m", "") or None
        if o.base_knot == "unknot":
            cons_ok = cons == "unknotted" or (cons == "spun" and base in (None, "unknot", "0_1"))
        elif not o.knotted and cons == "unknotted":
            cons_ok = True  # a 1-twist-spun knot IS the unknotted sphere: naming the isotopy class is right too
        else:
            cons_ok = cons == o.construction and base == o.base_knot and \
                (o.twist == 0 or int(answer.get("twist") or 0) == o.twist)
        preds = answer.get("held_out") or []
        hits = sum(1 for i, t in enumerate(self._held_truth)
                   if i < len(preds) and sorted(str(x) for x in (preds[i] or [])) == t)
        held = hits / len(self._held_truth) if self._held_truth else 0.0
        return {"object": o.name, "knotted_true": o.knotted, "knotted_answer": k, "knotted_correct": knotted_ok,
                "construction_true": f"{o.construction} {o.base_knot}" + (f" twist {o.twist}" if o.twist else ""),
                "construction_answer": f"{cons} {answer.get('knot')}" + (f" twist {answer.get('twist')}" if answer.get("twist") else ""),
                "construction_correct": cons_ok,
                "held_out_slices": [h.as_dict() for h in self.held_out], "held_out_truth": self._held_truth,
                "held_out_answer": preds, "held_out_accuracy": held,
                "probes_used": len(self.log), "budget": self.budget,
                "score": 0.5 * knotted_ok + 0.25 * cons_ok + 0.25 * held}
