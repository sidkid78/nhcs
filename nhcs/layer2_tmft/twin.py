"""
Digital Twin — orchestrates the four TMFT solvers and emits PhysicalRealization.
"""

from __future__ import annotations

import logging
import time

import numpy as np

from nhcs.layer2_tmft.chamber import SapphireChamber
from nhcs.layer2_tmft.coil_field import CoilFieldSolver
from nhcs.layer2_tmft.controller import HopfionController
from nhcs.layer2_tmft.photonics import emission_spectrum, wavelength_to_rgb
from nhcs.layer2_tmft.topology_to_field import TopologyToField
from nhcs.schemas import ConceptTarget, EmissionSpectrum, PhysicalRealization

logger = logging.getLogger(__name__)

# Controller grid for the spectral solver's quadratic forms. This is
# DELIBERATELY FIXED and independent of both `self.grid_size` (the CRIM
# tensor-extraction grid) and default.yaml's `layer2.twin.grid_size`
# (the render-fidelity grid, 16 dev / 64 fidelity). The concept->field
# mapping must be reproducible: the same Betti vector has to yield the
# same currents whether the pipeline runs at dev or fidelity resolution,
# otherwise concept identities drift silently between runs (exactly what
# the field_map tag exists to prevent). The spectral forms are built once
# per grid size and cached; each per-concept solve is a closed-form
# eigenvector mix (microseconds).
#
# gs=12 chosen as the fixed reference: the spectrum has converged in
# structure by gs=12 (icosahedral multiplets 3/2+3/3/1), c_lo stable to
# ~1.5% and the mid-triplet to <0.5% vs finer grids; only the top mode
# shifts (~68 at gs12 -> ~65 asymptotic) and that is absorbed by reading
# anchors from this same grid (see _spectrum_anchors). gs=4 had only 8
# interior points (~40% drift) and is obsolete now that speed is a
# non-issue.
_CTRL_GRID_SIZE = 12

# Saturation constant for the I_f -> complexity-target map (mirrors the
# TPMM hyperbolic maps f(I_f) and L(I_L), which use K = 5). K_C = 4 puts
# I_f = 4 at half-span and I_f = 12 at 75% of the achievable spectrum.
_K_C = 4.0


class DigitalTwin:
    """
    Step a ConceptTarget through the full TMFT pipeline and produce
    a PhysicalRealization.

    grid_size : voxels per axis for CRIM field tensor extraction (default 8).
    The controller always uses the FIXED _CTRL_GRID_SIZE for its spectral
    forms, independent of this grid and of the render-fidelity grid, so
    the concept->field mapping is reproducible across fidelity settings.
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
        # Cache the (c_lo, c_hi) mapping anchors from the FIXED control
        # grid once, so the I_f -> complexity-target map is stable for the
        # life of the twin and never picks up render-grid changes.
        self._c_lo, self._c_hi = self._spectrum_anchors()

    def _spectrum_anchors(self) -> tuple[float, float]:
        """
        (c_lo, c_hi) for the I_f -> target map, read from the fixed control
        grid's exact eigenvalue spectrum rather than hardcoded.

        c_lo = first STRUCTURED eigenvalue: the coil array's icosahedral
        symmetry produces three near-zero modes (near-uniform interior
        fields) that carry no spatial structure; index 3 is the first
        genuinely structured mode. c_hi = top of the spectrum. Reading
        these at runtime means the map self-corrects if the geometry,
        coil count, or control grid ever changes.
        """
        spec = self.controller.spectrum(_CTRL_GRID_SIZE)
        n_null = int(np.sum(spec < 1e-2 * spec[-1]))   # count near-zero modes
        lo_idx = min(n_null, len(spec) - 2)
        return float(spec[lo_idx]), float(spec[-1])

    def step(self, concept: ConceptTarget) -> PhysicalRealization:
        t0 = time.perf_counter()

        # 1. Topology → target physical parameters
        mapping = self.t2f.translate(concept)
        target_freq = mapping["target_freq_hz"]
        target_wl   = mapping["target_wavelength_nm"]

        # 2. Map Betti I_f to a field-complexity target across the FULL
        # achievable spectrum (the generalized eigenvalue range of the
        # coil array), via hyperbolic saturation like the TPMM maps:
        #     target(I_f) = c_lo + (c_hi - c_lo) * I_f / (K_C + I_f)
        # Anchors are read once from the fixed control grid's exact
        # spectrum (self._c_lo/_c_hi), NOT hardcoded -- so switching the
        # render grid between dev (16) and fidelity (64) cannot shift the
        # concept->field mapping. Different beta1/beta2 profiles -> different
        # targets AND eigenvector variants -> near-orthogonal fields.
        b = concept.signature.betti
        I_f = b[1] + 2 * (b[2] if len(b) > 2 else 0)
        target_charge = self._c_lo + (self._c_hi - self._c_lo) * I_f / (_K_C + I_f)

        # 3. Closed-form spectral solve (exact within achievable spectrum);
        # variant=I_f cycles orthogonal eigenvectors inside degenerate
        # symmetry multiplets for maximal concept distinctness.
        currents = self.controller.compute_currents(
            target_freq, target_charge, grid_size=_CTRL_GRID_SIZE, variant=I_f
        )

        # 4. Evaluate achieved complexity
        achieved  = self.controller.achieved_charge(currents, grid_size=_CTRL_GRID_SIZE)
        error_pct = abs(achieved - target_charge) / (abs(target_charge) + 1e-6) * 100

        # 5. Full-resolution field for CRIM tensor extraction
        B_grid   = self.coil.field_grid(self.grid_size, self.chamber.inner_radius_m, currents)
        mean_b_mt = float(np.linalg.norm(B_grid, axis=-1).mean() * 1000)

        # 6. Emission spectrum (note: distinct name from the eigen-spectrum
        # above -- do NOT rebind `spec`, which callers may rely on later)
        emission = EmissionSpectrum(
            **emission_spectrum(target_wl, target_freq, self.emission_duration)
        )

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
            emission_spectrum=emission,
            mesh_vertices=pts.tolist(),
            mesh_field_tensors=field_tensors_9.tolist(),
            mean_b_field_mt=mean_b_mt,
        )
