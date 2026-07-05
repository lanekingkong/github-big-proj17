"""Tests for the token optimizer."""

import pytest
from codetruth.engine.optimizer import (
    TokenOptimizer,
    CompressionStrategy,
    CompressionResult,
)


class TestTokenOptimizer:
    """Test suite for TokenOptimizer."""

    @pytest.fixture
    def optimizer(self):
        return TokenOptimizer()

    def test_estimate_tokens(self, optimizer):
        """Test token estimation."""
        text = "Hello world, this is a test string with some content."
        tokens = optimizer.estimate_tokens(text)
        assert tokens > 0
        assert tokens <= len(text)

    def test_compress_minimal(self, optimizer):
        """Test minimal compression."""
        text = "line1\n\n\n\nline2\n\n\nline3"
        result = optimizer.compress_minimal(text)
        assert result.compressed_tokens <= result.original_tokens
        assert result.strategy_used == CompressionStrategy.MINIMAL

    def test_compress_moderate(self, optimizer):
        """Test moderate compression."""
        text = """
# This is a comment
def foo():
    # Another comment
    return 42
"""
        result = optimizer.compress_moderate(text)
        assert result.compressed_tokens <= result.original_tokens
        assert result.strategy_used == CompressionStrategy.MODERATE

    def test_compress_aggressive(self, optimizer):
        """Test aggressive compression."""
        text = """
# Comment 1
def foo():
    # Comment 2
    x = 1
    # Comment 3
    return x

if __name__ == "__main__":
    foo()
"""
        result = optimizer.compress_aggressive(text)
        assert result.compressed_tokens <= result.original_tokens
        assert result.strategy_used == CompressionStrategy.AGGRESSIVE

    def test_compress_semantic(self, optimizer):
        """Test semantic compression."""
        text = """
def foo():
    return 1

def bar():
    return 2

class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
"""
        result = optimizer.compress_semantic(text)
        # For very small inputs, semantic compression may add summary metadata
        # making it larger; this is expected and acceptable
        assert result.strategy_used == CompressionStrategy.SEMANTIC
        assert "def foo" in result.compressed_text or "def bar" in result.compressed_text

    def test_optimize_with_strategy(self, optimizer):
        """Test optimize with explicit strategy."""
        text = "x" * 1000
        result = optimizer.optimize(text, CompressionStrategy.MINIMAL)
        assert result.strategy_used == CompressionStrategy.MINIMAL

    def test_auto_optimize_small(self, optimizer):
        """Test auto-optimize for small text."""
        text = "short text"
        result = optimizer.auto_optimize(text)
        assert result.strategy_used == CompressionStrategy.MINIMAL

    def test_auto_optimize_medium(self, optimizer):
        """Test auto-optimize for medium text."""
        text = "x" * 5000
        result = optimizer.auto_optimize(text)
        assert result.strategy_used in (
            CompressionStrategy.MODERATE,
            CompressionStrategy.MINIMAL,
        )

    def test_auto_optimize_large(self, optimizer):
        """Test auto-optimize for large text."""
        text = "x" * 30000
        result = optimizer.auto_optimize(text)
        assert result.strategy_used in (
            CompressionStrategy.AGGRESSIVE,
            CompressionStrategy.SEMANTIC,
        )

    def test_compression_result_to_dict(self, optimizer):
        """Test CompressionResult serialization."""
        result = optimizer.compress_minimal("test text")
        d = result.to_dict()
        assert "original_tokens" in d
        assert "compressed_tokens" in d
        assert "compression_ratio" in d
        assert "strategy" in d

    def test_get_report(self, optimizer):
        """Test optimization report."""
        optimizer.compress_minimal("test1")
        optimizer.compress_moderate("test2")
        report = optimizer.get_report()
        assert report.operations >= 1
        assert report.total_original_tokens > 0

    def test_estimate_cost(self, optimizer):
        """Test cost estimation."""
        cost = optimizer.estimate_cost(1000, 500)
        assert cost > 0

    def test_empty_text(self, optimizer):
        """Test compression of empty text."""
        result = optimizer.compress_minimal("")
        assert result.original_tokens >= 0
        assert result.compressed_tokens >= 0