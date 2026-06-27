"""
Biot-Savart coil field solver for the 12-channel dodecahedral array.

Given a current vector (12,) produces B(x,y,z) at arbitrary query points.

Performance: fully vectorised with numpy — no Python loops over grid points.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "coil_array_dodec12.yaml"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _build_coil_dl_pts(
    centre: np.ndarray,
    normal: np.ndarray,
    radius: float,
    n_turns: int,
    mesh_res: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Pre-compute loop points and dl vectors for a single coil.

    Returns
    -------
    pts : (mesh_res, 3)   — points on the coil loop
    dls : (mesh_res, 3)   — differential current elements (scaled by I later)
    """
    # Local orthonormal frame
    perp = np.array([-normal[1], normal[0], 0.0])
    if np.linalg.norm(perp) < 1e-6:
        perp = np.array([0.0, -normal[2], normal[1]])
    perp /= np.linalg.norm(perp)
    perp2 = np.cross(normal, perp)

    thetas = np.linspace(0, 2 * np.pi, mesh_res, endpoint=False)
    dth = 2 * np.pi / mesh_res

    cos_t = np.cos(thetas)[:, None]   # (M,1)
    sin_t = np.sin(thetas)[:, None]

    # Points on loop: centre + R*(cos(t)*perp + sin(t)*perp2)
    pts = centre + radius * (cos_t * perp + sin_t * perp2)  # (M,3)

    # dl = R * dθ * (-sin(t)*perp + cos(t)*perp2)  scaled by n_turns
    dls = radius * dth * n_turns * (-sin_t * perp + cos_t * perp2)  # (M,3)

    return pts, dls


class CoilFieldSolver:
    """
    Fully vectorised Biot-Savart solver for a dodecahedral coil array.

    Each coil is pre-computed as (pts, dls) arrays so that field evaluation
    is a matrix multiply — no Python loops over grid or theta.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        cfg = yaml.safe_load(open(config_path or _CONFIG_PATH))
        self.radius = cfg["coil_radius_m"]
        self.n_channels = cfg["n_channels"]
        self.n_turns = cfg["wire_turns"]
        self.mesh_res = cfg["biot_savart"]["mesh_resolution"]
        self.face_normals = np.array(cfg["face_normals"], dtype=np.float64)
        norms = np.linalg.norm(self.face_normals, axis=1, keepdims=True)
        self.face_normals /= norms
        self.centres = self.face_normals * self.radius

        # Pre-build coil geometry: list of (pts, dls) per channel
        self._coil_pts: list[np.ndarray] = []
        self._coil_dls: list[np.ndarray] = []
        for i in range(self.n_channels):
            pts, dls = _build_coil_dl_pts(
                self.centres[i], self.face_normals[i],
                self.radius, self.n_turns, self.mesh_res,
            )
            self._coil_pts.append(pts)   # (M, 3)
            self._coil_dls.append(dls)   # (M, 3)

        # Stack into (n_channels, mesh_res, 3)
        self._all_pts = np.stack(self._coil_pts, axis=0)   # (C, M, 3)
        self._all_dls = np.stack(self._coil_dls, axis=0)   # (C, M, 3)

        logger.debug(
            "CoilFieldSolver: %d channels, mesh_res=%d, coil_radius=%.3f m",
            self.n_channels, self.mesh_res, self.radius,
        )

    # ------------------------------------------------------------------
    # Core vectorised Biot-Savart
    # ------------------------------------------------------------------

    def field_at_batch(
        self,
        query_pts: np.ndarray,   # (N, 3)
        currents: np.ndarray,    # (C,)
    ) -> np.ndarray:
        """
        Vectorised Biot-Savart for N query points and C coils.

        Returns (N, 3) B-field array in Tesla.

        Broadcasting plan:
          query_pts : (N, 1, 1, 3)
          coil_pts  : (1, C, M, 3)
          r_vec     : (N, C, M, 3)
          dls       : (1, C, M, 3) * currents (C,) → (1, C, M, 3)
        """
        MU0_OVER_4PI = 1e-7

        q = query_pts[:, None, None, :]     # (N, 1, 1, 3)
        p = self._all_pts[None, :, :, :]    # (1, C, M, 3)
        r_vec = q - p                        # (N, C, M, 3)
        r_mag = np.linalg.norm(r_vec, axis=-1, keepdims=True)  # (N, C, M, 1)
        r_mag = np.where(r_mag < 1e-9, 1e-9, r_mag)

        # dl weighted by current: (1, C, M, 3) * (C,) → (N, C, M, 3)
        dl_I = self._all_dls[None] * currents[None, :, None, None]  # (1,C,M,3)

        # dl × r_vec / |r|³
        cross = np.cross(dl_I, r_vec)        # (N, C, M, 3)
        dB = cross / (r_mag ** 3)            # (N, C, M, 3)

        # Sum over coils (C) and loop segments (M)
        B = MU0_OVER_4PI * dB.sum(axis=(1, 2))   # (N, 3)
        return B

    def field_at(self, query_pt: np.ndarray, currents: np.ndarray) -> np.ndarray:
        """Single-point query (kept for API compatibility)."""
        return self.field_at_batch(query_pt[None], currents)[0]

    def field_grid(
        self,
        grid_size: int = 16,
        sphere_radius_m: float = 0.05,
        currents: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Evaluate B on a 3D grid inside the sphere.

        Returns (grid_size, grid_size, grid_size, 3) — vectorised, no Python loops.
        """
        if currents is None:
            currents = np.ones(self.n_channels)

        coords = np.linspace(-sphere_radius_m, sphere_radius_m, grid_size)
        gx, gy, gz = np.meshgrid(coords, coords, coords, indexing='ij')
        all_pts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)  # (N,3)

        # Mask: only evaluate inside sphere
        r2 = (all_pts ** 2).sum(axis=1)
        mask = r2 <= sphere_radius_m ** 2

        B_flat = np.zeros((len(all_pts), 3))
        if mask.any():
            B_flat[mask] = self.field_at_batch(all_pts[mask], currents)

        return B_flat.reshape(grid_size, grid_size, grid_size, 3)
