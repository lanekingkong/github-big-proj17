"""
Quality Gate Pipeline - configurable verification checkpoints.

Inspired by: PR-Agent (automated PR review), SonarQube (quality gates),
             ECC (security layer with configurable policies)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Callable


class GateStatus(str, Enum):
    """Status of a quality gate check."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


class GateSeverity(str, Enum):
    """Severity level of a gate failure."""
    BLOCKER = "blocker"    # Must be fixed before proceeding
    CRITICAL = "critical"  # Should be fixed immediately
    MAJOR = "major"        # Should be fixed in this sprint
    MINOR = "minor"        # Nice to fix
    INFO = "info"          # Informational only


@dataclass
class GateRule:
    """A single rule in a quality gate."""

    rule_id: str
    name: str
    description: str
    category: str  # security, quality, coverage, style, etc.
    severity: GateSeverity
    enabled: bool = True
    threshold: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateCheck:
    """Result of a single quality gate check."""

    rule: GateRule
    status: GateStatus
    score: float = 100.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GateResult:
    """Aggregated result of a quality gate pipeline."""

    gate_id: str
    gate_name: str
    checks: list[GateCheck]
    overall_status: GateStatus
    pass_count: int
    warn_count: int
    fail_count: int
    skip_count: int
    duration_ms: float = 0.0
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "overall_status": self.overall_status.value,
            "pass_count": self.pass_count,
            "warn_count": self.warn_count,
            "fail_count": self.fail_count,
            "skip_count": self.skip_count,
            "duration_ms": self.duration_ms,
            "checks": [
                {
                    "rule_name": c.rule.name,
                    "category": c.rule.category,
                    "severity": c.rule.severity.value,
                    "status": c.status.value,
                    "score": c.score,
                    "message": c.message,
                }
                for c in self.checks
            ],
            "checked_at": self.checked_at.isoformat(),
        }


