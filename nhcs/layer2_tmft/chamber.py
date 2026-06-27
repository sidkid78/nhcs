"""
Sapphire sphere boundary conditions and chamber geometry.

Documents the discrepancy between info.md (50 mm) and domain report (100 mm).
Config-driven via colloid_fe3o4.yaml.
"""

from __future__ import annotations
from pathlib import Path
import yaml
import numpy as np

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "colloid_fe3o4.yaml"


def load_chamber_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)["chamber"]


class SapphireChamber:
    """
    Defines the sapphire sphere geometry and enforces boundary conditions.

    NOTE: sphere_diameter_mm defaults to 100 mm (TMFT domain report).
    Override via config if the info.md 50 mm spec is intended.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        cfg = load_chamber_config() if config_path is None else \
              yaml.safe_load(open(config_path))["chamber"]
        self.diameter_mm = cfg["sphere_diameter_mm"]
        self.wall_mm = cfg["wall_thickness_mm"]
        self.radius_m = (self.diameter_mm / 2.0) / 1000.0
        self.inner_radius_m = self.radius_m - self.wall_mm / 1000.0
        self.transmission_pct = cfg["transmission_pct"]

    def is_inside(self, pt: np.ndarray) -> bool:
        """Check if point is inside the inner fluid volume."""
        return bool(np.linalg.norm(pt) <= self.inner_radius_m)

    def clamp_to_interior(self, pts: np.ndarray) -> np.ndarray:
        """Project points outside inner sphere onto its surface."""
        norms = np.linalg.norm(pts, axis=1, keepdims=True)
        mask = norms.ravel() > self.inner_radius_m
        pts[mask] = pts[mask] / norms[mask] * self.inner_radius_m
        return pts

    def sample_interior_grid(self, n: int = 16) -> np.ndarray:
        """Return (n³, 3) grid of points inside the inner sphere."""
        coords = np.linspace(-self.inner_radius_m, self.inner_radius_m, n)
        grid = np.stack(np.meshgrid(coords, coords, coords), axis=-1).reshape(-1, 3)
        inside = np.linalg.norm(grid, axis=1) <= self.inner_radius_m
        return grid[inside]
