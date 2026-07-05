"""
Token Optimizer - intelligent context compression for AI tools.

Inspired by: Headroom (60-95% token compression),
             CodeGraph (57% token reduction via structured queries)

Strategies:
- Remove redundant whitespace and comments when safe
- Strip boilerplate code patterns
- Preserve semantic meaning while reducing tokens
- Generate structured summaries of large files
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CompressionStrategy(str, Enum):
    """Available compression strategies."""
    MINIMAL = "minimal"          # Only remove excessive whitespace
    MODERATE = "moderate"        # Remove comments, trim whitespace
    AGGRESSIVE = "aggressive"    # Full compression: comments, whitespace, boilerplate
    SEMANTIC = "semantic"        # Generate compressed summary preserving meaning


@dataclass
class CompressionResult:
    """Result of a compression operation."""

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float  # 0-1, higher = more compressed
    strategy_used: CompressionStrategy
    compressed_text: str
    tokens_saved: int
    cost_saved_estimate: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": round(self.compression_ratio, 3),
            "strategy": self.strategy_used.value,
            "tokens_saved": self.tokens_saved,
            "cost_saved_estimate": round(self.cost_saved_estimate, 4),
            "warnings": self.warnings,
        }


@dataclass
class OptimizationReport:
    """Aggregated optimization report."""

    total_original_tokens: int
    total_compressed_tokens: int
    overall_compression_ratio: float
    total_cost_saved: float
    operations: int
    by_strategy: dict[str, int]


class TokenOptimizer:
    """
    Smart token compression engine.

    Reduces context size for AI tools while preserving
    semantic meaning, dramatically cutting token costs.
    """

    # Approximate cost per 1K tokens for major models (USD)
    _MODEL_COSTS: dict[str, tuple[float, float]] = {
        "claude-3-opus": (0.015, 0.075),
        "claude-3-sonnet": (0.003, 0.015),
        "gpt-4": (0.03, 0.06),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0005, 0.0015),
    }

    def __init__(
        self,
        target_ratio: float = 0.7,
        max_context_tokens: int = 128000,
        model: str = "claude-3-sonnet",
    ):
        self._target_ratio = target_ratio
        self._max_context_tokens = max_context_tokens
        self._model = model
        self._history: list[CompressionResult] = []

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: ~4 chars per token for English code)."""
        return max(1, len(text) // 4)

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """Estimate API cost for a given token count."""
        costs = self._MODEL_COSTS.get(self._model, (0.003, 0.015))
        return (input_tokens / 1000) * costs[0] + (output_tokens / 1000) * costs[1]

    def compress_minimal(self, text: str) -> CompressionResult:
        """Minimal compression: only excessive whitespace."""
        original = self.estimate_tokens(text)
        compressed = re.sub(r'\n{3,}', '\n\n', text)
        compressed = re.sub(r'[ \t]+$', '', compressed, flags=re.MULTILINE)
        compressed = compressed.strip()
        ct = self.estimate_tokens(compressed)
        ratio = 1 - (ct / original) if original > 0 else 0
        return CompressionResult(
            original_tokens=original,
            compressed_tokens=ct,
            compression_ratio=ratio,
            strategy_used=CompressionStrategy.MINIMAL,
            compressed_text=compressed,
            tokens_saved=original - ct,
            cost_saved_estimate=self.estimate_cost(original) - self.estimate_cost(ct),
        )

    def compress_moderate(self, text: str) -> CompressionResult:
        """Moderate compression: whitespace + single-line comments."""
        result = self.compress_minimal(text)
        compressed = result.compressed_text
        lines = compressed.split('\n')
        filtered = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') < 2 and stripped.count("'''") < 2:
                    continue
            filtered.append(line)
        compressed = '\n'.join(filtered)
        ct = self.estimate_tokens(compressed)
        original = result.original_tokens
        ratio = 1 - (ct / original) if original > 0 else 0
        warnings = []
        if ratio > 0.5:
            warnings.append("High compression may lose context; verify output")
        cr = CompressionResult(
            original_tokens=original,
            compressed_tokens=ct,
            compression_ratio=ratio,
            strategy_used=CompressionStrategy.MODERATE,
            compressed_text=compressed,
            tokens_saved=original - ct,
            cost_saved_estimate=self.estimate_cost(original) - self.estimate_cost(ct),
            warnings=warnings,
        )
        self._history.append(cr)
        return cr

    def compress_aggressive(self, text: str) -> CompressionResult:
        """Aggressive compression: remove comments, whitespace, boilerplate."""
        result = self.compress_moderate(text)
        compressed = result.compressed_text
        # Remove blank lines
        compressed = re.sub(r'\n\s*\n', '\n', compressed)
        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r'if __name__ == ["\']__main__["\']:.*',
            r'@staticmethod\s*\n',
            r'@classmethod\s*\n',
            r'@property\s*\n',
        ]
        for pattern in boilerplate_patterns:
            compressed = re.sub(pattern, '', compressed, flags=re.DOTALL)
        ct = self.estimate_tokens(compressed)
        original = result.original_tokens
        ratio = 1 - (ct / original) if original > 0 else 0
        warnings = result.warnings + (
            ["Aggressive compression may remove meaningful structural context"]
            if ratio > 0.7 else []
        )
        cr = CompressionResult(
            original_tokens=original,
            compressed_tokens=ct,
            compression_ratio=ratio,
            strategy_used=CompressionStrategy.AGGRESSIVE,
            compressed_text=compressed,
            tokens_saved=original - ct,
            cost_saved_estimate=self.estimate_cost(original) - self.estimate_cost(ct),
            warnings=warnings,
        )
        self._history.append(cr)
        return cr

    def compress_semantic(self, text: str) -> CompressionResult:
        """Semantic compression: generate a structural summary."""
        lines = text.strip().split('\n')
        signatures = []
        for line in lines:
            stripped = line.strip()
            if any(kw in stripped for kw in [
                'def ', 'class ', 'async def', 'import ',
                'from ', '@', 'return', 'raise', 'yield',
            ]):
                signatures.append(stripped)
        if not signatures:
            return self.compress_moderate(text)
        summary = (
            f"[CodeTruth Semantic Summary]\n"
            f"File structure ({len(lines)} lines, {len(signatures)} key statements):\n"
            + '\n'.join(f"  {s}" for s in signatures[:50])
        )
        if len(signatures) > 50:
            summary += f"\n  ... and {len(signatures) - 50} more statements"
        original = self.estimate_tokens(text)
        ct = self.estimate_tokens(summary)
        ratio = 1 - (ct / original) if original > 0 else 0
        cr = CompressionResult(
            original_tokens=original,
            compressed_tokens=ct,
            compression_ratio=ratio,
            strategy_used=CompressionStrategy.SEMANTIC,
            compressed_text=summary,
            tokens_saved=original - ct,
            cost_saved_estimate=self.estimate_cost(original) - self.estimate_cost(ct),
        )
        self._history.append(cr)
        return cr

    def optimize(
        self, text: str, strategy: CompressionStrategy = CompressionStrategy.MODERATE
    ) -> CompressionResult:
        """Optimize text using the specified strategy."""
        strategy_map = {
            CompressionStrategy.MINIMAL: self.compress_minimal,
            CompressionStrategy.MODERATE: self.compress_moderate,
            CompressionStrategy.AGGRESSIVE: self.compress_aggressive,
            CompressionStrategy.SEMANTIC: self.compress_semantic,
        }
        return strategy_map[strategy](text)

    def auto_optimize(self, text: str) -> CompressionResult:
        """Automatically choose the best compression strategy."""
        tokens = self.estimate_tokens(text)
        if tokens < 1000:
            return self.compress_minimal(text)
        if tokens < 5000:
            return self.compress_moderate(text)
        if tokens < 20000:
            return self.compress_aggressive(text)
        return self.compress_semantic(text)

    def get_report(self) -> OptimizationReport:
        """Generate an aggregated optimization report."""
        if not self._history:
            return OptimizationReport(0, 0, 0.0, 0.0, 0, {})
        total_original = sum(r.original_tokens for r in self._history)
        total_compressed = sum(r.compressed_tokens for r in self._history)
        total_cost = sum(r.cost_saved_estimate for r in self._history)
        by_strat: dict[str, int] = {}
        for r in self._history:
            s = r.strategy_used.value
            by_strat[s] = by_strat.get(s, 0) + 1
        return OptimizationReport(
            total_original_tokens=total_original,
            total_compressed_tokens=total_compressed,
            overall_compression_ratio=(
                1 - (total_compressed / total_original) if total_original > 0 else 0
            ),
            total_cost_saved=round(total_cost, 4),
            operations=len(self._history),
            by_strategy=by_strat,
        )