"""
Hidden objects in R^4 with Betti numbers known by construction.

Every object is centred, scaled to fit the unit ball, and given a random
rotation in O(4), so no coordinate axis is special and an explorer cannot read
the answer off an axis-aligned slice. Betti numbers are over a field of
characteristic 0 (rational): the Klein bottle is (1,1,0) and RP^2 is (1,0,0),
even though over Z/2 they would look like a torus and a sphere.

The suite is chosen so that the probes can decide it: a slab tiling recovers
the Euler characteristic exactly (see probes.py), so every object is pinned down
by its number of pieces, its dimension and chi, except that orientability is
undecidable when chi is even and not 2 (torus vs Klein bottle; genus-2 vs a
non-orientable surface of chi -2). Higher-genus and non-orientable surfaces are
connected sums, glued with a round tube in R^4.

Surfaces are the real test. A generic 3D slice of a surface in R^4 is a curve,
and a generic projection to R^3 has self-intersections, so neither probe shows
the topology directly. Curves are controls: their projections to R^3 are
generically embeddings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.spatial import cKDTree

from nhcs.explorer.topology import voxel_downsample


@dataclass
class Hidden4D:
    name: str
    points: np.ndarray            # (N, 4), centred, max norm 1, randomly posed
    betti: list[int]              # [b0, b1, b2] over Q
    intrinsic_dim: int            # 1 = curve(s), 2 = surface(s)
    orientable: bool | None       # None for curves
    spacing: float                # sampling scale: 95th pct of the 6th-neighbour distance
    note: str = ""
    meta: dict = field(default_factory=dict)


def _grid(n_u: int, n_v: int):
    u = np.linspace(0, 2 * math.pi, n_u, endpoint=False)
    v = np.linspace(0, 2 * math.pi, n_v, endpoint=False)
    return np.meshgrid(u, v, indexing="ij")


def _random_rotation(rng: np.random.Generator) -> np.ndarray:
    q, r = np.linalg.qr(rng.standard_normal((4, 4)))
    return q * np.sign(np.diag(r))


def _finish(name, pts, betti, dim, orientable, rng, note="", pose=True) -> Hidden4D:
    pts = np.asarray(pts, float)
    pts = pts - pts.mean(0)
    pts = pts / np.linalg.norm(pts, axis=1).max()
    if pose:
        pts = pts @ _random_rotation(rng).T
    d, _ = cKDTree(pts).query(pts, k=7)
    return Hidden4D(name, pts, list(betti), dim, orientable, float(np.percentile(d[:, 6], 95)), note)


# Rips scale used for every topological measurement, as a multiple of the
# sampling scale. Verified: every object in SUITE reproduces its known Betti
# numbers at 2.5x and 4x (and fails at 1.5x, where sampling holes show).
RESOLUTION = 3.0


# --- curves (controls) -------------------------------------------------------

def circle(rng, n=400):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return _finish("circle", np.stack([np.cos(t), np.sin(t), 0 * t, 0 * t], 1), [1, 1, 0], 1, None, rng)


def hopf_link(rng, n=400):
    """Two Hopf fibres of S^3: great circles that are linked in S^3."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    a = np.stack([np.cos(t), np.sin(t), 0 * t, 0 * t], 1)
    b = np.stack([0 * t, 0 * t, np.cos(t), np.sin(t)], 1)
    return _finish("hopf_link", np.vstack([a, b]), [2, 2, 0], 1, None, rng,
                   note="two disjoint circles (linked in S^3)")


def theta_wedge(rng, n=300):
    """Three circles sharing one point (a bouquet of three circles), in three different 2-planes."""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)[1:]
    loops = []
    planes = [(0, 1), (1, 2), (2, 3)]
    for i, j in planes:
        p = np.zeros((len(t), 4))
        p[:, i] = 1 - np.cos(t)
        p[:, j] = np.sin(t)
        loops.append(p)
    pts = np.vstack([np.zeros((1, 4))] + loops)
    return _finish("bouquet_3_circles", pts, [1, 3, 0], 1, None, rng)


