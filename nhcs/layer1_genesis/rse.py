"""
Recursive Synthesis Engine (RSE).

Generates Pure Relational Topologies through iterative stochastic seeding,
tensor-morphism refinement, and attractor-state stabilisation.

MRO normalisation (run_002 fix):
  After each step the cloud is recentered at the origin and rescaled to unit
  mean distance. Without both operations:
    - Centroid drift: Q@D transforms move the centroid exponentially far from
      origin over 500 iterations (E[log stretch] > 0).
    - Float64 cancellation: once centroid > 1e14, pts - centroid loses all
      precision and GUDHI returns garbage topology.
  Both translation and uniform scaling are topological invariants — Betti
  numbers are preserved exactly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

import numpy as np

from nhcs.layer1_genesis.invariants import (
    InvariantProfile,
    compute_betti,
    topological_complexity_score,
)
from nhcs.layer1_genesis.prt import ENode, HypergraphStore, RelationalDistinction

logger = logging.getLogger(__name__)


@dataclass
class CandidateConcept:
    """An RSE output before AIAN filtering and ICVP validation."""
    store: HypergraphStore
    point_cloud: np.ndarray      # (N, d)
    invariant: InvariantProfile
    iteration: int
    rng_seed: int


class TopologicalProgenitor:
    """Seeds the initial simplicial complex as a standard-normal point cloud."""

    def __init__(
        self,
        n_points_range: tuple[int, int] = (20, 40),
        dimension_range: tuple[int, int] = (2, 5),
        rng: np.random.Generator | None = None,
    ) -> None:
        self.n_points_range = n_points_range
        self.dimension_range = dimension_range
        self.rng = rng or np.random.default_rng()

    def seed(self) -> tuple[np.ndarray, HypergraphStore]:
        n = self.rng.integers(*self.n_points_range)
        d = self.rng.integers(*self.dimension_range)
        points = self.rng.standard_normal((n, d))

        store = HypergraphStore()
        for coord in points:
            store.add_node(ENode(manifold_coords=coord))

        logger.debug("RSE seed: shape=%s nodes=%d", points.shape, store.n_nodes())
        return points, store


class MorphicRecursiveOperator:
    """
    Applies tensor morphisms: rotation + stretch + noise, then normalises.

    Normalisation (two steps, both required):
      1. Recenter — subtract mean so centroid is at origin. Prevents the
         centroid from drifting away under cumulative Q@D transforms.
      2. Rescale — divide by mean distance so scale stays bounded at 1.0.
         Prevents float64 precision loss from large absolute coordinates.
    Both steps preserve Betti numbers (topological invariants).
    """

    def __init__(
        self,
        noise_scale: float = 0.05,
        max_stretch: float = 1.5,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.noise_scale = noise_scale
        self.max_stretch = max_stretch
        self.rng = rng or np.random.default_rng()

    def apply(self, points: np.ndarray) -> np.ndarray:
        n, d = points.shape
        Q, _ = np.linalg.qr(self.rng.standard_normal((d, d)))
        stretch = self.rng.uniform(1.0 / self.max_stretch, self.max_stretch, size=d)
        D = np.diag(stretch)
        noise = self.rng.standard_normal((n, d)) * self.noise_scale

        transformed = (points @ Q @ D) + noise

        # Step 1: recenter — centroid moves to origin
        centered = transformed - transformed.mean(axis=0)

        # Step 2: rescale — mean distance from origin becomes 1.0
        mean_dist = np.linalg.norm(centered, axis=1).mean()
        if mean_dist > 1e-8:
            centered = centered / mean_dist

        logger.debug("MRO: shape=%s pre_scale=%.3e", points.shape, mean_dist)
        return centered


class InvariantValidator:
    """
    Fitness: rejects trivial configs. Requires β₁ ≥ 1.
    With MRO normalisation, complexity_score is in [0, ~10].
    """

    def __init__(
        self,
        min_complexity: float = 0.3,
        min_persistence: float = 0.05,
        max_dimension: int = 2,
    ) -> None:
        self.min_complexity = min_complexity
        self.min_persistence = min_persistence
        self.max_dimension = max_dimension

    def validate(self, points: np.ndarray) -> tuple[bool, InvariantProfile]:
        profile = compute_betti(points, max_dimension=self.max_dimension)

        if sum(profile.betti[1:]) == 0:
            return False, profile

        if profile.complexity_score < self.min_complexity:
            return False, profile

        if profile.persistence_pairs:
            finite = [
                p.lifetime for p in profile.persistence_pairs
                if p.lifetime < float("inf") and p.lifetime > self.min_persistence
            ]
            if not finite:
                return False, profile

        return True, profile


class RecursiveSynthesisEngine:
    """Orchestrates Progenitor → MRO loop → Validator → CandidateConcepts."""

    def __init__(
        self,
        n_seed_complexes: int = 20,
        max_iterations: int = 500,
        complexity_threshold: float = 0.3,
        persistence_threshold: float = 0.05,
        rng_seed: int = 42,
    ) -> None:
        self.rng = np.random.default_rng(rng_seed)
        self.progenitor = TopologicalProgenitor(rng=self.rng)
        self.mro = MorphicRecursiveOperator(rng=self.rng)
        self.validator = InvariantValidator(
            min_complexity=complexity_threshold,
            min_persistence=persistence_threshold,
        )
        self.n_seed_complexes = n_seed_complexes
        self.max_iterations = max_iterations

    def run(self) -> list[CandidateConcept]:
        candidates: list[CandidateConcept] = []

        for seed_idx in range(self.n_seed_complexes):
            points, store = self.progenitor.seed()
            best_points = points
            best_profile: InvariantProfile | None = None
            best_score = -float("inf")

            for _ in range(self.max_iterations):
                points = self.mro.apply(points)
                valid, profile = self.validator.validate(points)
                if valid and profile.complexity_score > best_score:
                    best_score = profile.complexity_score
                    best_points = points.copy()
                    best_profile = profile

            if best_profile is not None and best_profile.complexity_score > 0:
                for node, coord in zip(store.all_nodes(), best_points):
                    node.manifold_coords = coord

                candidates.append(CandidateConcept(
                    store=store,
                    point_cloud=best_points,
                    invariant=best_profile,
                    iteration=self.max_iterations,
                    rng_seed=seed_idx,
                ))

        logger.info("RSE produced %d/%d valid candidates.", len(candidates), self.n_seed_complexes)
        return candidates

    def stream(self) -> Iterator[CandidateConcept]:
        while True:
            yield from self.run()