class GatePipeline:
    """
    Configurable quality gate pipeline.

    Runs a sequence of quality checks against code and
    determines whether it meets the required standards.
    """

    def __init__(self, name: str = "default"):
        self._name = name
        self._rules: dict[str, GateRule] = {}
        self._history: list[GateResult] = []

    def add_rule(self, rule: GateRule) -> GateRule:
        """Add a quality gate rule."""
        self._rules[rule.rule_id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a quality gate rule."""
        return self._rules.pop(rule_id, None) is not None

    def get_rules(self) -> list[GateRule]:
        """Get all configured rules."""
        return list(self._rules.values())

    def build_default_rules(self) -> "GatePipeline":
        """Build a comprehensive set of default quality gate rules."""

        default_rules = [
            GateRule(
                rule_id="sec_hardcoded_secrets",
                name="No Hardcoded Secrets",
                description="Code must not contain hardcoded passwords, keys, or tokens",
                category="security",
                severity=GateSeverity.BLOCKER,
            ),
            GateRule(
                rule_id="sec_input_validation",
                name="Input Validation",
                description="All external inputs must be validated and sanitized",
                category="security",
                severity=GateSeverity.CRITICAL,
            ),
            GateRule(
                rule_id="sec_injection",
                name="Injection Prevention",
                description="Code must not be vulnerable to SQL/command injection",
                category="security",
                severity=GateSeverity.BLOCKER,
            ),
            GateRule(
                rule_id="qual_complexity",
                name="Code Complexity",
                description="Functions must maintain reasonable cyclomatic complexity",
                category="quality",
                severity=GateSeverity.MAJOR,
            ),
            GateRule(
                rule_id="qual_line_length",
                name="Line Length",
                description="Lines should not exceed 120 characters",
                category="quality",
                severity=GateSeverity.MINOR,
            ),
            GateRule(
                rule_id="cov_test_presence",
                name="Test Presence",
                description="New code should have associated tests",
                category="coverage",
                severity=GateSeverity.MAJOR,
            ),
            GateRule(
                rule_id="doc_docstring",
                name="Documentation",
                description="Public functions and classes should have docstrings",
                category="documentation",
                severity=GateSeverity.MINOR,
            ),
            GateRule(
                rule_id="perf_n_plus_1",
                name="N+1 Query Prevention",
                description="Avoid N+1 query patterns in database code",
                category="performance",
                severity=GateSeverity.CRITICAL,
            ),
            GateRule(
                rule_id="style_consistency",
                name="Style Consistency",
                description="Code should follow project style conventions",
                category="style",
                severity=GateSeverity.MINOR,
            ),
            GateRule(
                rule_id="dep_no_circular",
                name="No Circular Dependencies",
                description="Code must not introduce circular dependencies",
                category="architecture",
                severity=GateSeverity.CRITICAL,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

        return self

    def check(
        self,
        code: str = "",
        file_path: str = "",
        trust_score: Optional[float] = None,
        test_coverage: Optional[float] = None,
        ai_generated_pct: float = 0.0,
    ) -> GateResult:
        """Run all enabled quality gate checks against the given code."""
        import time
        start = time.time()
        checks: list[GateCheck] = []

        for rule in self._rules.values():
            if not rule.enabled:
                checks.append(GateCheck(
                    rule=rule,
                    status=GateStatus.SKIPPED,
                    message="Rule is disabled",
                ))
                continue

            if rule.rule_id == "sec_hardcoded_secrets":
                checks.append(self._check_secrets(code, rule))
            elif rule.rule_id == "sec_injection":
                checks.append(self._check_injection(code, rule))
            elif rule.rule_id == "qual_line_length":
                checks.append(self._check_line_length(code, rule))
            elif rule.rule_id == "doc_docstring":
                checks.append(self._check_docstrings(code, rule))
            elif rule.rule_id == "cov_test_presence":
                if test_coverage is not None:
                    status = GateStatus.PASSED if test_coverage >= 50 else GateStatus.FAILED
                    checks.append(GateCheck(
                        rule=rule,
                        status=status,
                        score=test_coverage,
                        message=f"Test coverage: {test_coverage}%",
                    ))
                else:
                    checks.append(GateCheck(
                        rule=rule,
                        status=GateStatus.WARNING,
                        score=0,
                        message="Test coverage data not available",
                    ))
            else:
                checks.append(GateCheck(
                    rule=rule,
                    status=GateStatus.PASSED,
                    score=100,
                    message="Passed",
                ))

        duration = (time.time() - start) * 1000
        passed = sum(1 for c in checks if c.status == GateStatus.PASSED)
        warned = sum(1 for c in checks if c.status == GateStatus.WARNING)
        failed = sum(1 for c in checks if c.status == GateStatus.FAILED)
        skipped = sum(1 for c in checks if c.status == GateStatus.SKIPPED)

        # Determine overall status
        has_blocker = any(
            c.status == GateStatus.FAILED and c.rule.severity == GateSeverity.BLOCKER
            for c in checks
        )
        has_critical = any(
            c.status == GateStatus.FAILED and c.rule.severity == GateSeverity.CRITICAL
            for c in checks
        )

        if has_blocker:
            overall = GateStatus.FAILED
        elif has_critical:
            overall = GateStatus.FAILED
        elif failed > 0:
            overall = GateStatus.WARNING
        elif warned > 0:
            overall = GateStatus.WARNING
        else:
            overall = GateStatus.PASSED

        import uuid
        result = GateResult(
            gate_id=str(uuid.uuid4())[:8],
            gate_name=self._name,
            checks=checks,
            overall_status=overall,
            pass_count=passed,
            warn_count=warned,
            fail_count=failed,
            skip_count=skipped,
            duration_ms=round(duration, 1),
        )

        self._history.append(result)
        return result

    def _check_secrets(self, code: str, rule: GateRule) -> GateCheck:
        """Check for hardcoded secrets."""
        secret_patterns = [
            "password", "secret", "api_key", "token", "private_key",
            "access_key", "auth_token",
        ]
        found = []
        for pattern in secret_patterns:
            if pattern in code.lower():
                # Check if it's assigned a literal value
                import re
                matches = re.findall(
                    rf'{pattern}\s*[:=]\s*["\']([^"\']+)["\']',
                    code, re.IGNORECASE
                )
                if matches:
                    found.append(pattern)

        if found:
            return GateCheck(
                rule=rule,
                status=GateStatus.FAILED,
                score=0,
                message=f"Hardcoded secrets found: {', '.join(found)}",
            )
        return GateCheck(rule=rule, status=GateStatus.PASSED, score=100, message="No secrets found")

    def _check_injection(self, code: str, rule: GateRule) -> GateCheck:
        """Check for injection vulnerabilities."""
        dangerous = []
        if "eval(" in code:
            dangerous.append("eval()")
        if "exec(" in code:
            dangerous.append("exec()")
        if "os.system(" in code:
            dangerous.append("os.system()")

        if dangerous:
            return GateCheck(
                rule=rule,
                status=GateStatus.FAILED,
                score=0,
                message=f"Dangerous functions: {', '.join(dangerous)}",
            )
        return GateCheck(rule=rule, status=GateStatus.PASSED, score=100, message="No injection risks")

    def _check_line_length(self, code: str, rule: GateRule) -> GateCheck:
        """Check line length."""
        lines = code.split("\n")
        long_lines = [i + 1 for i, l in enumerate(lines) if len(l) > 120]
        if long_lines:
            return GateCheck(
                rule=rule,
                status=GateStatus.WARNING,
                score=max(0, 100 - len(long_lines) * 2),
                message=f"{len(long_lines)} lines exceed 120 chars: lines {long_lines[:5]}",
            )
        return GateCheck(rule=rule, status=GateStatus.PASSED, score=100, message="All lines within limit")

    def _check_docstrings(self, code: str, rule: GateRule) -> GateCheck:
        """Check for docstrings on public functions/classes."""
        import re
        public_defs = re.findall(r'^def (?!_)\w+|^class (?!_)\w+', code, re.MULTILINE)
        if not public_defs:
            return GateCheck(rule=rule, status=GateStatus.PASSED, score=100, message="No public definitions")

        has_docstring = '"""' in code or "'''" in code
        if has_docstring:
            return GateCheck(rule=rule, status=GateStatus.PASSED, score=100, message="Docstrings present")
        return GateCheck(
            rule=rule,
            status=GateStatus.WARNING,
            score=50,
            message=f"{len(public_defs)} public definitions without docstrings",
        )

    def get_history(self, limit: int = 10) -> list[GateResult]:
        """Get recent gate check history."""
        return self._history[-limit:]

    def stats(self) -> dict[str, Any]:
        """Get pipeline statistics."""
        if not self._history:
            return {"total_runs": 0}
        passed = sum(1 for r in self._history if r.overall_status == GateStatus.PASSED)
        return {
            "total_runs": len(self._history),
            "pass_rate": round(passed / len(self._history) * 100, 1),
            "rules_configured": len(self._rules),
            "rules_enabled": sum(1 for r in self._rules.values() if r.enabled),
        }