# --- surfaces ----------------------------------------------------------------

def sphere(rng, n=110):
    """Round S^2 in a 3-plane of R^4 (posing tilts that 3-plane)."""
    k = n * n
    i = np.arange(k) + 0.5
    th = np.arccos(1 - 2 * i / k)
    ph = math.pi * (1 + 5 ** 0.5) * i
    pts = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th), 0 * th], 1)
    return _finish("sphere", pts, [1, 0, 1], 2, True, rng)


def clifford_torus(rng, n=130):
    u, v = _grid(n, n)
    pts = np.stack([np.cos(u), np.sin(u), np.cos(v), np.sin(v)], -1).reshape(-1, 4) / math.sqrt(2)
    return _finish("clifford_torus", pts, [1, 2, 1], 2, True, rng)


def klein_bottle(rng, n=130, R=1.0, r=0.45):
    """The standard embedding of the Klein bottle in R^4 (it has none in R^3)."""
    u, v = _grid(n, n)
    pts = np.stack([(R + r * np.cos(v)) * np.cos(u), (R + r * np.cos(v)) * np.sin(u),
                    r * np.sin(v) * np.cos(u / 2), r * np.sin(v) * np.sin(u / 2)], -1).reshape(-1, 4)
    return _finish("klein_bottle", pts, [1, 1, 0], 2, False, rng,
                   note="non-orientable; over Z/2 its Betti numbers would match a torus")


def projective_plane(rng, n=110):
    """RP^2 embedded in R^4 by the Veronese-type map (x,y,z) -> (x^2-y^2, xy, xz, yz) on S^2."""
    k = n * n
    i = np.arange(k) + 0.5
    th = np.arccos(1 - 2 * i / k)
    ph = math.pi * (1 + 5 ** 0.5) * i
    x, y, z = np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)
    pts = np.stack([x * x - y * y, x * y, x * z, y * z], 1)
    return _finish("projective_plane", pts, [1, 0, 0], 2, False, rng,
                   note="non-orientable; rational Betti numbers match a point")


def torus_and_sphere(rng):
    """A Clifford torus and a small sphere, disjoint."""
    t = clifford_torus(np.random.default_rng(1), n=110).points
    k = 2500
    i = np.arange(k) + 0.5
    th = np.arccos(1 - 2 * i / k)
    ph = math.pi * (1 + 5 ** 0.5) * i
    s = 0.35 * np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th), 0 * th], 1)
    s = s + np.array([2.2, 0, 0, 0])
    return _finish("torus_plus_sphere", np.vstack([t, s]), [2, 2, 2], 2, True, rng,
                   note="two components")


# --- connected sums ----------------------------------------------------------

def _frame(pts: np.ndarray, p: np.ndarray, out: np.ndarray) -> np.ndarray:
    """Orthonormal frame at p: row 0 = ``out`` made normal to the surface, rows 1-2 = tangent plane."""
    nb = pts[cKDTree(pts).query_ball_point(p, 0.15)] - p
    t = np.linalg.svd(nb, full_matrices=False)[2][:2]
    out = out - t.T @ (t @ out)
    out = out / np.linalg.norm(out)
    t = t - np.outer(t @ out, out)
    q, _ = np.linalg.qr(np.column_stack([out, t.T, np.eye(4)]))
    F = q[:, :4].T
    if F[0] @ out < 0:
        F[0] = -F[0]
    return F


