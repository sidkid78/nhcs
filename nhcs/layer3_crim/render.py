"""
Open3D-based Hopf field renderer.

Falls back to a terminal text summary when:
  - Open3D is not installed
  - Running on Windows (OffscreenRenderer requires EGL, Linux only)
  - Point cloud is empty
"""

from __future__ import annotations

import logging
import platform

import numpy as np

from nhcs.schemas import PhysicalRealization

logger = logging.getLogger(__name__)

_ON_WINDOWS = platform.system() == "Windows"

try:
    import open3d as o3d  # type: ignore
    _O3D_AVAILABLE = not _ON_WINDOWS   # EGL not available on Windows
    if _ON_WINDOWS:
        logger.debug("open3d imported but headless rendering skipped on Windows (no EGL).")
except ImportError:
    _O3D_AVAILABLE = False
    logger.debug("open3d not available — renderer will use text stub.")


class HopfFieldRenderer:
    """
    Renders a PhysicalRealization as a coloured point cloud.

    On Windows (no EGL), always uses text fallback — this avoids the
    repeated stereoscopic-material warnings from Filament/OpenGL.
    """

    def __init__(self, output_dir: str = "renders", headless: bool = True) -> None:
        self.output_dir = output_dir
        self.headless = headless

    def render(self, realization: PhysicalRealization, filename: str | None = None) -> str:
        """Render or summarise. Returns PNG path or summary string."""
        if _O3D_AVAILABLE and self.headless:
            try:
                import os
                os.makedirs(self.output_dir, exist_ok=True)
                fname  = filename or f"{self.output_dir}/{realization.concept_id[:8]}_hopf.png"
                pts    = realization.vertices_array()
                if pts.shape[0] > 0:
                    pcd = o3d.geometry.PointCloud()
                    pcd.points = o3d.utility.Vector3dVector(pts.astype(np.float64))
                    vis = o3d.visualization.rendering.OffscreenRenderer(800, 600)
                    mat = o3d.visualization.rendering.MaterialRecord()
                    mat.shader = "defaultUnlit"
                    mat.point_size = 5.0
                    vis.scene.add_geometry("hopf", pcd, mat)
                    vis.scene.camera.look_at([0, 0, 0], [0.3, 0.3, 0.3], [0, 1, 0])
                    img = vis.render_to_image()
                    o3d.io.write_image(fname, img)
                    del vis
                    logger.info("Rendered Hopf field → %s", fname)
                    return fname
            except RuntimeError as exc:
                logger.debug("OffscreenRenderer failed (%s) — text fallback.", exc)

        summary = (
            f"[Hopf] {realization.concept_id[:8]} "
            f"freq={realization.target_frequency_hz:.1f}Hz "
            f"B={realization.mean_b_field_mt:.2f}mT "
            f"err={realization.charge_error_pct:.1f}%"
        )
        logger.debug(summary)
        return summary
