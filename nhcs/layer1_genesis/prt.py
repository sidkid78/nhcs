"""
Pure Relational Topology primitives.

Eidetic Nodes (ENodes) are the fundamental relational units.
Relational Distinctions (RDs) are directed, weighted, typed hyperedges.
HypergraphStore wraps NetworkX with hyperedge support.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np


@dataclass
class ENode:
    """
    Eidetic Node — a relational unit with no intrinsic label.

    Identity is defined purely by its position in the relational web
    (isomorphic distance from other nodes), not by any semantic tag.
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Embedding in the Dynamic Embedding Manifold (filled by manifold.py)
    manifold_coords: np.ndarray | None = field(default=None, repr=False)
    # Persistent homology birth-death pair if this node anchors a feature
    persistence_birth: float = 0.0
    persistence_death: float = float("inf")
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def persistence_lifetime(self) -> float:
        return self.persistence_death - self.persistence_birth

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ENode) and self.node_id == other.node_id


@dataclass
class RelationalDistinction:
    """
    Relational Distinction — a directed, weighted, typed hyperedge.

    An RD connects a set of source ENodes to a set of target ENodes,
    representing a morphism in the relational category.
    """
    rd_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sources: list[str] = field(default_factory=list)   # ENode IDs
    targets: list[str] = field(default_factory=list)   # ENode IDs
    weight: float = 1.0
    rd_type: str = "morphism"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.rd_id)


class HypergraphStore:
    """
    Wraps NetworkX DiGraph with hyperedge (RD) support.

    ENodes are graph nodes; RDs that have >1 source or target are
    reified as intermediate "hyperedge" nodes with prefix 'he:'.
    """

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, ENode] = {}
        self._rds: dict[str, RelationalDistinction] = {}

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, node: ENode) -> None:
        self._nodes[node.node_id] = node
        self._g.add_node(node.node_id, enode=node)

    def get_node(self, node_id: str) -> ENode | None:
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[ENode]:
        return list(self._nodes.values())

    # ------------------------------------------------------------------
    # RD / hyperedge management
    # ------------------------------------------------------------------

    def add_rd(self, rd: RelationalDistinction) -> None:
        self._rds[rd.rd_id] = rd
        he_id = f"he:{rd.rd_id}"

        if len(rd.sources) == 1 and len(rd.targets) == 1:
            # Simple directed edge — no reification needed
            self._g.add_edge(
                rd.sources[0], rd.targets[0],
                weight=rd.weight, rd_id=rd.rd_id, rd_type=rd.rd_type,
            )
        else:
            # Hyperedge reification
            self._g.add_node(he_id, is_hyperedge=True, rd_id=rd.rd_id)
            for src in rd.sources:
                self._g.add_edge(src, he_id, weight=rd.weight)
            for tgt in rd.targets:
                self._g.add_edge(he_id, tgt, weight=rd.weight)

    def get_rd(self, rd_id: str) -> RelationalDistinction | None:
        return self._rds.get(rd_id)

    def all_rds(self) -> list[RelationalDistinction]:
        return list(self._rds.values())

    # ------------------------------------------------------------------
    # Graph accessors
    # ------------------------------------------------------------------

    @property
    def graph(self) -> nx.DiGraph:
        return self._g

    def n_nodes(self) -> int:
        return len(self._nodes)

    def n_rds(self) -> int:
        return len(self._rds)

    def adjacency_dict(self) -> dict[str, list[str]]:
        """Compact representation for serialisation."""
        return {n: list(self._g.successors(n)) for n in self._nodes}

    def to_point_cloud(self) -> np.ndarray:
        """
        Return manifold coordinates of all ENodes as an (N,d) array.
        Nodes without coords get zeros.
        """
        coords = []
        for n in self._nodes.values():
            if n.manifold_coords is not None:
                coords.append(n.manifold_coords)
            else:
                coords.append(np.zeros(3))
        return np.stack(coords, axis=0) if coords else np.empty((0, 3))

    def __repr__(self) -> str:
        return f"HypergraphStore(nodes={self.n_nodes()}, rds={self.n_rds()})"
