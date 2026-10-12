"""
Constructive concept generator (RSE ``mode="pushout"``).

The MRO generator samples Gaussian point clouds and keeps whichever random
linear transform maximises the Betti count at the Rips cutoff. Measured on 48
concepts, the loops it finds almost all die just past that cutoff (median
persistence ratio ~0.15); searching that space for persistent loops found
one in only 5 of 48 seeds.

This generator builds the topology first and the geometry second:

1. **Compose** (abstract, exact). Start from a primitive and repeatedly glue
   on another via the categorical pushout (``pushout.glue``):
     - circle (S^1, a polygon) glued along k >= 1 shared vertices, which adds
       1 + (k - 1) independent cycles (Mayer-Vietoris: dim ker φ0 = k - 1);
     - sphere (S^2, boundary of a tetrahedron) wedged on at one vertex, which
       adds one 2-void.
   Every step runs with ``strict=True``, so no step merges simplices beyond
   the shared boundary; the Betti numbers are those Mayer-Vietoris predicts.

2. **Realise** (geometric). Lay the circle graph out in R^d (d = 3..5) with a
   spring layout, sample points along its straight edges, sample each sphere
   as a small round sphere through its attaching vertex, and reject layouts
   where unrelated parts come too close.

3. **Verify**. Recompute the point cloud's Betti numbers with the pipeline's
   own ``compute_betti`` at the construction's scale (Rips cutoff =
   ``cutoff_factor`` x sample spacing). A realisation is emitted only if they
   equal the constructed ones; otherwise it is re-laid out, and after
   ``geometry_tries`` failures the construction is dropped and counted.

Why not the adaptive cutoff: ``compute_betti``'s default cutoff is the 20th
percentile of all pairwise distances, a rule suited to blob-like noise clouds.
On a laid-out graph it lands at about one edge length, which fills in small
loops (measured: 32 of 36 circle-only realisations lost cycles). The
generator knows its own sampling scale, so it states it.

Note that the persistence ratio P is relative to the cutoff, so a cutoff tied
to the sample spacing makes P larger than under the adaptive rule. Compare
generators on death/birth, which does not depend on the cutoff.

Persistence is not assumed: ICVP measures it with the same persistence ratio
as for MRO concepts.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import networkx as nx
import numpy as np

from nhcs.layer1_genesis.invariants import compute_betti
from nhcs.layer1_genesis.prt import ENode, HypergraphStore
from nhcs.layer1_genesis.pushout import PushoutError, SimplicialComplex, glue

logger = logging.getLogger(__name__)


@dataclass
class Construction:
    """How a concept was built — recorded on the CandidateConcept."""

    steps: list[dict] = field(default_factory=list)   # one entry per primitive
    predicted_betti: list[int] = field(default_factory=list)
    ambient_dim: int = 0
    n_points: int = 0
    geometry_attempts: int = 0

    def as_dict(self) -> dict:
        return {
            "generator": "pushout",
            "steps": self.steps,
            "predicted_betti": self.predicted_betti,
            "ambient_dim": self.ambient_dim,
            "n_points": self.n_points,
            "geometry_attempts": self.geometry_attempts,
        }


def _polygon(m: int, offset: int) -> SimplicialComplex:
    vs = [offset + i for i in range(m)]
    return SimplicialComplex.from_simplices([(vs[i], vs[(i + 1) % m]) for i in range(m)])


def _tetra_boundary(offset: int) -> SimplicialComplex:
    a, b, c, d = (offset + i for i in range(4))
    return SimplicialComplex.from_simplices([(a, b, c), (a, b, d), (a, c, d), (b, c, d)])


class PushoutGenerator:
    """
    Parameters
    ----------
    n_primitives : (lo, hi)
        Number of primitives glued together per concept (inclusive).
    max_glue_points : int
        Max shared vertices when gluing a circle (k points add k - 1 extra cycles).
    sphere_prob : float
        Chance each primitive after the first is a sphere (adds a 2-void).
    ambient_dim : (lo, hi)
        Dimension of the embedding space (inclusive).
    spacing : float
        Sample spacing along edges, in units of the median edge length.
    cutoff_factor : float
        Rips cutoff for the concept's invariants, as a multiple of ``spacing``.
    clearance : float, optional
        Minimum distance between samples on unrelated parts (edges sharing no
        vertex, or a sphere and the graph away from its attaching point).
        Must exceed the cutoff or unrelated parts get joined; default
        1.4 x cutoff.
    geometry_tries : int
        Layout attempts per construction before it is dropped.
    """

    def __init__(
        self,
        n_primitives: tuple[int, int] = (2, 4),
        max_glue_points: int = 3,
        sphere_prob: float = 0.2,
        ambient_dim: tuple[int, int] = (3, 5),
        spacing: float = 0.2,
        cutoff_factor: float = 2.0,
        clearance: float | None = None,
        geometry_tries: int = 8,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.n_primitives = n_primitives
        self.max_glue_points = max_glue_points
        self.sphere_prob = sphere_prob
        self.ambient_dim = ambient_dim
        self.spacing = spacing
        self.cutoff = cutoff_factor * spacing
        self.clearance = clearance if clearance is not None else 1.4 * self.cutoff
        if self.clearance <= self.cutoff:
            raise ValueError("clearance must exceed the Rips cutoff")
        self.geometry_tries = geometry_tries
        self.rng = rng or np.random.default_rng()
        self.stats = {"constructed": 0, "emitted": 0, "dropped_geometry": 0}

    # ------------------------------------------------------------------
    # 1. Compose
    # ------------------------------------------------------------------

    def compose(self) -> tuple[SimplicialComplex, list[tuple[int, int]], list[int], Construction]:
        """
        Returns (complex, circle_edges, sphere_attach_vertices, construction).
        Vertices are ints; circle_edges are the 1-simplices of the circle graph.
        """
        rng = self.rng
        n_prim = int(rng.integers(self.n_primitives[0], self.n_primitives[1] + 1))
        m0 = int(rng.integers(4, 8))
        k = _polygon(m0, 0)
        edges = {frozenset(s) for s in k.simplices if len(s) == 2}
        spheres: list[int] = []          # attaching vertex of each sphere
        sphere_only: set[int] = set()
        cons = Construction(steps=[{"primitive": "circle", "vertices": m0, "glue_points": 0}])

        for _ in range(n_prim - 1):
            is_sphere = rng.random() < self.sphere_prob
            graph_vertices = sorted(k.vertices - sphere_only)
            for _attempt in range(20):
                if is_sphere:
                    new = _tetra_boundary(10_000)
                    pairs = [(int(rng.choice(graph_vertices)), 10_000)]
                else:
                    kmax = min(self.max_glue_points, len(graph_vertices))
                    n_glue = int(rng.integers(1, kmax + 1))
                    m = int(rng.integers(max(4, 2 * n_glue + 1), 2 * n_glue + 6))
                    new = _polygon(m, 10_000)
                    # Glue points on the new circle are spread out and in order,
                    # so no two are adjacent (adjacent pairs would collapse an edge).
                    start = int(rng.integers(m))
                    step = m / n_glue
                    on_new = [10_000 + (start + round(i * step)) % m for i in range(n_glue)]
                    on_old = [int(v) for v in rng.choice(graph_vertices, n_glue, replace=False)]
                    pairs = list(zip(on_old, on_new))
                try:
                    res = glue(k, new, pairs, strict=True)
                    break
                except PushoutError:
                    continue
            else:
                continue  # no admissible gluing found; skip this primitive

            assert res.predicted_betti is None or res.predicted_betti == res.betti[:2]
            order = sorted(res.complex.vertices, key=repr)
            lab = {v: i for i, v in enumerate(order)}
            to_c_old = {v: lab[res.j_a[v]] for v in k.vertices}
            to_c_new = {v: lab[res.j_b[v]] for v in new.vertices}
            edges = {frozenset(to_c_old[v] for v in e) for e in edges}
            sphere_only = {to_c_old[v] for v in sphere_only}
            spheres = [to_c_old[v] for v in spheres]
            if is_sphere:
                spheres.append(to_c_old[pairs[0][0]])
                sphere_only |= {to_c_new[v] for v in new.vertices if v != 10_000}
                cons.steps.append({"primitive": "sphere", "glue_points": 1,
                                   "kernel_phi0": res.kernel_phi0})
            else:
                edges |= {frozenset(to_c_new[v] for v in s)
                          for s in new.simplices if len(s) == 2}
                cons.steps.append({"primitive": "circle", "vertices": len(new.vertices),
                                   "glue_points": len(pairs), "kernel_phi0": res.kernel_phi0})
            k = SimplicialComplex(frozenset(frozenset(lab[v] for v in s)
                                            for s in res.complex.simplices))

        cons.predicted_betti = k.betti(2)
        self.stats["constructed"] += 1
        return k, [tuple(sorted(e)) for e in edges], spheres, cons

    # ------------------------------------------------------------------
    # 2. Realise
    # ------------------------------------------------------------------

    def realise(self, edges: list[tuple[int, int]], spheres: list[int], dim: int) -> np.ndarray | None:
        """Point cloud for the circle graph + spheres, or None if the layout is too tight."""
        rng = self.rng
        g = nx.Graph(edges)
        pos = nx.spring_layout(g, dim=dim, seed=int(rng.integers(2**31)), iterations=200)
        pos = {v: np.asarray(p, float) + rng.normal(0, 0.02, dim) for v, p in pos.items()}
        lengths = [np.linalg.norm(pos[a] - pos[b]) for a, b in edges]
        scale = 1.0 / float(np.median(lengths))
        pos = {v: p * scale for v, p in pos.items()}
        if min(lengths) * scale < 0.6:
            return None

        h = self.spacing
        samples: list[np.ndarray] = [pos[v] for v in g.nodes]
        owner: list[tuple] = [("v", v) for v in g.nodes]
        for a, b in edges:
            n = max(1, math.ceil(np.linalg.norm(pos[a] - pos[b]) / h))
            for t in np.arange(1, n) / n:
                samples.append((1 - t) * pos[a] + t * pos[b])
                owner.append(("e", a, b))
        pts = np.array(samples)

        # Edges sharing no vertex must keep their distance.
        if not self._clear(pts, owner):
            return None

        sphere_pts = []
        centroid = pts.mean(axis=0)
        for v in spheres:
            for _ in range(10):
                out = pos[v] - centroid + rng.normal(0, 0.3, dim)
                u = out / np.linalg.norm(out)
                r = float(rng.uniform(0.45, 0.6))
                basis = np.linalg.qr(np.column_stack([u, rng.standard_normal((dim, 2))]))[0][:, :3]
                if basis[:, 0] @ u < 0:
                    basis[:, 0] *= -1
                c = pos[v] + r * u
                n_s = max(24, math.ceil(4 * math.pi * r * r / (0.8 * h) ** 2))
                fib = _fibonacci_sphere(n_s)
                s = c + r * fib @ basis.T
                s = s[np.linalg.norm(s - pos[v], axis=1) > 0.5 * h]  # v itself is already sampled
                far_from_v = np.linalg.norm(pts - pos[v], axis=1) > 2.5 * r
                if far_from_v.any():
                    d = np.min(np.linalg.norm(s[:, None] - pts[far_from_v][None], axis=-1))
                    if d < self.clearance:
                        continue
                if sphere_pts:
                    d = np.min(np.linalg.norm(s[:, None] - np.vstack(sphere_pts)[None], axis=-1))
                    if d < self.clearance:
                        continue
                sphere_pts.append(s)
                break
            else:
                return None
        return np.vstack([pts] + sphere_pts) if sphere_pts else pts

    def _clear(self, pts, owner) -> bool:
        """Samples closer than ``clearance`` must lie on parts that share a vertex."""
        ends = [{o[1]} if o[0] == "v" else {o[1], o[2]} for o in owner]
        d = np.linalg.norm(pts[:, None] - pts[None], axis=-1)
        for i, j in np.argwhere(np.triu(d < self.clearance, 1)):
            if not ends[i] & ends[j]:
                return False
        return True

    # ------------------------------------------------------------------
    # 3. Verify + emit
    # ------------------------------------------------------------------

    def generate_one(self):
        """One verified concept, or None if no layout reproduced its Betti numbers."""
        from nhcs.layer1_genesis.rse import CandidateConcept  # avoid import cycle

        k, edges, spheres, cons = self.compose()
        dim = int(self.rng.integers(self.ambient_dim[0], self.ambient_dim[1] + 1))
        for attempt in range(1, self.geometry_tries + 1):
            pts = self.realise(edges, spheres, dim)
            if pts is None:
                continue
            profile = compute_betti(pts, max_dimension=2, max_edge_length=self.cutoff)
            if profile.betti != cons.predicted_betti:
                logger.debug("realisation mismatch: built %s, measured %s",
                             cons.predicted_betti, profile.betti)
                continue
            cons.ambient_dim, cons.n_points, cons.geometry_attempts = dim, len(pts), attempt
            store = HypergraphStore()
            for coord in pts:
                store.add_node(ENode(manifold_coords=coord))
            self.stats["emitted"] += 1
            return CandidateConcept(store=store, point_cloud=pts, invariant=profile,
                                    iteration=0, rng_seed=0, construction=cons.as_dict())
        self.stats["dropped_geometry"] += 1
        logger.debug("dropped construction %s after %d layouts",
                     cons.predicted_betti, self.geometry_tries)
        return None

    def run(self, n_concepts: int):
        out = []
        for i in range(n_concepts):
            c = self.generate_one()
            if c is not None:
                c.rng_seed = i
                out.append(c)
        logger.info("Pushout generator produced %d/%d concepts (stats=%s).",
                    len(out), n_concepts, self.stats)
        return out


def _fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    theta = np.arccos(1 - 2 * i / n)
    phi = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(theta), np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi)], 1)
