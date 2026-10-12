"""
Multi-Dimensional Phenomenological Vector Space (MDPVS).

Projects Hopf field tensors into a low-dim space aligned with the NSM prime
coordinate system.

Field scaling fix (run_006):
  Raw Biot-Savart output is in Tesla (1-4 mT = 1e-3 T scale). Without scaling,
  W @ mean_tensor ≈ 1e-3 for all concepts, so tanh(1e-3) ≈ 0.001, giving
  temporal ≈ 0.5 (MOMENT) always regardless of topology or field strength.
  Scaling by 1000 (T → mT) puts projection inputs in the ~0.7–1.5 range
  where tanh produces meaningful variation.

Per-vertex projection fix (Thread A, spectral-v2):
  The previous implementation projected the MEAN tensor: raw = W @ mean(tensor).
  For fields with directional structure that cancels under spatial averaging
  (the icosahedral symmetry multiplets are the pathological case), mean(tensor)
  ≈ 0 even though every individual vertex carries an O(1) field. The surviving
  scalar magnitude collapsed to near-zero, and — because magnitude was the only
  channel feeding SDR that varied per concept — SDR flatlined to exactly 0.

  Fix: project every vertex, then aggregate.
    - spatial_3d / temporal : from the MEAN projection (unchanged; linearity
      guarantees mean(W @ t_i) == W @ mean(t_i), so directions match legacy).
    - magnitude : mean of per-vertex projection NORMS — taken BEFORE averaging,
      so structural intensity survives even under perfect directional
      cancellation.
    - variability : structural turbulence, 1 - ||mean_proj|| / mean(||proj_i||).
      0 when all vertices are coherent (THE SAME), → 1 when they cancel
      (OTHER/ELSE). This channel directly encodes the icosahedral-cancellation
      phenomenon that used to destroy the signal.
"""

from __future__ import annotations
import numpy as np

# Raw Biot-Savart is in Tesla; scale to mT so projection inputs are O(1)
# rather than O(1e-3) where tanh is effectively zero for all concepts.
_FIELD_SCALE = 10000.0   # T → mT-ish working units

# Magnitude calibration. mean(||proj_i||) after _FIELD_SCALE lands well above
# tanh's sensitive band for typical fields, saturating MUCH/BIG/VERY for every
# concept. Dividing by _MAG_NORM re-centres the *population* of magnitudes into
# tanh's responsive range so magnitude still discriminates. Like _FIELD_SCALE
# this is a working-units constant, NOT physics; recalibrate against a real
# field-magnitude population before trusting absolute magnitude primes. Concept
# discrimination does not depend on it — variability + target encoding carry
# that load independently.
_MAG_NORM = 12.0


class PhenomenologicalVectorSpace:
    """
    Linear projection: per-vertex field tensor (9D) -> MDPVS.

    Outputs (spatial_3d, temporal, magnitude, variability) where:
      spatial_3d  : (3,) unit vector on S^2
      temporal    : float in [0,1]
      magnitude   : float >= 0   (structural intensity; survives cancellation)
      variability : float in [0,1] (structural turbulence / directional spread)
    """

    def __init__(self, input_dim: int = 9, rng_seed: int = 0) -> None:
        rng = np.random.default_rng(rng_seed)
        self._W = rng.standard_normal((3, input_dim)).astype(np.float32)
        self._W /= np.linalg.norm(self._W, axis=1, keepdims=True) + 1e-8

    def project_full(
        self,
        field_tensors: np.ndarray,
    ) -> tuple[np.ndarray, float, float, float]:
        """
        Project per-vertex field tensors into
        (spatial_3d, temporal, magnitude, variability).

        Parameters
        ----------
        field_tensors : (N, 9) float array — one row per grid vertex (Tesla)

        Returns
        -------
        (spatial_3d, temporal, magnitude, variability)
        """
        if field_tensors.size == 0 or len(field_tensors) == 0:
            return np.zeros(3, dtype=np.float32), 0.5, 0.0, 0.0

        # Scale T → working units; project EVERY vertex.
        scaled = field_tensors.astype(np.float64) * _FIELD_SCALE   # (N, 9)
        proj = scaled @ self._W.T.astype(np.float64)               # (N, 3)

        mean_proj = proj.mean(axis=0)                              # (3,)
        per_vertex_norm = np.linalg.norm(proj, axis=1)             # (N,)
        mean_norm = float(per_vertex_norm.mean())                  # scalar

        # ── spatial direction (identical to legacy: mean projection) ──
        spatial_3d = mean_proj.astype(np.float32).copy()
        norm = np.linalg.norm(spatial_3d)
        if norm > 1e-6:
            spatial_3d = spatial_3d / norm

        # ── temporal (unchanged mapping on mean projection y-component) ──
        temporal = float(np.clip(0.5 + 0.5 * np.tanh(mean_proj[1]), 0.0, 1.0))

        # ── magnitude: structural intensity that survives cancellation ──
        magnitude = mean_norm / _MAG_NORM

        # ── variability: 1 - ||mean_proj|| / mean(||proj_i||) ──
        # coherent field  → ||mean_proj|| ≈ mean_norm → variability ≈ 0
        # cancelling field → ||mean_proj|| ≈ 0        → variability ≈ 1
        variability = float(np.clip(
            1.0 - np.linalg.norm(mean_proj) / (mean_norm + 1e-8),
            0.0, 1.0,
        ))

        return spatial_3d.astype(np.float32), temporal, magnitude, variability

    def project(self, field_tensors: np.ndarray) -> np.ndarray:
        """Legacy single-vector output (spatial_x, temporal, magnitude)."""
        sp, tmp, mag, _var = self.project_full(field_tensors)
        return np.array([sp[0], tmp, mag], dtype=np.float32)
