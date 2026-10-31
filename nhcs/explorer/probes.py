"""
Budgeted probes of a hidden 4D object, held-out slice tasks, and scoring.

Three probes, each costing one unit of budget:

  slice(normal, offset)
      The 3D cross-section {x : normal . x = offset}. Points within a thin
      slab are kept and expressed in coordinates on the hyperplane. Reported:
      its Betti numbers, point count, component sizes and extent.
  project(direction)
      The shadow of the object in the 3-space orthogonal to ``direction``.
      Same report. Projections can merge components and create spurious loops
      and voids where the shadow crosses itself; they never split components.
  slab(normal, lo, hi)
      The part of the object with lo <= normal . x <= hi, kept in R^4 (no
      projection). Width must be between MIN_SLAB and MAX_SLAB, so one slab
      never swallows the whole object. Slabs exist because slices and shadows
      cannot see the Euler characteristic: tile the object with overlapping
      slabs and Mayer-Vietoris gives
          chi(X) = sum chi(slabs) - sum chi(overlaps),
      exactly (verified: 28/28 across seven objects with 0.1-wide overlaps;
      abutting slabs with slices standing in for the overlaps fail ~1 in 3).

All topology is measured at one fixed Rips scale per object (RESOLUTION x the
sampling scale), the same scale at which the object's own Betti numbers were
verified. Held-out slices are scored against the same measurement, so an
explorer is graded on exactly what it would have seen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np

from nhcs.explorer.objects import RESOLUTION, Hidden4D, euler, orientability_decidable
from nhcs.explorer.topology import betti_at_scale, voxel_downsample


MIN_SLAB = 0.1
MAX_SLAB = 0.6


class ProbeError(ValueError):
    pass


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float).reshape(-1)
    if v.shape != (4,):
        raise ProbeError("direction must have 4 components")
    n = np.linalg.norm(v)
    if not np.isfinite(n) or n < 1e-9:
        raise ProbeError("direction must be a non-zero 4-vector")
    return v / n


def _complement_basis(n: np.ndarray) -> np.ndarray:
    """Orthonormal 3x4 basis of the hyperplane orthogonal to n."""
    q, _ = np.linalg.qr(np.column_stack([n, np.eye(4)]))
    return q[:, 1:4].T


@dataclass
class HeldOutSlice:
    normal: list[float]
    offset: float

    def as_dict(self):
        return {"normal": [round(x, 4) for x in self.normal], "offset": round(self.offset, 4)}


class ProbeSession:
    """
    Parameters
    ----------
    obj : Hidden4D
    budget : int
        Number of probes the explorer may spend.
    n_held_out : int
        Slices the explorer must predict without probing them.
    seed : int
    """

    def __init__(self, obj: Hidden4D, budget: int = 20, n_held_out: int = 4, seed: int = 0) -> None:
        self.obj = obj
        self.budget = budget
        self.scale = RESOLUTION * obj.spacing
        # Slab half-width. 0.25 x scale: thin enough that slices past an edge come
        # back empty, thick enough that slice curves stay connected (agreed with
        # 0.15 x scale on 48/48 random slices across four surfaces).
        self.thickness = 0.25 * self.scale
        self.rng = np.random.default_rng(seed)
        self.log: list[dict] = []
        self.held_out = [self._random_slice() for _ in range(n_held_out)]
        self._held_truth = [self._measure_slice(_unit(h.normal), h.offset)["betti"][:2] for h in self.held_out]

    # -- probes -----------------------------------------------------------

    @property
    def remaining(self) -> int:
        return self.budget - len(self.log)

    def slice(self, normal, offset: float) -> dict:
        n = _unit(normal)
        offset = float(offset)
        self._check_budget()
        self._check_held_out(n, offset, offset)
        out = self._measure_slice(n, offset)
        self.log.append({"probe": "slice", "normal": n.round(4).tolist(), "offset": round(offset, 4), **out})
        return out

    def project(self, direction) -> dict:
        d = _unit(direction)
        self._check_budget()
        B = _complement_basis(d)
        pts = self.obj.points @ B.T
        out = self._describe(voxel_downsample(pts, self.scale / 2.5))
        self.log.append({"probe": "project", "direction": d.round(4).tolist(), **out})
        return out

    def slab(self, normal, lo: float, hi: float) -> dict:
        n = _unit(normal)
        lo, hi = float(lo), float(hi)
        if not (MIN_SLAB - 1e-9 <= hi - lo <= MAX_SLAB + 1e-9):
            raise ProbeError(f"slab width hi - lo must be between {MIN_SLAB} and {MAX_SLAB}")
        self._check_budget()
        self._check_held_out(n, lo, hi)
        h = self.obj.points @ n
        out = self._describe(voxel_downsample(self.obj.points[(h >= lo) & (h <= hi)], self.scale / 2.5))
        self.log.append({"probe": "slab", "normal": n.round(4).tolist(), "lo": round(lo, 4), "hi": round(hi, 4), **out})
        return out

    # -- held-out scoring --------------------------------------------------

    def score(self, answer: dict) -> dict:
        """
        answer = {"betti": [b0, b1, b2], "dimension": 1 | 2, "orientable": bool | None,
                  "held_out": [[b0, b1], ...]  (one per held-out slice, in order)}

        The headline score is 0.5 * core + 0.5 * held-out accuracy, where core
        means pieces (b0), dimension and Euler characteristic are all right:
        exactly what the probes can decide. Exact Betti numbers and
        orientability are reported too; for objects whose orientability the
        probes cannot decide (orientability_decidable False) they are partly
        a guess, so they stay out of the headline.
        """
        truth = self.obj.betti
        b = [int(x) for x in (list(answer.get("betti") or []) + [0, 0, 0])[:3]]
        dim = answer.get("dimension")
        if dim is None and answer.get("betti"):
            dim = 2 if b[2] > 0 else None
        core = bool(answer.get("betti")) and b[0] == truth[0] and euler(b) == euler(truth) and dim == self.obj.intrinsic_dim
        preds = answer.get("held_out") or []
        hits = 0
        for i, t in enumerate(self._held_truth):
            p = preds[i] if i < len(preds) else None
            if p is not None and [int(x) for x in list(p)[:2]] == t:
                hits += 1
        held_acc = hits / len(self._held_truth) if self._held_truth else 0.0
        orient = answer.get("orientable")
        orient_ok = None if self.obj.orientable is None or orient is None else bool(orient) == self.obj.orientable
        return {
            "object": self.obj.name,
            "betti_true": truth, "betti_answer": b,
            "dimension_true": self.obj.intrinsic_dim, "dimension_answer": dim,
            "euler_true": euler(truth), "euler_answer": euler(b),
            "core_correct": core,
            "betti_exact": b == truth,
            "betti_abs_error": int(sum(abs(x - y) for x, y in zip(b, truth))),
            "orientable_true": self.obj.orientable, "orientable_answer": orient, "orientable_correct": orient_ok,
            "orientability_decidable": orientability_decidable(self.obj),
            "held_out_slices": [h.as_dict() for h in self.held_out],
            "held_out_truth": self._held_truth, "held_out_answer": preds,
            "held_out_accuracy": held_acc,
            "probes_used": len(self.log), "budget": self.budget,
            "score": 0.5 * core + 0.5 * held_acc,
        }

    # -- internals ---------------------------------------------------------

    def _check_held_out(self, n: np.ndarray, lo: float, hi: float):
        """
        Refuse probes along (nearly) a held-out normal, either sign, that reach
        within 0.08 of its offset or of the mirrored offset. The mirror matters:
        a centrally symmetric object (circle, sphere, torus, ...) has the same
        slice at -offset, and the mirrored slice matched the held-out answer in
        90/132 suite trials.
        """
        for h in self.held_out:
            hn = np.asarray(h.normal)
            if np.degrees(np.arccos(np.clip(abs(hn @ n), 0, 1))) >= 10:
                continue
            for o in (h.offset, -h.offset):
                if lo - 0.08 < o < hi + 0.08:
                    raise ProbeError("that probe is too close to a held-out slice (or its mirror image); probe elsewhere")

    def _check_budget(self):
        if self.remaining <= 0:
            raise ProbeError("probe budget exhausted; submit an answer")

    def _random_slice(self) -> HeldOutSlice:
        n = _unit(self.rng.standard_normal(4))
        h = self.obj.points @ n
        lo, hi = np.percentile(h, [8, 92])
        return HeldOutSlice(n.tolist(), float(self.rng.uniform(lo, hi)))

    def _measure_slice(self, n: np.ndarray, offset: float) -> dict:
        h = self.obj.points @ n
        sel = self.obj.points[np.abs(h - offset) < self.thickness]
        pts = sel @ _complement_basis(n).T
        return self._describe(voxel_downsample(pts, self.scale / 2.5))

    def _describe(self, pts: np.ndarray) -> dict:
        if len(pts) == 0:
            return {"empty": True, "betti": [0, 0, 0], "euler": 0, "n_points": 0, "components": [], "extent": 0.0}
        b = betti_at_scale(pts, self.scale, 2)
        # component sizes (by union-find on the Rips 1-skeleton)
        from scipy.sparse.csgraph import connected_components
        from scipy.spatial import cKDTree
        pairs = cKDTree(pts).query_pairs(self.scale, output_type="ndarray")
        import scipy.sparse as sp
        m = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(pts), len(pts))) if len(pairs) else sp.coo_matrix((len(pts), len(pts)))
        _, lab = connected_components(m, directed=False)
        sizes = sorted(np.bincount(lab).tolist(), reverse=True)
        ctr = pts.mean(0)
        return {"empty": False, "betti": b, "euler": b[0] - b[1] + b[2], "n_points": int(len(pts)),
                "components": sizes[:6], "extent": round(float(np.linalg.norm(pts - ctr, axis=1).max()), 3)}

    def transcript(self) -> str:
        return json.dumps(self.log, indent=1)
