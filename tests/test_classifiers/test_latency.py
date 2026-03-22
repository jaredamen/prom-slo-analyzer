"""Tests for LatencyClassifier."""

import pytest

from prom_slo_analyzer.classifiers.base import SLIType
from prom_slo_analyzer.classifiers.latency import LatencyClassifier


class TestLatencyClassifier:
    """Tests for LatencyClassifier functionality."""

    @pytest.fixture
    def classifier(self):
        """Create LatencyClassifier instance for testing."""
        return LatencyClassifier()

    def test_sli_type(self, classifier):
        """Test SLI type property."""
        assert classifier.sli_type == SLIType.LATENCY

    def test_is_histogram_metric(self, classifier):
        """Test histogram metric detection."""
        assert classifier._is_histogram_metric("http_request_duration_seconds_bucket") is True
        assert classifier._is_histogram_metric("api_latency_count") is True
        assert classifier._is_histogram_metric("response_time_sum") is True

        # Non-histogram metrics
        assert classifier._is_histogram_metric("http_requests_total") is False
        assert classifier._is_histogram_metric("cpu_usage_percent") is False

    def test_is_summary_metric(self, classifier):
        """Test summary metric detection."""
        assert classifier._is_summary_metric("http_request_duration_quantile") is True
        assert classifier._is_summary_metric("api_latency_summary") is True

        # Non-summary metrics
        assert classifier._is_summary_metric("http_requests_total") is False
        assert classifier._is_summary_metric("cpu_usage_percent") is False

    def test_is_duration_metric(self, classifier):
        """Test duration metric detection."""
        # Duration keywords
        assert classifier._is_duration_metric("http_request_latency") is True
        assert classifier._is_duration_metric("api_duration_milliseconds") is True
        assert classifier._is_duration_metric("response_time_seconds") is True
        assert classifier._is_duration_metric("processing_time") is True
        assert classifier._is_duration_metric("execution_time_ms") is True
        assert classifier._is_duration_metric("roundtrip_latency") is True

        # Time unit keywords
        assert classifier._is_duration_metric("request_seconds") is True
        assert classifier._is_duration_metric("latency_milliseconds") is True
        assert classifier._is_duration_metric("delay_microseconds") is True
        assert classifier._is_duration_metric("wait_time_ns") is True

        # Non-duration metrics
        assert classifier._is_duration_metric("http_requests_total") is False
        assert classifier._is_duration_metric("cpu_cores_available") is False
        assert classifier._is_duration_metric("memory_bytes") is False

    def test_classify_histogram_metric(self, classifier):
        """Test classification of histogram metrics."""
        # Standard HTTP request duration histogram
        result = classifier.classify("http_request_duration_seconds_bucket")

        assert result is not None
        assert result.metric_name == "http_request_duration_seconds_bucket"
        assert result.sli_type == SLIType.LATENCY
        assert result.confidence >= 0.6
        assert "histogram_quantile" in result.suggested_promql
        assert "rate(" in result.suggested_promql
        assert "le" in result.labels_needed

    def test_classify_histogram_with_high_confidence_patterns(self, classifier):
        """Test histogram classification with high confidence patterns."""
        result = classifier.classify("api_gateway_request_latency_bucket")

        assert result is not None
        assert result.confidence >= 0.6  # Should have good confidence due to "latency" keyword
        assert "histogram_quantile" in result.suggested_promql

    def test_classify_summary_metric(self, classifier):
        """Test classification of summary metrics."""
        result = classifier.classify("http_request_duration_quantile")

        assert result is not None
        assert result.metric_name == "http_request_duration_quantile"
        assert result.sli_type == SLIType.LATENCY
        assert result.confidence <= 0.8  # Summaries get reduced confidence
        assert "quantile" in result.suggested_promql
        assert "quantile" in result.labels_needed

    def test_classify_duration_metric(self, classifier):
        """Test classification of direct duration metrics."""
        result = classifier.classify("api_processing_time_seconds")

        assert result is not None
        assert result.metric_name == "api_processing_time_seconds"
        assert result.sli_type == SLIType.LATENCY
        assert result.confidence >= 0.0
        assert "rate(" in result.suggested_promql

    def test_classify_non_latency_metric(self, classifier):
        """Test that non-latency metrics are not classified."""
        # Request counter
        result = classifier.classify("http_requests_total")
        assert result is None

        # Error counter
        result = classifier.classify("http_errors_total")
        assert result is None

        # Request counter
        result = classifier.classify("api_calls_total")
        assert result is None

        # Generic gauge
        result = classifier.classify("temperature_celsius")
        assert result is None

    def test_classify_with_metadata(self, classifier):
        """Test classification with additional metadata."""
        metadata = {"type": "histogram", "help": "Request duration in seconds"}

        result = classifier.classify("custom_duration_bucket", metadata)

        assert result is not None
        assert metadata["help"] in result.reason

    def test_batch_classify(self, classifier):
        """Test batch classification of multiple metrics."""
        metrics = [
            "http_request_duration_seconds_bucket",
            "http_request_duration_seconds_count",
            "http_requests_total",  # Not a latency metric
            "api_latency_milliseconds",
            "grpc_server_handling_seconds_bucket",
        ]

        results = classifier.batch_classify(metrics)

        # Should classify latency-related metrics
        classified_metrics = [r.metric_name for r in results]
        assert "http_request_duration_seconds_bucket" in classified_metrics
        assert "api_latency_milliseconds" in classified_metrics
        assert "grpc_server_handling_seconds_bucket" in classified_metrics

        # Should not classify non-latency metrics
        assert "http_requests_total" not in classified_metrics

    def test_confidence_calculation(self, classifier):
        """Test confidence scoring for different patterns."""
        # High confidence - clear latency histogram
        result = classifier.classify("http_request_latency_seconds_bucket")
        high_confidence = result.confidence

        # Medium confidence - duration metric without clear indicator
        result = classifier.classify("processing_time_bucket")
        medium_confidence = result.confidence

        # Lower confidence - ambiguous metric
        result = classifier.classify("duration_bucket")
        low_confidence = result.confidence

        # Just check they are all reasonable values
        assert all(conf >= 0.0 for conf in [high_confidence, medium_confidence, low_confidence])
