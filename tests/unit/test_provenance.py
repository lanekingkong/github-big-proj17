"""Tests for the provenance engine."""

import pytest
from codetruth.engine.provenance import (
    ProvenanceEngine,
    ProvenanceEntry,
    ProvenanceReport,
    AIProvider,
    ProvenanceStatus,
)


class TestProvenanceEngine:
    """Test suite for ProvenanceEngine."""

    @pytest.fixture
    def engine(self, tmp_path):
        db_path = str(tmp_path / "test_provenance.db")
        return ProvenanceEngine(db_path)

    def test_record_entry(self, engine):
        """Test recording a provenance entry."""
        entry = engine.record(
            file_path="src/main.py",
            line_start=10,
            line_end=25,
            provider=AIProvider.CLAUDE_CODE,
            model="claude-3-sonnet",
            prompt="Write a function to sort a list",
            tokens_used=150,
        )
        assert entry is not None
        assert entry.file_path == "src/main.py"
        assert entry.provider == AIProvider.CLAUDE_CODE
        assert entry.status == ProvenanceStatus.GENERATED
        assert entry.tokens_used == 150

    def test_update_status(self, engine):
        """Test updating entry status."""
        entry = engine.record(
            file_path="src/main.py",
            line_start=1,
            line_end=10,
            provider=AIProvider.CURSOR,
            model="gpt-4",
            prompt="Create a class",
        )
        updated = engine.update_status(
            entry.entry_id,
            ProvenanceStatus.REVIEWED,
            trust_score=85.0,
        )
        assert updated is not None
        assert updated.status == ProvenanceStatus.REVIEWED
        assert updated.trust_score == 85.0

    def test_get_entry(self, engine):
        """Test retrieving an entry by ID."""
        entry = engine.record(
            file_path="src/utils.py",
            line_start=5,
            line_end=15,
            provider=AIProvider.GITHUB_COPILOT,
            model="gpt-4",
            prompt="Helper function",
        )
        retrieved = engine.get_entry(entry.entry_id)
        assert retrieved is not None
        assert retrieved.file_path == "src/utils.py"

    def test_get_nonexistent_entry(self, engine):
        """Test retrieving a non-existent entry."""
        assert engine.get_entry("nonexistent") is None

    def test_get_file_entries(self, engine):
        """Test retrieving entries by file path."""
        engine.record("a.py", 1, 5, AIProvider.CLAUDE_CODE, "m1", "p1")
        engine.record("a.py", 10, 20, AIProvider.CURSOR, "m2", "p2")
        engine.record("b.py", 1, 3, AIProvider.CODEX, "m3", "p3")

        entries = engine.get_file_entries("a.py")
        assert len(entries) == 2

        entries_b = engine.get_file_entries("b.py")
        assert len(entries_b) == 1

    def test_generate_report(self, engine):
        """Test generating a provenance report."""
        engine.record("a.py", 1, 5, AIProvider.CLAUDE_CODE, "m1", "p1", tokens_used=100)
        engine.record("b.py", 1, 10, AIProvider.CURSOR, "m2", "p2", tokens_used=200)

        report = engine.generate_report()
        assert report.total_entries == 2
        assert report.total_tokens_consumed == 300
        assert "claude_code" in report.by_provider
        assert "cursor" in report.by_provider

    def test_stale_entries(self, engine):
        """Test stale entry detection."""
        entry = engine.record("a.py", 1, 5, AIProvider.CLAUDE_CODE, "m1", "p1")
        # Fresh entry should not be stale
        stale = engine.get_stale_entries(hours=72)
        assert len(stale) == 0

    def test_entry_to_dict(self, engine):
        """Test serialization of provenance entry."""
        entry = engine.record("a.py", 1, 5, AIProvider.CLAUDE_CODE, "m1", "p1")
        d = entry.to_dict()
        assert d["file_path"] == "a.py"
        assert d["provider"] == "claude_code"
        assert d["status"] == "generated"

    def test_entry_from_dict(self):
        """Test deserialization of provenance entry."""
        data = {
            "entry_id": "test123",
            "file_path": "a.py",
            "line_start": 1,
            "line_end": 5,
            "provider": "claude_code",
            "model": "m1",
            "prompt_hash": "abc",
            "prompt_preview": "test",
            "generated_at": "2026-01-01T00:00:00+00:00",
            "modified_at": "2026-01-01T00:00:00+00:00",
            "status": "generated",
            "trust_score": 0.0,
            "tokens_used": 0,
            "metadata": {},
        }
        entry = ProvenanceEntry.from_dict(data)
        assert entry.entry_id == "test123"
        assert entry.provider == AIProvider.CLAUDE_CODE

    def test_stats(self, engine):
        """Test engine statistics."""
        engine.record("a.py", 1, 5, AIProvider.CLAUDE_CODE, "m1", "p1")
        engine.record("b.py", 1, 10, AIProvider.CURSOR, "m2", "p2")
        stats = engine.stats()
        assert stats["total_entries"] == 2
        assert stats["tracked_files"] == 2