"""
Digital Twin — orchestrates the four TMFT solvers and emits PhysicalRealization.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from nhcs.layer2_tmft.chamber import SapphireChamber
from nhcs.layer2_tmft.coil_field import CoilFieldSolver
from nhcs.layer2_tmft.controller import HopfionController, _C_MIN, _C_MAX
from nhcs.layer2_tmft.photonics import emission_spectrum, wavelength_to_rgb
from nhcs.layer2_tmft.topology_to_field import TopologyToField
from nhcs.schemas import ConceptTarget, EmissionSpectrum, PhysicalRealization

logger = logging.getLogger(__name__)

# Controller grid: gs=4 (64 points, ~2ms/call).  Beltrami complexity is
# smooth enough that gs=4 and gs=8 converge to the same solution; the 8x
# speed gain over gs=8 is the bottleneck reduction needed for bulk runs.
# CRIM tensor extraction uses self.grid_size (default 8) separately.
_CTRL_GRID_SIZE = 4


class DigitalTwin:
    """
    Step a ConceptTarget through the full TMFT pipeline and produce
    a PhysicalRealization.

    grid_size : voxels per axis for CRIM field tensor extraction (default 8).
    The controller always uses _CTRL_GRID_SIZE=4 internally for speed.
    """

    def __init__(
        self,
        grid_size: int = 8,
        emission_duration_s: float = 1.0,
    ) -> None:
        self.t2f = TopologyToField()
        self.chamber = SapphireChamber()
        self.coil = CoilFieldSolver()
        self.controller = HopfionController(coil_solver=self.coil)
        self.grid_size = grid_size
        self.emission_duration = emission_duration_s

    def step(self, concept: ConceptTarget) -> PhysicalRealization:
        t0 = time.perf_counter()

        # 1. Topology → target physical parameters
        mapping = self.t2f.translate(concept)
        target_freq = mapping["target_freq_hz"]
        target_wl   = mapping["target_wavelength_nm"]

        # 2. Map Betti I_f to Beltrami complexity target.
        # Different β₁/β₂ profiles → different target_charge → different
        # current patterns → different fields → concept-specific projections.
        #   I_f=1 → 8.5,  I_f=2 → 10.5,  I_f=3 → 12.5,
        #   I_f=4 → 14.5, I_f≥5 → 15.0
        b = concept.signature.betti
        I_f = b[1] + 2 * (b[2] if len(b) > 2 else 0)
        target_charge = float(np.clip(_C_MIN + (I_f - 1) * 2.0, _C_MIN, _C_MAX))

        # 3. Optimise coil currents at low resolution (fast: gs=4, ~2ms/call)
        currents = self.controller.compute_currents(
            target_freq, target_charge, grid_size=_CTRL_GRID_SIZE
        )

        # 4. Evaluate achieved complexity
        achieved  = self.controller.achieved_charge(currents, grid_size=_CTRL_GRID_SIZE)
        error_pct = abs(achieved - target_charge) / (abs(target_charge) + 1e-6) * 100

        # 5. Full-resolution field for CRIM tensor extraction
        B_grid   = self.coil.field_grid(self.grid_size, self.chamber.inner_radius_m, currents)
        mean_b_mt = float(np.linalg.norm(B_grid, axis=-1).mean() * 1000)

        # 6. Emission spectrum
        spec = EmissionSpectrum(**emission_spectrum(target_wl, target_freq, self.emission_duration))

        # 7. Per-vertex field tensors for CRIM
        pts = self.chamber.sample_interior_grid(n=8)
        verts_idx = np.round(
            (pts + self.chamber.inner_radius_m)
            / (2 * self.chamber.inner_radius_m)
            * (self.grid_size - 1)
        ).astype(int).clip(0, self.grid_size - 1)
        field_tensors   = B_grid[verts_idx[:, 0], verts_idx[:, 1], verts_idx[:, 2]]
        field_tensors_9 = np.concatenate(
            [field_tensors, np.zeros((len(field_tensors), 6))], axis=1
        )

        dt = time.perf_counter() - t0
        logger.info(
            "DigitalTwin: I_f=%d target_c=%.2f achieved=%.4f err=%.1f%% "
            "B=%.2fmT freq=%.1fHz [%.2fs]",
            I_f, target_charge, achieved, error_pct, mean_b_mt, target_freq, dt,
        )

        return PhysicalRealization(
            concept_id=concept.concept_id,
            achieved_hopf_charge=achieved,
            target_hopf_charge=target_charge,
            charge_error_pct=error_pct,
            target_frequency_hz=target_freq,
            target_wavelength_nm=target_wl,
            emission_spectrum=spec,
            mesh_vertices=pts.tolist(),
            mesh_field_tensors=field_tensors_9.tolist(),
            mean_b_field_mt=mean_b_mt,
        )
