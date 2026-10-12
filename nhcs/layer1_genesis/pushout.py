"""
Categorical pushout of simplicial complexes (concept gluing).

Given complexes K_A, K_B and a shared sub-complex K_I, identified in each by
vertex maps i_A : K_I -> K_A and i_B : K_I -> K_B, the pushout is

    K_C = (K_A ⊔ K_B) / ~ ,   i_A(x) ~ i_B(x)  for every vertex x of K_I.

In the category of simplicial complexes a simplex is determined by its vertex
set, so the quotient can identify MORE than K_I: if two vertices of K_I span an
edge in both K_A and K_B, but that edge is not in K_I, the two edges collapse
into one. Mayer-Vietoris (and the formula β1(K_C) = β1(K_A) + β1(K_B) +
dim ker φ0 when H1(K_I) = 0) only holds when the images of K_A and K_B meet in
exactly the image of K_I. ``glue`` detects that condition and reports it as
``collapsed`` (or raises, with ``strict=True``).

Homology here is ORDINARY simplicial homology of a fixed complex (computed with
GUDHI over Z/2 at a single filtration value). To glue two RSE concepts, first
extract each concept's Rips complex at its own cutoff with
``complex_from_points`` -- do not merge the point clouds and re-run Rips, which
creates new cross edges between nearby points and breaks the pushout.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Hashable, Iterable, Mapping

import numpy as np

logger = logging.getLogger(__name__)

try:
    import gudhi  # type: ignore
    _GUDHI_AVAILABLE = True
except ImportError:  # pragma: no cover - GUDHI is a hard dependency in practice
    _GUDHI_AVAILABLE = False

Vertex = Hashable
Simplex = frozenset


def _closure(simplices: Iterable[Iterable[Vertex]]) -> set[Simplex]:
    """All faces of the given simplices (downward closure)."""
    out: set[Simplex] = set()
    for s in simplices:
        s = tuple(s)
        for k in range(1, len(s) + 1):
            for face in itertools.combinations(s, k):
                out.add(frozenset(face))
    return out


@dataclass(frozen=True)
class SimplicialComplex:
    """An abstract simplicial complex: a face-closed set of vertex sets."""

    simplices: frozenset[Simplex]

    @classmethod
    def from_simplices(cls, simplices: Iterable[Iterable[Vertex]]) -> "SimplicialComplex":
        return cls(frozenset(_closure(simplices)))

    @property
    def vertices(self) -> set[Vertex]:
        return {v for s in self.simplices if len(s) == 1 for v in s}

    @property
    def dimension(self) -> int:
        return max((len(s) - 1 for s in self.simplices), default=-1)

    def euler_characteristic(self) -> int:
        """χ from simplex counts — independent of any homology computation."""
        return sum((-1) ** (len(s) - 1) for s in self.simplices)

    def betti(self, max_dimension: int = 2) -> list[int]:
        """Betti numbers β0..β_max_dimension (over Z/2, via GUDHI)."""
        if not self.simplices:
            return [0] * (max_dimension + 1)
        index = {v: i for i, v in enumerate(sorted(self.vertices, key=repr))}
        if _GUDHI_AVAILABLE:
            st = gudhi.SimplexTree()
            for s in self.simplices:
                st.insert(sorted(index[v] for v in s), filtration=0.0)
            st.compute_persistence(persistence_dim_max=True)
            raw = list(st.betti_numbers())
        else:
            raw = _betti_numpy(self.simplices, index, max_dimension)
        return (raw + [0] * (max_dimension + 1))[: max_dimension + 1]

    def components(self) -> list[set[Vertex]]:
        """Connected components as vertex sets (union-find on edges)."""
        parent = {v: v for v in self.vertices}

        def find(v):
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        for s in self.simplices:
            if len(s) == 2:
                a, b = tuple(s)
                parent[find(a)] = find(b)
        groups: dict[Vertex, set[Vertex]] = {}
        for v in self.vertices:
            groups.setdefault(find(v), set()).add(v)
        return list(groups.values())


def _betti_numpy(simplices, index, max_dimension) -> list[int]:  # pragma: no cover
    """Fallback rank computation over Z/2 when GUDHI is unavailable."""
    by_dim: dict[int, list[tuple[int, ...]]] = {}
    for s in simplices:
        by_dim.setdefault(len(s) - 1, []).append(tuple(sorted(index[v] for v in s)))

    def rank_gf2(m: np.ndarray) -> int:
        m = m.copy() % 2
        r = 0
        for c in range(m.shape[1]):
            piv = next((i for i in range(r, m.shape[0]) if m[i, c]), None)
            if piv is None:
                continue
            m[[r, piv]] = m[[piv, r]]
            for i in range(m.shape[0]):
                if i != r and m[i, c]:
                    m[i] ^= m[r]
            r += 1
        return r

    ranks = {}
    for k in range(1, max_dimension + 2):
        rows, cols = by_dim.get(k - 1, []), by_dim.get(k, [])
        if not rows or not cols:
            ranks[k] = 0
            continue
        pos = {s: i for i, s in enumerate(rows)}
        d = np.zeros((len(rows), len(cols)), dtype=np.uint8)
        for j, s in enumerate(cols):
            for face in itertools.combinations(s, k):
                d[pos[face], j] = 1
        ranks[k] = rank_gf2(d)
    return [len(by_dim.get(k, [])) - ranks.get(k, 0) - ranks.get(k + 1, 0)
            for k in range(max_dimension + 1)]


@dataclass
class PushoutResult:
    """K_C plus the structure maps and the Mayer-Vietoris bookkeeping."""

    complex: SimplicialComplex
    j_a: dict[Vertex, Vertex]                 # vertex map K_A -> K_C
    j_b: dict[Vertex, Vertex]                 # vertex map K_B -> K_C
    shared: SimplicialComplex                 # K_I, as embedded in K_C
    collapsed: list[Simplex] = field(default_factory=list)  # extra identifications
    betti: list[int] = field(default_factory=list)
    predicted_betti: list[int] | None = None  # Mayer-Vietoris prediction (β0, β1)
    kernel_phi0: int = 0                      # dim ker(H0(K_I) -> H0(K_A) ⊕ H0(K_B))

    @property
    def is_homotopy_pushout(self) -> bool:
        """True when Mayer-Vietoris applies (no simplices beyond K_I were merged)."""
        return not self.collapsed


class PushoutError(ValueError):
    pass


def _rank_phi0(
    k_a: SimplicialComplex, k_b: SimplicialComplex,
    shared_a: list[Vertex], shared_b: list[Vertex], k_i: SimplicialComplex,
) -> int:
    """Rank of φ0 = (i_A*, i_B*) : H0(K_I) -> H0(K_A) ⊕ H0(K_B), over Q."""
    comps_i = k_i.components()
    comps_a = k_a.components()
    comps_b = k_b.components()
    comp_of_a = {v: n for n, c in enumerate(comps_a) for v in c}
    comp_of_b = {v: n for n, c in enumerate(comps_b) for v in c}
    m = np.zeros((len(comps_a) + len(comps_b), len(comps_i)))
    for col, comp in enumerate(comps_i):
        x = next(iter(comp))  # x is a K_I vertex, i.e. an index into the shared lists
        m[comp_of_a[shared_a[x]], col] = 1
        m[len(comps_a) + comp_of_b[shared_b[x]], col] = 1
    return int(np.linalg.matrix_rank(m)) if m.size else 0


def glue(
    k_a: SimplicialComplex,
    k_b: SimplicialComplex,
    shared: Mapping[Vertex, Vertex] | Iterable[tuple[Vertex, Vertex]],
    shared_simplices: Iterable[Iterable[int]] | None = None,
    strict: bool = False,
    max_dimension: int = 2,
) -> PushoutResult:
    """
    Pushout of K_A <- K_I -> K_B.

    Parameters
    ----------
    shared
        Pairs (a, b): vertex ``a`` of K_A is identified with vertex ``b`` of K_B.
        These pairs are the vertices of K_I (indexed 0..n-1 in the given order).
    shared_simplices
        Higher simplices of K_I, as tuples of indices into ``shared``. Each must
        exist in both K_A and K_B. Default: K_I is discrete (vertices only).
    strict
        Raise ``PushoutError`` if the quotient identifies simplices that are not
        in K_I (i.e. the result is not the Mayer-Vietoris pushout).
    """
    pairs = list(shared.items()) if isinstance(shared, Mapping) else list(shared)
    shared_a = [a for a, _ in pairs]
    shared_b = [b for _, b in pairs]
    if len(set(shared_a)) != len(pairs) or len(set(shared_b)) != len(pairs):
        raise PushoutError("shared vertex maps must be injective (i_A, i_B are monomorphisms)")
    missing = ({a for a in shared_a} - k_a.vertices) | ({b for b in shared_b} - k_b.vertices)
    if missing:
        raise PushoutError(f"shared vertices not present in the complexes: {missing}")

    i_simplices =[tuple(s) for s in (shared_simplices or [])] + [(n,) for n in range(len(pairs))]
    k_i = SimplicialComplex.from_simplices(i_simplices)
    for s in k_i.simplices:
        if frozenset(shared_a[n] for n in s) not in k_a.simplices:
            raise PushoutError(f"K_I simplex {sorted(s)} is not a simplex of K_A")
        if frozenset(shared_b[n] for n in s) not in k_b.simplices:
            raise PushoutError(f"K_I simplex {sorted(s)} is not a simplex of K_B")

    # Disjoint union, then identify i_A(x) ~ i_B(x). Shared vertices get ("I", n).
    j_a = {v: ("A", v) for v in k_a.vertices}
    j_b = {v: ("B", v) for v in k_b.vertices}
    for n, (a, b) in enumerate(pairs):
        j_a[a] = ("I", n)
        j_b[b] = ("I", n)

    img_a = {frozenset(j_a[v] for v in s) for s in k_a.simplices}
    img_b = {frozenset(j_b[v] for v in s) for s in k_b.simplices}
    img_i = {frozenset(("I", n) for n in s) for s in k_i.simplices}
    k_c = SimplicialComplex(frozenset(img_a | img_b))

    collapsed = sorted(
        ((img_a & img_b) - img_i), key=lambda s: (len(s), sorted(map(repr, s)))
    )
    if collapsed:
        msg = (f"pushout identified {len(collapsed)} simplex(es) beyond K_I "
               f"(e.g. {sorted(collapsed[0], key=repr)}); Mayer-Vietoris does not apply. "
               "Subdivide, or add these simplices to K_I.")
        if strict:
            raise PushoutError(msg)
        logger.warning(msg)

    betti = k_c.betti(max_dimension)
    rank_phi0 = _rank_phi0(k_a, k_b, shared_a, shared_b, k_i)
    ker_phi0 = len(k_i.components()) - rank_phi0

    predicted = None
    beta_i = k_i.betti(max_dimension)
    if not collapsed and all(b == 0 for b in beta_i[1:]):
        # H_k(K_I) = 0 for k >= 1, so the sequence reads
        #   0 -> H1(A)⊕H1(B) -> H1(C) -> H0(I) -φ0-> H0(A)⊕H0(B) -> H0(C) -> 0
        # and splits (ker φ0 is free).
        ba, bb = k_a.betti(max_dimension), k_b.betti(max_dimension)
        predicted = [ba[0] + bb[0] - rank_phi0, ba[1] + bb[1] + ker_phi0]

    return PushoutResult(
        complex=k_c, j_a=j_a, j_b=j_b,
        shared=SimplicialComplex(frozenset(img_i)),
        collapsed=collapsed, betti=betti,
        predicted_betti=predicted, kernel_phi0=ker_phi0,
    )


def complex_from_points(
    points: np.ndarray, max_edge_length: float, max_dimension: int = 2,
) -> SimplicialComplex:
    """
    The Vietoris-Rips complex of a point cloud at a single scale.

    Vertices are row indices into ``points``. Use the same cutoff the concept's
    invariants were computed at (``InvariantProfile.max_edge_length``) so the
    complex has the concept's reported Betti numbers.
    """
    if not _GUDHI_AVAILABLE:  # pragma: no cover
        raise RuntimeError("complex_from_points requires GUDHI")
    rips = gudhi.RipsComplex(points=np.asarray(points).tolist(), max_edge_length=max_edge_length)
    st = rips.create_simplex_tree(max_dimension=max_dimension + 1)
    return SimplicialComplex(frozenset(frozenset(s) for s, f in st.get_simplices()
                                       if f <= max_edge_length))
