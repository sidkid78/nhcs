"""
Knot reading for slice curves, and knotted 2-spheres in R^4 built as meshes.

A slice of a surface in R^4 by a hyperplane is a link in R^3. This module
turns closed 3D polylines into knot diagrams (a generic projection to a plane,
with over/under from the third coordinate), and reads them with knot Floer
homology (the knot_floer_homology package; no Sage needed):

    Alexander polynomial (graded Euler characteristic), Seifert genus,
    fiberedness, tau (tells a trefoil from its mirror image).

Small knots are named by matching those invariants against a table built
from SnapPy's knot tables; composite or larger knots are reported by their
invariants alone.

Knotted spheres are made the classical ways, so their knot types are known:

    Artin spinning: an arc K in the half-space x3 >= 0 with its ends on
        x3 = 0, spun by (x1, x2, x3 cos t, x3 sin t). Knotted when K is.
    Zeeman twist-spinning: while spinning by t, the knotted ball the arc
        passes through is also rotated by n t about the arc's axis. The
        1-twist-spun knot of anything is UNKNOTTED (Zeeman 1965), although
        its slices are knotted; n >= 2 twist-spins of nontrivial knots are knotted.

Surfaces are triangle meshes, so a slice is computed exactly as closed polylines.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

# --- closed curves ---------------------------------------------------------

def trefoil_curve(n: int = 600) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    # the (2,3) torus knot: fat lobes, so cutting it open leaves well-separated ends
    return np.stack([(2 + np.cos(3 * t)) * np.cos(2 * t), (2 + np.cos(3 * t)) * np.sin(2 * t), np.sin(3 * t)], 1)


def figure_eight_curve(n: int = 600) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([(2 + np.cos(2 * t)) * np.cos(3 * t), (2 + np.cos(2 * t)) * np.sin(3 * t), np.sin(4 * t)], 1)


def unknot_curve(n: int = 300) -> np.ndarray:
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([2 * np.cos(t), 2 * np.sin(t), 0 * t], 1)


CURVES = {"unknot": unknot_curve, "trefoil": trefoil_curve, "figure_eight": figure_eight_curve}

# --- diagrams: closed polylines -> PD code ---------------------------------

def _rot(rng):
    q, r = np.linalg.qr(rng.standard_normal((3, 3)))
    return q * np.sign(np.diag(r))


def _seg_cross(P, Q):
    """All proper crossings between 2D segment sets P[i]=(a,b), Q[j]=(c,d). Returns i, j, s, u (params)."""
    a, b = P[:, 0], P[:, 1]
    c, d = Q[:, 0], Q[:, 1]
    r = b - a
    s_ = d - c
    den = r[:, None, 0] * s_[None, :, 1] - r[:, None, 1] * s_[None, :, 0]
    w = c[None, :, :] - a[:, None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (w[..., 0] * s_[None, :, 1] - w[..., 1] * s_[None, :, 0]) / den
        u = (w[..., 0] * r[:, None, 1] - w[..., 1] * r[:, None, 0]) / den
    ok = (np.abs(den) > 1e-14) & (t > 0) & (t < 1) & (u > 0) & (u < 1)
    i, j = np.nonzero(ok)
    return i, j, t[i, j], u[i, j]


def diagram(polys: list[np.ndarray], seed: int = 0, chunk: int = 1500):
    """
    Project closed polylines to a generic plane and find crossings.
    Returns (pd_code, crossings) where crossings carry the component indices
    and sign. pd_code follows the KnotTheory/spherogram convention:
    (incoming under, then counterclockwise).
    """
    R = _rot(np.random.default_rng(seed))
    comps = [np.asarray(p, float) @ R.T for p in polys]
    segs = []  # per component: (k, 2, 3)
    for p in comps:
        segs.append(np.stack([p, np.roll(p, -1, 0)], 1))
    events = [[] for _ in comps]  # (seg index + t, crossing id)
    xs = []
    for ci in range(len(comps)):
        for cj in range(ci, len(comps)):
            A, B = segs[ci], segs[cj]
            for a0 in range(0, len(A), chunk):
                Ab = A[a0:a0 + chunk]
                i, j, t, u = _seg_cross(Ab[:, :, :2], B[:, :, :2])
                i = i + a0
                for ii, jj, tt, uu in zip(i, j, t, u):
                    if ci == cj and (jj <= ii or abs(int(ii) - int(jj)) <= 1 or {int(ii), int(jj)} == {0, len(A) - 1}):
                        continue
                    za = A[ii, 0, 2] + tt * (A[ii, 1, 2] - A[ii, 0, 2])
                    zb = B[jj, 0, 2] + uu * (B[jj, 1, 2] - B[jj, 0, 2])
                    da = A[ii, 1, :2] - A[ii, 0, :2]
                    db = B[jj, 1, :2] - B[jj, 0, :2]
                    k = len(xs)
                    a_over = za > zb
                    xs.append({"comp": (ci, cj), "over": 0 if a_over else 1, "dirs": (da, db)})
                    events[ci].append((ii + tt, k, 0))
                    events[cj].append((jj + uu, k, 1))
    # arcs: label the stretch after each event; incoming label = label of previous stretch
    label = 0
    inc = {}  # (crossing, strand) -> (in_label, out_label)
    first_label = []
    for ev in events:
        ev.sort()
        if not ev:
            continue
        base = label
        m = len(ev)
        for e_idx, (_, k, st) in enumerate(ev):
            inc[(k, st)] = (base + (e_idx - 1) % m, base + e_idx)
        label += m
    pd = []
    for k, x in enumerate(xs):
        o = x["over"]
        u_ = 1 - o
        under_in, under_out = inc[(k, u_)]
        over_in, over_out = inc[(k, o)]
        du, dv = x["dirs"][u_], x["dirs"][o]
        ang0 = math.atan2(-du[1], -du[0])
        ends = [(ang0, under_in), (math.atan2(du[1], du[0]), under_out),
                (math.atan2(-dv[1], -dv[0]), over_in), (math.atan2(dv[1], dv[0]), over_out)]
        ends.sort(key=lambda e: (e[0] - ang0) % (2 * math.pi))
        pd.append(tuple(e[1] for e in ends))
        x["sign"] = 1 if (du[0] * dv[1] - du[1] * dv[0]) > 0 else -1
    return pd, xs


# --- invariants --------------------------------------------------------------

def _hfk(pd):
    from knot_floer_homology import pd_to_hfk
    return pd_to_hfk(pd)


def _simplify(pd):
    import spherogram
    if not pd:
        return []
    L = spherogram.Link(pd)
    L.simplify("global")
    return L.PD_code()


def alexander_from_ranks(ranks: dict) -> list[int]:
    """Symmetrised Alexander polynomial coefficients, lowest power first, from HFK ranks {(A, M): r}."""
    coef: dict[int, int] = {}
    for (a, m), r in ranks.items():
        coef[a] = coef.get(a, 0) + (-1) ** (m % 2) * r
    if not coef:
        return [1]
    lo, hi = min(coef), max(coef)
    c = [coef.get(a, 0) for a in range(lo, hi + 1)]
    while len(c) > 1 and c[0] == 0:
        c = c[1:]
    while len(c) > 1 and c[-1] == 0:
        c = c[:-1]
    if c[len(c) // 2] < 0 or (c and c[0] < 0):
        c = [-x for x in c] if sum(c) < 0 else c
    return c


def knot_invariants(pd) -> dict:
    """Invariants of one knot diagram (PD code; [] = unknot)."""
    pd = _simplify(pd) if pd else []
    if not pd:
        return {"crossings": 0, "alexander": [1], "genus": 0, "fibered": True, "tau": 0, "name": "unknot"}
    h = _hfk(pd)
    inv = {"crossings": len(pd), "alexander": alexander_from_ranks(h["ranks"]), "genus": h["seifert_genus"],
           "fibered": h["fibered"], "tau": h["tau"]}
    inv["name"] = name_for(inv)
    return inv


@lru_cache(maxsize=1)
def _table():
    import snappy
    rows = []
    names = ["3_1", "4_1", "5_1", "5_2", "6_1", "6_2", "6_3", "7_1", "7_2", "7_3", "7_4", "7_5", "7_6", "7_7"]
    for n in names:
        L = snappy.Link(n)
        for mirror in (False, True):
            K = L.mirror() if mirror else L
            h = _hfk(K.PD_code())
            key = (tuple(alexander_from_ranks(h["ranks"])), h["seifert_genus"], h["tau"])
            label = n if not mirror else "m" + n
            if h["tau"] == 0 and mirror:
                continue  # amphichiral as far as these invariants see
            rows.append((key, label))
    # a few composites that slices of spun knots produce
    for a, b, lab in [("3_1", "3_1", "3_1 # 3_1"), ("3_1", "m3_1", "3_1 # m3_1"), ("4_1", "4_1", "4_1 # 4_1")]:
        La = snappy.Link(a.lstrip("m"))
        Lb = snappy.Link(b.lstrip("m"))
        if a.startswith("m"):
            La = La.mirror()
        if b.startswith("m"):
            Lb = Lb.mirror()
        K = La.connected_sum(Lb)
        h = _hfk(K.PD_code())
        rows.append(((tuple(alexander_from_ranks(h["ranks"])), h["seifert_genus"], h["tau"]), lab))
        if h["tau"] != 0:
            rows.append(((tuple(alexander_from_ranks(h["ranks"])), h["seifert_genus"], -h["tau"]), "m(" + lab + ")"))
    return rows


def name_for(inv: dict) -> str | None:
    key = (tuple(inv["alexander"]), inv["genus"], inv["tau"])
    hits = [lab for k, lab in _table() if k == key]
    return " or ".join(hits) if hits else None


def read_link(polys: list[np.ndarray], seed: int = 0) -> dict:
    """
    Knot types of each component of a link in R^3 and the pairwise linking
    numbers (absolute values: components carry no preferred orientation).
    """
    comps = []
    for p in polys:
        pd, _ = diagram([p], seed=seed)
        comps.append(knot_invariants(pd))
    lk = []
    if len(polys) > 1:
        _, xs = diagram(polys, seed=seed)
        tot: dict[tuple[int, int], int] = {}
        for x in xs:
            a, b = x["comp"]
            if a != b:
                tot[(a, b)] = tot.get((a, b), 0) + x["sign"]
        lk = [[a, b, abs(v) // 2] for (a, b), v in sorted(tot.items()) if abs(v) // 2]
    return {"components": comps, "linking": lk}


# --- knotted arcs and spun spheres ------------------------------------------

def _resample(path: np.ndarray, step: float) -> np.ndarray:
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.stack([np.interp(s, d, path[:, k]) for k in range(path.shape[1])], 1)


def long_knot(curve: np.ndarray, cut: float = 0.04) -> tuple[np.ndarray, float]:
    """
    Cut a closed curve open at its highest point (max y), removing a fraction
    ``cut`` of it on each side, and route the ends to the poles (0, -R, 0) and
    (0, R, 0) of a ball of radius R about the origin: in the plane z = 0 and
    outside the diagram, so no crossings are added and the closure outside the
    ball is the original knot. Ends and routes keep a clearance of about
    0.2 x the diagram's radius from everything else (no near-touching sheets
    once the arc is spun).
    Returns (path from south pole to north pole, R).
    """
    c = np.asarray(curve, float)
    c = c - np.r_[c[:, :2].mean(0), 0]
    n = len(c)
    p = int(np.argmax(c[:, 1]))
    c[:, 0] -= c[p, 0]
    k = max(2, int(cut * n))
    body = np.roll(c, -(p + k), axis=0)[: n - 2 * k + 1]  # starts after p, ends before p
    if body[0, 0] > body[-1, 0]:
        body = body[::-1]
    left, right = body[0], body[-1]
    rmax = np.linalg.norm(c[:, :2], axis=1).max()
    ro, R = 1.5 * rmax, 1.8 * rmax
    top = c[p, 1] + 0.2 * rmax          # the left end's route turns left here
    top2 = top + 0.25 * rmax            # the right end turns towards the north pole here
    xo = -math.sqrt(max(ro**2 - top**2, 0.0))
    # clockwise from the bottom, round the LEFT side, to the upper left (never over the top,
    # where the north leg runs)
    arc_t = np.linspace(-math.pi / 2, math.atan2(top, xo) - 2 * math.pi, 160)
    outer = np.stack([ro * np.cos(arc_t), ro * np.sin(arc_t), 0 * arc_t], 1)  # bottom -> left -> upper left
    path = np.vstack([[[0, -R, 0.0]], outer,
                      [[left[0], top, 0.0], [left[0], left[1] + 0.05 * rmax, 0.5 * left[2]]],
                      body,
                      [[right[0], right[1] + 0.05 * rmax, 0.5 * right[2]], [right[0], top2, 0.0], [0, top2 + 0.15 * rmax, 0.0], [0, R, 0.0]]])
    return path, R


def clearance(path: np.ndarray, scale: float) -> float:
    """Smallest r (as a fraction of scale) at which two points far apart along the path (> 4 r) come within r."""
    from scipy.spatial import cKDTree
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    tree = cKDTree(path)
    for r in np.linspace(0.005, 0.5, 100) * scale:
        pr = tree.query_pairs(r, output_type="ndarray")
        if len(pr) and (np.abs(d[pr[:, 0]] - d[pr[:, 1]]) > 4 * r).any():
            return float(r / scale)
    return 0.5


def spin_arc(curve: np.ndarray, step: float | None = None):
    """
    Arc for spinning, in (X1, X2, X3) with X3 >= 0 and both ends on X3 = 0:
    leg up to the ball's pole, the long knot through the ball (axis along X1),
    leg down. Returns (arc, ball_mask, H, R): ball_mask marks the points that
    twist-spinning rotates; the ball has centre (0, 0, H), radius R.
    """
    lk, R = long_knot(curve)
    H = 1.6 * R
    t = np.stack([lk[:, 1], lk[:, 0], H + lk[:, 2]], 1)  # tangle axis (y) -> X1
    legs_s = np.array([[-R, 0, 0.0], [-R, 0, H]])
    legs_n = np.array([[R, 0, H], [R, 0, 0.0]])
    step = step or R / 60
    parts = [_resample(legs_s, step), _resample(t, step), _resample(legs_n, step)]
    mask = np.r_[np.zeros(len(parts[0]), bool), np.ones(len(parts[1]), bool), np.zeros(len(parts[2]), bool)]
    mask[len(parts[0])] = mask[len(parts[0]) + len(parts[1]) - 1] = False  # poles stay put
    return np.vstack(parts), mask, H, R


def spun_sphere(curve: np.ndarray, twist: int = 0, n_theta: int = 240, step: float | None = None):
    """
    Triangle mesh of the (twist-)spun knot of ``curve`` in R^4.
    Returns (vertices (V, 4), triangles (T, 3)). The arc's two ends become the
    sphere's poles and are merged into single vertices.
    """
    arc, mask, H, R = spin_arc(curve, step)
    ns = len(arc)
    th = np.linspace(0, 2 * math.pi, n_theta, endpoint=False)
    V = np.zeros((ns, n_theta, 4))
    for j, t in enumerate(th):
        a = arc.copy()
        if twist:
            phi = twist * t
            y, z = a[mask, 1], a[mask, 2] - H
            a[mask, 1] = math.cos(phi) * y - math.sin(phi) * z
            a[mask, 2] = H + math.sin(phi) * y + math.cos(phi) * z
        V[:, j] = np.stack([a[:, 0], a[:, 1], a[:, 2] * math.cos(t), a[:, 2] * math.sin(t)], 1)
    idx = np.arange(ns * n_theta).reshape(ns, n_theta)
    idx[0, :] = idx[0, 0]
    idx[-1, :] = idx[-1, 0]
    a_, b_ = idx[:-1, :], np.roll(idx[:-1, :], -1, 1)
    c_, d_ = idx[1:, :], np.roll(idx[1:, :], -1, 1)
    T = np.concatenate([np.stack([a_, c_, d_], -1).reshape(-1, 3), np.stack([a_, d_, b_], -1).reshape(-1, 3)])
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    used, inv = np.unique(T, return_inverse=True)
    return V.reshape(-1, 4)[used], inv.reshape(-1, 3)


def slice_mesh(V: np.ndarray, T: np.ndarray, normal, offset: float) -> list[np.ndarray]:
    """
    Exact cross-section of a triangle mesh by {normal . x = offset}, as closed
    polylines in R^4 (chained through shared mesh edges).
    """
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    f = V @ n - offset
    f[f == 0] = 1e-12
    s = f[T] > 0
    cut = s.any(1) & ~s.all(1)
    TT = T[cut]
    nb: dict = {}
    pts: dict = {}
    for tri in TT:
        es = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if (f[a] > 0) != (f[b] > 0):
                key = (a, b) if a < b else (b, a)
                if key not in pts:
                    t = f[a] / (f[a] - f[b])
                    pts[key] = V[a] + t * (V[b] - V[a])
                es.append(key)
        if len(es) == 2:
            nb.setdefault(es[0], []).append(es[1])
            nb.setdefault(es[1], []).append(es[0])
    seen, loops = set(), []
    for start in nb:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [k for k in nb[cur] if k != prev]
            if not nxt or nxt[0] == start or nxt[0] in seen:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) >= 3:
            loops.append(np.array([pts[k] for k in loop]))
    return loops
