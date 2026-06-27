"""
Inter-layer message schemas (Pydantic v2).

Five bus channels:
  L1 → L2  : ConceptTarget
  L2 → L3  : PhysicalRealization
  L3 → L1  : IntegrationFeedback
  L3 → L2  : RetargetRequest  (lateral — PID freq correction)
  L1 ↔ L1  : ICVPVote         (consensus traffic between validator nodes)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Shared sub-types
# ---------------------------------------------------------------------------

class TopologicalSignature(BaseModel):
    """Compact descriptor of a Pure Relational Topology."""
    betti: list[int] = Field(description="[β0, β1, β2, ...]")
    euler_characteristic: int
    dimension: int
    crossing_number: int = 0
    bridge_index: int = 0
    torus_p: int = 0
    torus_q: int = 0
    genus: int = 0
    persistence_entropy: float = 0.0
    complexity_score: float = 0.0


class MeritScores(BaseModel):
    epistemic_truth: float        # Et ∈ [0,1]
    algorithmic_parsimony: float  # Ap ∈ [0,1]
    mdl_score: float = 0.0
    compression_progress: float = 0.0
    fractal_dimension: float = 0.0
    edge_of_chaos_ratio: float = 0.0
    novelty_score: float = 0.0    # from AIAN


# ---------------------------------------------------------------------------
# L1 → L2 : ConceptTarget
# ---------------------------------------------------------------------------

class ConceptTarget(BaseModel):
    """Emitted by ICVP after a concept reaches supermajority consensus."""
    concept_id: str = Field(default_factory=_new_uuid)
    timestamp: datetime = Field(default_factory=_utcnow)

    # Topological description
    signature: TopologicalSignature
    merit: MeritScores

    # Arousal/valence scalars → drive oscillation freq & colour
    arousal: float = Field(ge=0.0, le=1.0, default=0.5)
    valence: float = Field(ge=-1.0, le=1.0, default=0.0)

    # Hopf map sampled on unit S³ grid — shape (n_points, 4) float32
    # Serialised as nested list for Pydantic; convert via .hopf_map_array()
    hopf_map_grid: list[list[float]] = Field(default_factory=list)

    # Optimisation hints for Layer 2
    max_coil_power_w: float = 100.0
    viscosity_bounds_mpa_s: tuple[float, float] = (8.0, 15.0)
    reconfigure_budget_s: float = 2.0

    def hopf_map_array(self) -> np.ndarray:
        return np.array(self.hopf_map_grid, dtype=np.float32)

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# L2 → L3 : PhysicalRealization
# ---------------------------------------------------------------------------

class EmissionSpectrum(BaseModel):
    """Emission trajectory sampled at ~60 Hz."""
    timestamps_s: list[float]
    wavelength_nm: list[float]
    frequency_hz: list[float]
    intensity: list[float]


class PhysicalRealization(BaseModel):
    """
    Physics boundary — everything past this point is signal-mapping, not physics.
    Layer 3 cannot reach back into the physics solvers.
    """
    concept_id: str
    timestamp: datetime = Field(default_factory=_utcnow)

    # Achieved topological result
    achieved_hopf_charge: float        # dimensionless
    target_hopf_charge: float
    charge_error_pct: float

    # Physical outputs
    target_frequency_hz: float
    target_wavelength_nm: float
    emission_spectrum: EmissionSpectrum

    # Renderable mesh — vertices (N,3) and per-vertex field tensor (N,9)
    # Serialised as nested lists
    mesh_vertices: list[list[float]] = Field(default_factory=list)
    mesh_field_tensors: list[list[float]] = Field(default_factory=list)

    # B-field summary (mean magnitude in mT)
    mean_b_field_mt: float = 0.0

    def vertices_array(self) -> np.ndarray:
        return np.array(self.mesh_vertices, dtype=np.float32)

    def field_tensor_array(self) -> np.ndarray:
        return np.array(self.mesh_field_tensors, dtype=np.float32)

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# L3 → L1 : IntegrationFeedback
# ---------------------------------------------------------------------------

class IntegrationFeedback(BaseModel):
    """Closes the outer loop: updates Layer 1 merit priors."""
    concept_id: str
    timestamp: datetime = Field(default_factory=_utcnow)

    # Time-series (downsampled to feedback_hz)
    cli_series: list[float]          # Cognitive Load Index
    iis_series: list[float]          # Immersion Intensity Score

    # Summary statistics
    bhi: float                        # Biometric Homeostasis Index ∈ [0,1]
    sdr: float                        # Semantic Distance Reduction ∈ [0,1]
    sdr_confidence: float = 0.0

    # Subject type for provenance
    synthetic_subject: bool = True
    n_integration_steps: int = 0


# ---------------------------------------------------------------------------
# L3 → L2 : RetargetRequest  (lateral)
# ---------------------------------------------------------------------------

class RetargetRequest(BaseModel):
    """PID asks Layer 2 to adjust physical output within stability regime."""
    concept_id: str
    timestamp: datetime = Field(default_factory=_utcnow)
    requested_frequency_hz: float
    urgency: float = Field(ge=0.0, le=1.0, default=0.5)

    @field_validator("requested_frequency_hz")
    @classmethod
    def clamp_to_stability_regime(cls, v: float) -> float:
        # Hard guardrail: 15-40 Hz Resonant Stability Regime
        return float(np.clip(v, 15.0, 40.0))


# ---------------------------------------------------------------------------
# L1 ↔ L1 : ICVPVote
# ---------------------------------------------------------------------------

class ICVPVote(BaseModel):
    """Signed vote from a single ICVP validator node."""
    vote_id: str = Field(default_factory=_new_uuid)
    concept_id: str
    validator_did: str
    timestamp: datetime = Field(default_factory=_utcnow)

    approve: bool
    et_score: float
    ap_score: float
    rationale: str = ""
    signature: str = ""              # placeholder for crypto signature
