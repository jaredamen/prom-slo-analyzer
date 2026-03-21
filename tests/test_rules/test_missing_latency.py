"""Tests for MissingLatencyRule."""

import pytest

from prom_slo_analyzer.classifiers.base import ClassificationResult, SLIType
from prom_slo_analyzer.discovery import ServiceMetrics
from prom_slo_analyzer.rules.base import GapSeverity
from prom_slo_analyzer.rules.missing_latency import MissingLatencyRule


class TestMissingLatencyRule:
    """Tests for MissingLatencyRule functionality."""

    @pytest.fixture
    def rule(self):
        """Create MissingLatencyRule instance for testing."""
        return MissingLatencyRule()

    @pytest.fixture
    def service_with_all_metrics(self):
        """Service with latency, error rate, and throughput metrics."""
        return ServiceMetrics(
            name="complete_service",
            namespace="production",
            metrics=["requests_total", "errors_total", "duration_bucket"],
            labels={},
        )

    @pytest.fixture
    def service_missing_latency(self):
        """Service with error rate and throughput but no latency."""
        return ServiceMetrics(
            name="incomplete_service", namespace="production", metrics=["requests_total", "errors_total"], labels={}
        )

    @pytest.fixture
    def service_no_request_metrics(self):
        """Service with no request-related metrics."""
        return ServiceMetrics(
            name="background_service", namespace="production", metrics=["memory_usage", "cpu_usage"], labels={}
        )

    def test_rule_name(self, rule):
        """Test rule name property."""
        assert rule.rule_name == "Missing Latency Metrics"

    def test_no_gap_when_latency_present(self, rule, service_with_all_metrics):
        """Test no gap when service has latency metrics."""
        classifications = [
            ClassificationResult("requests_total", SLIType.THROUGHPUT, 0.9),
            ClassificationResult("errors_total", SLIType.ERROR_RATE, 0.9),
            ClassificationResult("duration_bucket", SLIType.LATENCY, 0.9),
        ]

        gaps = rule.check(service_with_all_metrics, classifications)

        assert len(gaps) == 0

    def test_gap_when_missing_latency_with_both_error_and_throughput(self, rule, service_missing_latency):
        """Test high severity gap when missing latency but has both error and throughput."""
        classifications = [
            ClassificationResult("requests_total", SLIType.THROUGHPUT, 0.9),
            ClassificationResult("errors_total", SLIType.ERROR_RATE, 0.9),
        ]

        gaps = rule.check(service_missing_latency, classifications)

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.service_name == "incomplete_service"
        assert gap.severity == GapSeverity.HIGH
        assert "tracks both errors and throughput but lacks latency" in gap.message
        assert "histogram metrics" in gap.recommendation

    def test_gap_when_missing_latency_with_throughput_only(self, rule, service_missing_latency):
        """Test medium severity gap when missing latency but has throughput."""
        classifications = [ClassificationResult("requests_total", SLIType.THROUGHPUT, 0.9)]

        gaps = rule.check(service_missing_latency, classifications)

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.severity == GapSeverity.MEDIUM
        assert "tracks request throughput but lacks latency" in gap.message

    def test_gap_when_missing_latency_with_errors_only(self, rule, service_missing_latency):
        """Test medium severity gap when missing latency but has error rate."""
        classifications = [ClassificationResult("errors_total", SLIType.ERROR_RATE, 0.9)]

        gaps = rule.check(service_missing_latency, classifications)

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.severity == GapSeverity.MEDIUM
        assert "tracks errors but lacks latency" in gap.message

    def test_no_gap_for_non_request_services(self, rule, service_no_request_metrics):
        """Test no gap for services without request-related metrics."""
        classifications = []  # No request-related classifications

        gaps = rule.check(service_no_request_metrics, classifications)

        assert len(gaps) == 0

    def test_affected_metrics_included(self, rule, service_missing_latency):
        """Test that affected metrics are included in gap result."""
        classifications = [
            ClassificationResult("requests_total", SLIType.THROUGHPUT, 0.9),
            ClassificationResult("errors_total", SLIType.ERROR_RATE, 0.9),
        ]

        gaps = rule.check(service_missing_latency, classifications)

        assert len(gaps) == 1
        gap = gaps[0]
        assert "requests_total" in gap.affected_metrics
        assert "errors_total" in gap.affected_metrics