def _connect(A: np.ndarray, B: np.ndarray, rho: float = 0.3, L: float = 0.5, cell: float = 0.035) -> np.ndarray:
    """
    Connected sum A # B in R^4. A is moved so its support point in direction e1
    sits at the origin with outward normal +e1 (so A lies in x1 <= 0); B so a
    support point sits at (L,0,0,0) facing -e1 (B lies in x1 >= L). A disc of
    radius rho is cut from each and the two boundary circles are joined by the
    round tube {(s, rho cos t, rho sin t, 0)}, which meets nothing else.
    """
    e1 = np.array([1.0, 0, 0, 0])
    p = A[np.argmax(A @ e1)]
    A2 = (A - p) @ _frame(A, p, e1).T
    d = np.random.default_rng(0).standard_normal(4)
    d /= np.linalg.norm(d)
    q = B[np.argmax(B @ d)]
    FB = _frame(B, q, d)
    FB[0] = -FB[0]
    B2 = (B - q) @ FB.T + L * e1
    A2 = A2[np.linalg.norm(A2, axis=1) > rho]
    B2 = B2[np.linalg.norm(B2 - L * e1, axis=1) > rho]
    nth, ns = 2 * int(2 * math.pi * rho / cell), 2 * int(L / cell) + 8
    th, s = np.meshgrid(np.linspace(0, 2 * math.pi, nth, endpoint=False), np.linspace(-0.06, L + 0.06, ns), indexing="ij")
    tube = np.stack([s, rho * np.cos(th), rho * np.sin(th), 0 * s], -1).reshape(-1, 4)
    return np.vstack([A2, tube, B2])


def _uniform(pts: np.ndarray, cell: float) -> np.ndarray:
    """Normalise to the unit ball, then even out the density (the tube is sampled more finely)."""
    pts = pts - pts.mean(0)
    return voxel_downsample(pts / np.linalg.norm(pts, axis=1).max(), cell)


_CACHE: dict[str, np.ndarray] = {}


def _cached(key: str, build: Callable[[], np.ndarray]) -> np.ndarray:
    if key not in _CACHE:
        _CACHE[key] = build()
    return _CACHE[key]


def _torus_piece():
    return clifford_torus(np.random.default_rng(0)).points


def genus_2(rng):
    pts = _cached("genus_2", lambda: _uniform(_connect(_torus_piece(), _torus_piece()), 0.014))
    return _finish("genus_2", pts, [1, 4, 1], 2, True, rng, note="T # T, chi = -2")


def genus_3(rng):
    pts = _cached("genus_3", lambda: _uniform(_connect(_connect(_torus_piece(), _torus_piece()), _torus_piece()), 0.012))
    return _finish("genus_3", pts, [1, 6, 1], 2, True, rng, note="T # T # T, chi = -4")


def dyck_surface(rng):
    """RP^2 # T^2 (Dyck's surface): chi = -1, so it must be non-orientable."""
    def build():
        P = 2.0 * projective_plane(np.random.default_rng(0), n=150).points
        return _uniform(_connect(P, _torus_piece()), 0.014)
    return _finish("dyck_surface", _cached("dyck", build), [1, 2, 0], 2, False, rng,
                   note="RP^2 # T^2; rational Betti numbers (1,2,0)")


SUITE: dict[str, Callable[[np.random.Generator], Hidden4D]] = {
    "circle": circle,
    "hopf_link": hopf_link,
    "bouquet_3_circles": theta_wedge,
    "sphere": sphere,
    "clifford_torus": clifford_torus,
    "klein_bottle": klein_bottle,
    "projective_plane": projective_plane,
    "torus_plus_sphere": torus_and_sphere,
    "genus_2": genus_2,
    "genus_3": genus_3,
    "dyck_surface": dyck_surface,
}


def make(name: str, seed: int = 0) -> Hidden4D:
    return SUITE[name](np.random.default_rng(seed))


def euler(betti) -> int:
    return int(betti[0] - betti[1] + betti[2])


def orientability_decidable(obj: Hidden4D) -> bool:
    """
    Can b0, dimension and chi settle orientability? Only for one connected
    surface with odd chi (then non-orientable) or chi = 2 (the sphere).
    """
    if obj.intrinsic_dim != 2 or obj.betti[0] != 1:
        return False
    x = euler(obj.betti)
    return x % 2 == 1 or x == 2
