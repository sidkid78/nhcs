"""
Multi-Dimensional Phenomenological Vector Space (MDPVS).

Projects Hopf field tensors into a low-dim space aligned with the NSM prime
coordinate system.

Milestone 1: random projection stub.

Field scaling fix (run_006):
  Raw Biot-Savart output is in Tesla (1-4 mT = 1e-3 T scale). Without scaling,
  W @ mean_tensor ≈ 1e-3 for all concepts, so tanh(1e-3) ≈ 0.001, giving
  temporal ≈ 0.5 (MOMENT) always regardless of topology or field strength.
  Scaling by 1000 (T → mT) puts projection inputs in the ~0.7–1.5 range
  where tanh produces meaningful variation, spreading prime activations across
  BEFORE / NOW / MOMENT / AFTER and making spatial directions concept-specific.
"""

from __future__ import annotations
import numpy as np

# Raw Biot-Savart is in Tesla; scale to mT so projection inputs are O(1)
# rather than O(1e-3) where tanh is effectively zero for all concepts.
_FIELD_SCALE = 10000.0   # T → mT


class PhenomenologicalVectorSpace:
    """
    Linear projection: per-vertex field tensor (9D) -> MDPVS (3D).

    Outputs (spatial_3d, temporal, magnitude) where:
      spatial_3d : (3,) unit vector on S^2
      temporal   : float in [0,1]
      magnitude  : float >= 0
    """

    def __init__(self, input_dim: int = 9, rng_seed: int = 0) -> None:
        rng = np.random.default_rng(rng_seed)
        self._W = rng.standard_normal((3, input_dim)).astype(np.float32)
        self._W /= np.linalg.norm(self._W, axis=1, keepdims=True) + 1e-8

    def project_full(
        self,
        field_tensors: np.ndarray,
    ) -> tuple[np.ndarray, float, float]:
        """
        Project mean field tensor into (spatial_3d, temporal, magnitude).

        Field tensors are scaled from Tesla to mT before projection so the
        projection inputs are O(1) rather than O(1e-3), enabling tanh to
        produce meaningful temporal variation between concepts.

        Parameters
        ----------
        field_tensors : (N, 9) float array — one row per grid vertex (Tesla)

        Returns
        -------
        (spatial_3d, temporal, magnitude)
        """
        if field_tensors.size == 0 or len(field_tensors) == 0:
            return np.zeros(3, dtype=np.float32), 0.5, 0.0

        # Scale T → mT; project mean tensor
        scaled      = field_tensors.astype(np.float64) * _FIELD_SCALE
        mean_tensor = scaled.mean(axis=0).astype(np.float32)   # (9,)
        raw         = self._W @ mean_tensor                     # (3,)

        spatial_3d = raw.copy()
        norm = np.linalg.norm(spatial_3d)
        if norm > 1e-6:
            spatial_3d = spatial_3d / norm

        temporal  = float(np.clip(0.5 + 0.5 * np.tanh(raw[1]), 0.0, 1.0))
        magnitude = float(np.abs(np.mean(np.abs(raw))))

        return spatial_3d.astype(np.float32), temporal, magnitude

    def project(self, field_tensors: np.ndarray) -> np.ndarray:
        """Legacy single-vector output."""
        sp, tmp, mag = self.project_full(field_tensors)
        return np.array([sp[0], tmp, mag], dtype=np.float32)
