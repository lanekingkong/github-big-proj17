"""
Trust Scoring Engine - multi-dimensional quality assessment.

Inspired by: PR-Agent (AI code review), SonarQube (quality gates),
             ECC (security layer with configurable policies)

Scoring dimensions:
- Quality: code style, complexity, maintainability
- Security: vulnerability patterns, sensitive data exposure
- Testability: test coverage, mockability
- Performance: algorithm efficiency, resource usage
- Documentation: docstrings, comments, type hints
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any


class ScoreLevel(str, Enum):
    """Trust score classification."""
    EXCELLENT = "excellent"   # 90-100
    GOOD = "good"             # 75-89
    FAIR = "fair"             # 60-74
    WARNING = "warning"       # 40-59
    CRITICAL = "critical"     # 0-39


class Dimension(str, Enum):
    """Scoring dimensions."""
    QUALITY = "quality"
    SECURITY = "security"
    TESTABILITY = "testability"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"


# Dimension weights (sum = 1.0)
DEFAULT_WEIGHTS: dict[Dimension, float] = {
    Dimension.QUALITY: 0.25,
    Dimension.SECURITY: 0.30,
    Dimension.TESTABILITY: 0.15,
    Dimension.PERFORMANCE: 0.10,
    Dimension.DOCUMENTATION: 0.10,
    Dimension.MAINTAINABILITY: 0.10,
}


@dataclass
class DimensionScore:
    """Score for a single dimension."""

    dimension: Dimension
    score: float  # 0-100
    max_score: float = 100.0
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def normalized(self) -> float:
        """Normalize to 0-1 range."""
        return max(0.0, min(1.0, self.score / self.max_score))

    @property
    def level(self) -> ScoreLevel:
        if self.score >= 90:
            return ScoreLevel.EXCELLENT
        if self.score >= 75:
            return ScoreLevel.GOOD
        if self.score >= 60:
            return ScoreLevel.FAIR
        if self.score >= 40:
            return ScoreLevel.WARNING
        return ScoreLevel.CRITICAL


@dataclass
class TrustScore:
    """Aggregated trust score for a code entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    overall_score: float  # 0-100 weighted average
    dimensions: dict[Dimension, DimensionScore]
    level: ScoreLevel
    ai_generated_pct: float
    assessed_at: datetime
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "overall_score": self.overall_score,
            "dimensions": {
                d.value: {
                    "score": ds.score,
                    "issues": ds.issues,
                    "suggestions": ds.suggestions,
                }
                for d, ds in self.dimensions.items()
            },
            "level": self.level.value,
            "ai_generated_pct": self.ai_generated_pct,
            "assessed_at": self.assessed_at.isoformat(),
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


