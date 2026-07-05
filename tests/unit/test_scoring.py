"""Tests for the trust scoring engine."""

import pytest
from codetruth.engine.scoring import (
    TrustScoringEngine,
    Dimension,
    ScoreLevel,
    DimensionScore,
    TrustScore,
)


class TestTrustScoringEngine:
    """Test suite for TrustScoringEngine."""

    @pytest.fixture
    def engine(self):
        return TrustScoringEngine()

    def test_assess_clean_code(self, engine):
        """Test assessing clean, well-documented code."""
        code = '''
def calculate_average(numbers: list[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers.

    Args:
        numbers: List of floating point numbers.

    Returns:
        The arithmetic mean.
    """
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
'''
        score = engine.assess("test1", "calculate_average", "function", code, "python")
        assert score.overall_score > 60
        assert score.level in (ScoreLevel.GOOD, ScoreLevel.EXCELLENT, ScoreLevel.FAIR)

    def test_assess_code_with_secrets(self, engine):
        """Test assessing code with hardcoded secrets."""
        code = '''
def connect_db():
    password = "admin123"
    api_key = "sk-abc123def456"
    return password
'''
        score = engine.assess("test2", "connect_db", "function", code, "python")
        assert score.overall_score < 90  # Should be penalized for secrets
        # Security dimension should have issues
        sec = score.dimensions[Dimension.SECURITY]
        assert len(sec.issues) > 0

    def test_assess_code_with_eval(self, engine):
        """Test assessing code with dangerous eval()."""
        code = '''
def execute(user_input):
    result = eval(user_input)
    return result
'''
        score = engine.assess("test3", "execute", "function", code, "python")
        sec = score.dimensions[Dimension.SECURITY]
        assert len(sec.issues) > 0

    def test_get_score(self, engine):
        """Test retrieving a previously computed score."""
        code = "def foo(): pass"
        engine.assess("test4", "foo", "function", code, "python")
        retrieved = engine.get_score("test4")
        assert retrieved is not None
        assert retrieved.entity_name == "foo"

    def test_get_nonexistent_score(self, engine):
        """Test retrieving a non-existent score."""
        assert engine.get_score("nonexistent") is None

    def test_passes_threshold(self, engine):
        """Test threshold checking."""
        code = '''
def well_documented(x: int) -> int:
    """Return x plus one."""
    return x + 1
'''
        engine.assess("test5", "well_documented", "function", code, "python")
        # This should pass the default threshold of 70
        result = engine.passes_threshold("test5")
        assert isinstance(result, bool)

    def test_needs_warning(self, engine):
        """Test warning threshold."""
        code = "def f(): pass"
        engine.assess("test6", "f", "function", code, "python")
        result = engine.needs_warning("test6")
        assert isinstance(result, bool)

    def test_stats(self, engine):
        """Test scoring statistics."""
        engine.assess("a", "func_a", "function", "def a(): return 1", "python")
        engine.assess("b", "func_b", "function", "def b(): return 2", "python")
        stats = engine.stats()
        assert stats["total_assessments"] == 2
        assert "avg_score" in stats

    def test_dimension_score_levels(self):
        """Test dimension score level classification."""
        ds = DimensionScore(dimension=Dimension.QUALITY, score=95)
        assert ds.level == ScoreLevel.EXCELLENT

        ds = DimensionScore(dimension=Dimension.QUALITY, score=80)
        assert ds.level == ScoreLevel.GOOD

        ds = DimensionScore(dimension=Dimension.QUALITY, score=65)
        assert ds.level == ScoreLevel.FAIR

        ds = DimensionScore(dimension=Dimension.QUALITY, score=45)
        assert ds.level == ScoreLevel.WARNING

        ds = DimensionScore(dimension=Dimension.QUALITY, score=20)
        assert ds.level == ScoreLevel.CRITICAL

    def test_custom_weights(self, engine):
        """Test custom dimension weights."""
        custom_weights = {
            Dimension.QUALITY: 0.5,
            Dimension.SECURITY: 0.3,
            Dimension.TESTABILITY: 0.05,
            Dimension.PERFORMANCE: 0.05,
            Dimension.DOCUMENTATION: 0.05,
            Dimension.MAINTAINABILITY: 0.05,
        }
        engine_custom = TrustScoringEngine(weights=custom_weights)
        code = "def f(): pass"
        score = engine_custom.assess("test7", "f", "function", code, "python")
        assert score.overall_score >= 0

    def test_trust_score_to_dict(self, engine):
        """Test TrustScore serialization."""
        code = "def foo(): return 42"
        score = engine.assess("test8", "foo", "function", code, "python")
        d = score.to_dict()
        assert d["entity_name"] == "foo"
        assert "dimensions" in d
        assert "overall_score" in d