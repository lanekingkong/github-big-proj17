"""
Code Knowledge Graph Engine - builds AST-based dependency maps.

Inspired by: CodeGraph (21K stars - reduces token usage 57%),
             SuperMemory (memory graph with semantic relationships)
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class NodeType(str, Enum):
    """Types of nodes in the code knowledge graph."""
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    INTERFACE = "interface"


class EdgeType(str, Enum):
    """Types of edges (relationships) between nodes."""
    CONTAINS = "contains"
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    DECORATES = "decorates"


@dataclass
class GraphNode:
    """A node in the code knowledge graph."""

    node_id: str
    name: str
    node_type: NodeType
    file_path: str
    line_start: int
    line_end: int
    signature: str = ""
    docstring: str = ""
    language: str = "unknown"
    complexity_score: float = 0.0
    is_ai_generated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "docstring": self.docstring,
            "language": self.language,
            "complexity_score": self.complexity_score,
            "is_ai_generated": self.is_ai_generated,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """An edge connecting two nodes in the knowledge graph."""

    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }


@dataclass
class GraphSnapshot:
    """A snapshot of the knowledge graph at a point in time."""

    snapshot_id: str
    project_root: str
    created_at: datetime
    node_count: int
    edge_count: int
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "project_root": self.project_root,
            "created_at": self.created_at.isoformat(),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "stats": self.stats,
        }


class KnowledgeGraphEngine:
    """
    Builds and queries a code knowledge graph.

    Extracts structural information from codebases:
    - Classes, functions, methods, variables
    - Import/export relationships
    - Call graphs and dependency chains
    - Inheritance hierarchies

    This provides AI tools with structured project understanding,
    dramatically reducing token consumption vs raw file scanning.
    """

    def __init__(self, db_path: str, project_root: str = "."):
        self._db_path = db_path
        self._project_root = Path(project_root).resolve()
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._adjacency: dict[str, set[str]] = {}
        self._snapshots: list[GraphSnapshot] = []

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add a node to the graph."""
        self._nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = set()
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Add an edge to the graph."""
        self._edges[edge.edge_id] = edge
        if edge.source_id not in self._adjacency:
            self._adjacency[edge.source_id] = set()
        self._adjacency[edge.source_id].add(edge.target_id)
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def query_node(self, name: str, node_type: Optional[NodeType] = None) -> list[GraphNode]:
        """Search for nodes by name and optional type."""
        results = []
        for node in self._nodes.values():
            if name.lower() in node.name.lower():
                if node_type is None or node.node_type == node_type:
                    results.append(node)
        return results

    def get_neighbors(self, node_id: str, depth: int = 1) -> list[GraphNode]:
        """Get neighboring nodes up to a given depth."""
        if node_id not in self._adjacency:
            return []
        visited = {node_id}
        frontier = set(self._adjacency[node_id])
        for _ in range(depth - 1):
            new_frontier = set()
            for nid in frontier:
                if nid not in visited and nid in self._adjacency:
                    new_frontier.update(self._adjacency[nid])
            visited.update(frontier)
            frontier = new_frontier
        visited.update(frontier)
        return [self._nodes[nid] for nid in visited if nid in self._nodes]

    def find_dependencies(self, node_id: str) -> list[GraphNode]:
        """Find all dependencies (outgoing edges) for a node."""
        deps = set()
        for edge in self._edges.values():
            if edge.source_id == node_id:
                deps.add(edge.target_id)
        return [self._nodes[nid] for nid in deps if nid in self._nodes]

    def find_dependents(self, node_id: str) -> list[GraphNode]:
        """Find all dependents (incoming edges) for a node."""
        deps = set()
        for edge in self._edges.values():
            if edge.target_id == node_id:
                deps.add(edge.source_id)
        return [self._nodes[nid] for nid in deps if nid in self._nodes]

    def find_path(self, source_id: str, target_id: str) -> Optional[list[str]]:
        """Find the shortest path between two nodes using BFS."""
        if source_id not in self._adjacency or target_id not in self._adjacency:
            return None
        queue = [[source_id]]
        visited = {source_id}
        while queue:
            path = queue.pop(0)
            current = path[-1]
            if current == target_id:
                return path
            for neighbor in self._adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def get_ai_generated_nodes(self) -> list[GraphNode]:
        """Get all nodes marked as AI-generated."""
        return [n for n in self._nodes.values() if n.is_ai_generated]

    def export_graph(self) -> dict[str, Any]:
        """Export the full graph as a dictionary."""
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
            "project_root": str(self._project_root),
        }

    def stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        ai_nodes = len(self.get_ai_generated_nodes())
        type_counts: dict[str, int] = {}
        for node in self._nodes.values():
            t = node.node_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "ai_generated_nodes": ai_nodes,
            "ai_generated_pct": round(ai_nodes / len(self._nodes) * 100, 1) if self._nodes else 0,
            "by_type": type_counts,
            "snapshot_count": len(self._snapshots),
        }