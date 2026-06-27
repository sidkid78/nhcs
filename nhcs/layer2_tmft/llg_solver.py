"""
Stubs for full physics solvers (deferred to post-Milestone-2).
MuMax3 LLG, FEniCSx Q-tensor, Navier-Stokes.
"""
from __future__ import annotations
import logging, numpy as np
logger = logging.getLogger(__name__)

class LLGSolver:
    """Stub: returns zero magnetisation field."""
    def solve(self, B_grid: np.ndarray, dt: float = 1e-3, n_steps: int = 100) -> np.ndarray:
        logger.debug("LLGSolver stub returning zeros.")
        return np.zeros_like(B_grid)

class QTensorSolver:
    """Stub: returns isotropic Q-tensor (identity * 1/3)."""
    def solve(self, B_grid: np.ndarray) -> np.ndarray:
        logger.debug("QTensorSolver stub returning isotropic Q.")
        shape = B_grid.shape[:3] + (3, 3)
        Q = np.zeros(shape)
        for i in range(3):
            Q[..., i, i] = 1.0 / 3.0
        return Q

class NavierStokesSolver:
    """Stub: returns zero velocity field."""
    def solve(self, Q: np.ndarray) -> np.ndarray:
        logger.debug("NavierStokesSolver stub returning zeros.")
        return np.zeros(Q.shape[:3] + (3,))
