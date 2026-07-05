"""Tests for the knowledge graph engine."""

import pytest
from codetruth.engine.graph import (
    KnowledgeGraphEngine,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)


class TestKnowledgeGraphEngine:
    """Test suite for KnowledgeGraphEngine."""

    @pytest.fixture
    def engine(self, tmp_path):
        db_path = str(tmp_path / "test_graph.db")
        return KnowledgeGraphEngine(db_path)

    def test_add_node(self, engine):
        """Test adding a node."""
        node = GraphNode(
            node_id="n1",
            name="calculate_sum",
            node_type=NodeType.FUNCTION,
            file_path="src/math.py",
            line_start=10,
            line_end=20,
            signature="def calculate_sum(a, b)",
        )
        added = engine.add_node(node)
        assert added.node_id == "n1"
        assert engine.get_node("n1") is not None

    def test_add_edge(self, engine):
        """Test adding an edge."""
        engine.add_node(GraphNode("n1", "func_a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "func_b", NodeType.FUNCTION, "b.py", 1, 5))

        edge = GraphEdge(
            edge_id="e1",
            source_id="n1",
            target_id="n2",
            edge_type=EdgeType.CALLS,
        )
        added = engine.add_edge(edge)
        assert added.edge_id == "e1"

    def test_query_node(self, engine):
        """Test querying nodes by name."""
        engine.add_node(GraphNode("n1", "calculate_sum", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "calculate_avg", NodeType.FUNCTION, "a.py", 10, 15))
        engine.add_node(GraphNode("n3", "UserModel", NodeType.CLASS, "b.py", 1, 20))

        results = engine.query_node("calculate")
        assert len(results) == 2

        results = engine.query_node("UserModel", NodeType.CLASS)
        assert len(results) == 1

    def test_get_neighbors(self, engine):
        """Test getting neighboring nodes."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.FUNCTION, "a.py", 10, 15))
        engine.add_node(GraphNode("n3", "c", NodeType.FUNCTION, "a.py", 20, 25))

        engine.add_edge(GraphEdge("e1", "n1", "n2", EdgeType.CALLS))
        engine.add_edge(GraphEdge("e2", "n2", "n3", EdgeType.CALLS))

        neighbors = engine.get_neighbors("n1", depth=1)
        assert len(neighbors) >= 1

        neighbors_deep = engine.get_neighbors("n1", depth=2)
        assert len(neighbors_deep) >= 2

    def test_find_dependencies(self, engine):
        """Test finding dependencies."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.FUNCTION, "a.py", 10, 15))

        engine.add_edge(GraphEdge("e1", "n1", "n2", EdgeType.CALLS))

        deps = engine.find_dependencies("n1")
        assert len(deps) == 1
        assert deps[0].node_id == "n2"

    def test_find_dependents(self, engine):
        """Test finding dependents."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.FUNCTION, "a.py", 10, 15))

        engine.add_edge(GraphEdge("e1", "n1", "n2", EdgeType.CALLS))

        deps = engine.find_dependents("n2")
        assert len(deps) == 1
        assert deps[0].node_id == "n1"

    def test_find_path(self, engine):
        """Test finding shortest path."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.FUNCTION, "a.py", 10, 15))
        engine.add_node(GraphNode("n3", "c", NodeType.FUNCTION, "a.py", 20, 25))

        engine.add_edge(GraphEdge("e1", "n1", "n2", EdgeType.CALLS))
        engine.add_edge(GraphEdge("e2", "n2", "n3", EdgeType.CALLS))

        path = engine.find_path("n1", "n3")
        assert path is not None
        assert path == ["n1", "n2", "n3"]

    def test_find_path_no_connection(self, engine):
        """Test finding path when no connection exists."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.FUNCTION, "b.py", 1, 5))

        path = engine.find_path("n1", "n2")
        assert path is None

    def test_ai_generated_nodes(self, engine):
        """Test filtering AI-generated nodes."""
        engine.add_node(GraphNode("n1", "human_code", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode(
            "n2", "ai_code", NodeType.FUNCTION, "a.py", 10, 15, is_ai_generated=True
        ))

        ai_nodes = engine.get_ai_generated_nodes()
        assert len(ai_nodes) == 1
        assert ai_nodes[0].node_id == "n2"

    def test_export_graph(self, engine):
        """Test graph export."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_edge(GraphEdge("e1", "n1", "n1", EdgeType.CALLS))

        exported = engine.export_graph()
        assert "nodes" in exported
        assert "edges" in exported
        assert len(exported["nodes"]) == 1
        assert len(exported["edges"]) == 1

    def test_stats(self, engine):
        """Test graph statistics."""
        engine.add_node(GraphNode("n1", "a", NodeType.FUNCTION, "a.py", 1, 5))
        engine.add_node(GraphNode("n2", "b", NodeType.CLASS, "a.py", 10, 15, is_ai_generated=True))

        stats = engine.stats()
        assert stats["total_nodes"] == 2
        assert stats["ai_generated_nodes"] == 1
        assert stats["ai_generated_pct"] == 50.0