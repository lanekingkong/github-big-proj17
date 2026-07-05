"""Tests for the quality gate pipeline."""

import pytest
from codetruth.gates import (
    GatePipeline,
    GateRule,
    GateStatus,
    GateSeverity,
    GateCheck,
    GateResult,
)


class TestGatePipeline:
    """Test suite for GatePipeline."""

    @pytest.fixture
    def pipeline(self):
        return GatePipeline(name="test").build_default_rules()

    def test_build_default_rules(self, pipeline):
        """Test that default rules are created."""
        rules = pipeline.get_rules()
        assert len(rules) > 0
        rule_ids = [r.rule_id for r in rules]
        assert "sec_hardcoded_secrets" in rule_ids
        assert "qual_line_length" in rule_ids

    def test_check_clean_code(self, pipeline):
        """Test checking clean code."""
        code = '''
def hello_world():
    """Say hello."""
    return "Hello, World!"
'''
        result = pipeline.check(code=code, file_path="test.py")
        assert result.overall_status in (GateStatus.PASSED, GateStatus.WARNING)

    def test_check_code_with_secrets(self, pipeline):
        """Test checking code with hardcoded secrets."""
        code = '''
def connect():
    password = "admin123"
    api_key = "sk-secret"
'''
        result = pipeline.check(code=code, file_path="test.py")
        # Should have at least one failure for secrets
        assert result.fail_count >= 1

    def test_check_code_with_injection(self, pipeline):
        """Test checking code with injection vulnerabilities."""
        code = '''
def run(user_input):
    eval(user_input)
'''
        result = pipeline.check(code=code, file_path="test.py")
        assert result.fail_count >= 1

    def test_check_long_lines(self, pipeline):
        """Test checking code with long lines."""
        long_line = "x = " + "a" * 150
        code = long_line
        result = pipeline.check(code=code, file_path="test.py")
        assert result.warn_count >= 1 or result.fail_count >= 1

    def test_check_with_test_coverage(self, pipeline):
        """Test checking with test coverage data."""
        code = "def foo(): pass"
        result = pipeline.check(code=code, file_path="test.py", test_coverage=80)
        # Should pass coverage check
        coverage_checks = [
            c for c in result.checks if c.rule.rule_id == "cov_test_presence"
        ]
        if coverage_checks:
            assert coverage_checks[0].status == GateStatus.PASSED

    def test_check_with_trust_score(self, pipeline):
        """Test checking with trust score data."""
        code = "def foo(): pass"
        result = pipeline.check(code=code, trust_score=85)
        assert result is not None

    def test_add_rule(self, pipeline):
        """Test adding a custom rule."""
        custom_rule = GateRule(
            rule_id="custom_001",
            name="Custom Rule",
            description="A custom quality rule",
            category="custom",
            severity=GateSeverity.MAJOR,
        )
        pipeline.add_rule(custom_rule)
        assert "custom_001" in [r.rule_id for r in pipeline.get_rules()]

    def test_remove_rule(self, pipeline):
        """Test removing a rule."""
        assert pipeline.remove_rule("sec_hardcoded_secrets") is True
        assert pipeline.remove_rule("nonexistent") is False

    def test_gate_result_to_dict(self, pipeline):
        """Test GateResult serialization."""
        result = pipeline.check(code="def foo(): pass")
        d = result.to_dict()
        assert "gate_id" in d
        assert "overall_status" in d
        assert "checks" in d

    def test_stats(self, pipeline):
        """Test pipeline statistics."""
        pipeline.check(code="def a(): pass")
        pipeline.check(code="def b(): pass")
        stats = pipeline.stats()
        assert stats["total_runs"] == 2
        assert "pass_rate" in stats

    def test_skip_disabled_rule(self, pipeline):
        """Test that disabled rules are skipped."""
        pipeline._rules["doc_docstring"].enabled = False
        result = pipeline.check(code="def foo(): pass")
        doc_checks = [
            c for c in result.checks if c.rule.rule_id == "doc_docstring"
        ]
        if doc_checks:
            assert doc_checks[0].status == GateStatus.SKIPPED