"""Tests for AvailabilityClassifier."""

import pytest

from prom_slo_analyzer.classifiers.availability import AvailabilityClassifier
from prom_slo_analyzer.classifiers.base import SLIType


class TestAvailabilityClassifier:
    """Tests for AvailabilityClassifier functionality."""

    @pytest.fixture
    def classifier(self):
        """Create AvailabilityClassifier instance for testing."""
        return AvailabilityClassifier()

    def test_sli_type(self, classifier):
        """Test SLI type property."""
        assert classifier.sli_type == SLIType.AVAILABILITY

    def test_is_up_metric(self, classifier):
        """Test 'up' metric detection."""
        assert classifier._is_up_metric("up") is True
        assert classifier._is_up_metric("service_up") is True
        assert classifier._is_up_metric("api_gateway_up") is True

        # Non-up metrics
        assert classifier._is_up_metric("uptime_seconds") is False
        assert classifier._is_up_metric("cpu_usage_percent") is False

    def test_is_health_metric(self, classifier):
        """Test health metric detection."""
        assert classifier._is_health_metric("service_healthy") is True
        assert classifier._is_health_metric("api_health") is True
        assert classifier._is_health_metric("database_alive") is True
        assert classifier._is_health_metric("endpoint_ready") is True
        assert classifier._is_health_metric("service_available") is True
        assert classifier._is_health_metric("worker_running") is True
        assert classifier._is_health_metric("cache_active") is True
        assert classifier._is_health_metric("feature_enabled") is True
        assert classifier._is_health_metric("service_online") is True

        # Non-health metrics
        assert classifier._is_health_metric("request_count") is False
        assert classifier._is_health_metric("memory_usage") is False

    def test_classify_up_metric(self, classifier):
        """Test classification of 'up' metrics."""
        result = classifier.classify("up")

        assert result is not None
        assert result.metric_name == "up"
        assert result.sli_type == SLIType.AVAILABILITY
        assert result.confidence == 1.0  # Maximum confidence for 'up' metrics
        assert "avg_over_time(up[5m])" in result.suggested_promql
        assert "job" in result.labels_needed
        assert "instance" in result.labels_needed

    def test_classify_health_metric(self, classifier):
        """Test classification of health metrics."""
        result = classifier.classify("service_healthy")

        assert result is not None
        assert result.metric_name == "service_healthy"
        assert result.sli_type == SLIType.AVAILABILITY
        assert result.confidence >= 0.9  # Very high confidence for health metrics
        assert "avg_over_time(service_healthy[5m])" in result.suggested_promql

    def test_classify_non_availability_metric(self, classifier):
        """Test that non-availability metrics are not classified."""
        # Request counter
        result = classifier.classify("http_requests_total")
        assert result is None

        # Memory metric
        result = classifier.classify("memory_usage_bytes")
        assert result is None

        # CPU metric
        result = classifier.classify("cpu_usage_percent")
        assert result is None