class TrustScoringEngine:
    """
    Multi-dimensional trust scoring system.

    Evaluates code quality across six axes and produces
    an overall trust score with actionable recommendations.
    """

    def __init__(
        self,
        weights: Optional[dict[Dimension, float]] = None,
        pass_threshold: float = 70.0,
        warn_threshold: float = 50.0,
    ):
        self._weights = weights or DEFAULT_WEIGHTS
        self._pass_threshold = pass_threshold
        self._warn_threshold = warn_threshold
        self._scores: dict[str, TrustScore] = {}

    def _calculate_quality(self, code: str, language: str = "") -> DimensionScore:
        """Assess code quality: style, complexity, patterns."""
        lines = code.strip().split("\n")
        score = 100.0
        issues = []
        suggestions = []

        long_lines = [l for l in lines if len(l) > 120]
        if long_lines:
            score -= min(20, len(long_lines) * 2)
            issues.append(f"{len(long_lines)} lines exceed 120 characters")

        if len(lines) > 200:
            score -= 15
            issues.append("Function/class exceeds 200 lines; consider splitting")
            suggestions.append("Split into smaller, focused units")

        if "TODO" in code or "FIXME" in code:
            score -= 5
            issues.append("Contains TODO/FIXME markers")

        if "pass" in code and len(lines) < 5:
            score -= 10
            issues.append("Contains placeholder 'pass' statement")

        return DimensionScore(
            dimension=Dimension.QUALITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_security(self, code: str, language: str = "") -> DimensionScore:
        """Assess security: vulnerability patterns, sensitive data."""
        score = 100.0
        issues = []
        suggestions = []

        security_patterns = [
            ("password", "Hardcoded password detected"),
            ("secret_key", "Hardcoded secret key detected"),
            ("api_key", "Hardcoded API key detected"),
            ("token", "Hardcoded token detected"),
            ("eval(", "Dangerous eval() usage detected"),
            ("exec(", "Dangerous exec() usage detected"),
            ("os.system(", "Unsafe os.system() call detected"),
            ("subprocess.call(", "Potentially unsafe subprocess call"),
            ("pickle.loads", "Unsafe pickle deserialization"),
            ("sql = f", "Potential SQL injection via f-string"),
            ("sql = '", "Raw SQL string may be injectable"),
        ]

        for pattern, message in security_patterns:
            if pattern in code:
                score -= 10
                issues.append(message)
                suggestions.append(f"Remove or externalize {pattern}")

        return DimensionScore(
            dimension=Dimension.SECURITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_testability(self, code: str, language: str = "") -> DimensionScore:
        """Assess testability: structure, dependencies, mockability."""
        score = 80.0
        issues = []
        suggestions = []

        if "import " in code:
            import_count = code.count("import ")
            if import_count > 10:
                score -= min(20, (import_count - 10) * 2)
                issues.append(f"High import count ({import_count}); may be hard to mock")
                suggestions.append("Reduce dependencies or use dependency injection")

        if "unittest" in code or "pytest" in code or "test_" in code:
            score += 15
        else:
            suggestions.append("Add unit tests for this code")

        return DimensionScore(
            dimension=Dimension.TESTABILITY,
            score=max(0, min(100, score)),
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_performance(self, code: str, language: str = "") -> DimensionScore:
        """Assess performance: algorithm efficiency, resource usage."""
        score = 85.0
        issues = []
        suggestions = []

        perf_anti_patterns = [
            (["for ", " in range(", ".append("], "Loop with append; consider list comprehension"),
            (["while True", "sleep("], "Busy-waiting pattern; consider event-driven approach"),
            (["open(", "read()", "close()"], "Manual file handling; consider 'with' statement"),
        ]

        for patterns, message in perf_anti_patterns:
            if all(p in code for p in patterns):
                score -= 8
                issues.append(message)

        return DimensionScore(
            dimension=Dimension.PERFORMANCE,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_documentation(self, code: str, language: str = "") -> DimensionScore:
        """Assess documentation quality."""
        score = 70.0
        issues = []
        suggestions = []

        has_docstring = '"""' in code or "'''" in code
        has_comments = "#" in code or "//" in code
        has_type_hints = ": " in code and "->" in code

        if has_docstring:
            score += 20
        else:
            issues.append("Missing docstring")
            suggestions.append("Add docstring explaining purpose and parameters")

        if has_comments:
            score += 5

        if has_type_hints:
            score += 5
        else:
            suggestions.append("Add type hints for better maintainability")

        return DimensionScore(
            dimension=Dimension.DOCUMENTATION,
            score=max(0, min(100, score)),
            issues=issues,
            suggestions=suggestions,
        )

    def _calculate_maintainability(self, code: str, language: str = "") -> DimensionScore:
        """Assess maintainability: clarity, modularity, naming."""
        score = 80.0
        issues = []
        suggestions = []

        lines = code.strip().split("\n")
        nesting = max((len(l) - len(l.lstrip())) // 4 for l in lines if l.strip())
        if nesting > 4:
            score -= 20
            issues.append(f"Deep nesting level ({nesting}); consider refactoring")
            suggestions.append("Extract nested blocks into separate functions")

        if "global " in code:
            score -= 10
            issues.append("Uses global variables; avoid mutable global state")

        return DimensionScore(
            dimension=Dimension.MAINTAINABILITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )

    def assess(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        code: str,
        language: str = "",
        ai_generated_pct: float = 0.0,
    ) -> TrustScore:
        """Perform a full multi-dimensional assessment."""
        dimensions = {
            Dimension.QUALITY: self._calculate_quality(code, language),
            Dimension.SECURITY: self._calculate_security(code, language),
            Dimension.TESTABILITY: self._calculate_testability(code, language),
            Dimension.PERFORMANCE: self._calculate_performance(code, language),
            Dimension.DOCUMENTATION: self._calculate_documentation(code, language),
            Dimension.MAINTAINABILITY: self._calculate_maintainability(code, language),
        }

        weighted_sum = sum(
            ds.score * self._weights.get(d, 0.0) for d, ds in dimensions.items()
        )
        overall = round(weighted_sum, 1)

        if overall >= 90:
            level = ScoreLevel.EXCELLENT
        elif overall >= 75:
            level = ScoreLevel.GOOD
        elif overall >= 60:
            level = ScoreLevel.FAIR
        elif overall >= 40:
            level = ScoreLevel.WARNING
        else:
            level = ScoreLevel.CRITICAL

        all_issues = []
        all_suggestions = []
        for ds in dimensions.values():
            all_issues.extend(ds.issues)
            all_suggestions.extend(ds.suggestions)

        summary = (
            f"{entity_name} scored {overall}/100 ({level.value}). "
            f"{len(all_issues)} issues, {len(all_suggestions)} suggestions."
        )

        score = TrustScore(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            overall_score=overall,
            dimensions=dimensions,
            level=level,
            ai_generated_pct=ai_generated_pct,
            assessed_at=datetime.now(timezone.utc),
            summary=summary,
            recommendations=all_suggestions[:5],
        )

        self._scores[entity_id] = score
        return score

    def get_score(self, entity_id: str) -> Optional[TrustScore]:
        """Get a previously computed score."""
        return self._scores.get(entity_id)

    def passes_threshold(self, entity_id: str) -> bool:
        """Check if an entity passes the quality threshold."""
        score = self._scores.get(entity_id)
        if not score:
            return False
        return score.overall_score >= self._pass_threshold

    def needs_warning(self, entity_id: str) -> bool:
        """Check if an entity triggers a warning."""
        score = self._scores.get(entity_id)
        if not score:
            return True
        return score.overall_score < self._warn_threshold

    def stats(self) -> dict[str, Any]:
        """Get scoring statistics."""
        if not self._scores:
            return {"total_assessments": 0}
        scores = [s.overall_score for s in self._scores.values()]
        levels = {}
        for s in self._scores.values():
            lv = s.level.value
            levels[lv] = levels.get(lv, 0) + 1
        return {
            "total_assessments": len(self._scores),
            "avg_score": round(sum(scores) / len(scores), 1),
            "min_score": min(scores),
            "max_score": max(scores),
            "pass_rate": round(
                sum(1 for s in self._scores.values() if s.overall_score >= self._pass_threshold)
                / len(self._scores) * 100,
                1,
            ),
            "by_level": levels,
        }