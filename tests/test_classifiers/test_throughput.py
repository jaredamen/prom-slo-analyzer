"""Tests for ThroughputClassifier."""

import pytest

from prom_slo_analyzer.classifiers.base import SLIType
from prom_slo_analyzer.classifiers.throughput import ThroughputClassifier


class TestThroughputClassifier:
    """Tests for ThroughputClassifier functionality."""

    @pytest.fixture
    def classifier(self):
        """Create ThroughputClassifier instance for testing."""
        return ThroughputClassifier()

    def test_sli_type(self, classifier):
        """Test SLI type property."""
        assert classifier.sli_type == SLIType.THROUGHPUT

    def test_is_request_counter(self, classifier):
        """Test request counter detection."""
        # Request counters
        assert classifier._is_request_counter("http_requests_total") is True
        assert classifier._is_request_counter("api_request_total") is True
        assert classifier._is_request_counter("service_requests") is True
        assert classifier._is_request_counter("grpc_requests_total") is True
        assert classifier._is_request_counter("api_calls_total") is True
        assert classifier._is_request_counter("endpoint_invocations_total") is True
        assert classifier._is_request_counter("cache_hits_total") is True
        assert classifier._is_request_counter("database_accesses_total") is True

        # Non-request counters
        assert classifier._is_request_counter("memory_usage_bytes") is False
        assert classifier._is_request_counter("cpu_seconds_total") is False
        assert classifier._is_request_counter("errors_total") is False

    def test_is_processing_counter(self, classifier):
        """Test processing counter detection."""
        assert classifier._is_processing_counter("messages_processed_total") is True
        assert classifier._is_processing_counter("tasks_handled_total") is True
        assert classifier._is_processing_counter("jobs_completed_total") is True
        assert classifier._is_processing_counter("events_finished_total") is True
        assert classifier._is_processing_counter("operations_executed_total") is True
        assert classifier._is_processing_counter("queue_items_total") is True

        # Non-processing counters
        assert classifier._is_processing_counter("http_requests_total") is False
        assert classifier._is_processing_counter("memory_usage_bytes") is False

    def test_is_transaction_counter(self, classifier):
        """Test transaction counter detection."""
        assert classifier._is_transaction_counter("payment_transactions_total") is True
        assert classifier._is_transaction_counter("ecommerce_orders_total") is True
        assert classifier._is_transaction_counter("purchases_total") is True
        assert classifier._is_transaction_counter("file_uploads_total") is True
        assert classifier._is_transaction_counter("data_downloads_total") is True
        assert classifier._is_transaction_counter("database_queries_total") is True

        # Non-transaction counters
        assert classifier._is_transaction_counter("http_requests_total") is False
        assert classifier._is_transaction_counter("cpu_usage_percent") is False

    def test_classify_request_counter(self, classifier):
        """Test classification of request counters."""
        result = classifier.classify("http_requests_total")

        assert result is not None
        assert result.metric_name == "http_requests_total"
        assert result.sli_type == SLIType.THROUGHPUT
        assert result.confidence >= 0.7  # High confidence for request metrics
        assert result.suggested_promql == "rate(http_requests_total[5m])"
        assert "method" in result.labels_needed
        assert "endpoint" in result.labels_needed

    def test_classify_processing_counter(self, classifier):
        """Test classification of processing counters."""
        result = classifier.classify("messages_processed_total")

        assert result is not None
        assert result.metric_name == "messages_processed_total"
        assert result.sli_type == SLIType.THROUGHPUT
        assert result.confidence >= 0.6  # Good confidence for processing metrics
        assert result.suggested_promql == "rate(messages_processed_total[5m])"
        assert "queue" in result.labels_needed or "topic" in result.labels_needed

    def test_classify_transaction_counter(self, classifier):
        """Test classification of transaction counters."""
        result = classifier.classify("payment_transactions_total")

        assert result is not None
        assert result.metric_name == "payment_transactions_total"
        assert result.sli_type == SLIType.THROUGHPUT
        assert result.confidence >= 0.5  # Good confidence for business metrics
        assert result.suggested_promql == "rate(payment_transactions_total[5m])"
        assert "status" in result.labels_needed or "type" in result.labels_needed

    def test_classify_non_throughput_metric(self, classifier):
        """Test that non-throughput metrics are not classified."""
        # Error counter
        result = classifier.classify("http_errors_total")
        assert result is None

        # Latency metric
        result = classifier.classify("request_duration_seconds")
        assert result is None

        # Memory metric
        result = classifier.classify("memory_usage_bytes")
        assert result is None

        # Gauge metric
        result = classifier.classify("active_connections")
        assert result is None

    def test_classify_with_metadata(self, classifier):
        """Test classification with additional metadata."""
        metadata = {"type": "counter", "help": "Total number of HTTP requests"}

        result = classifier.classify("api_requests_total", metadata)

        assert result is not None
        assert metadata["help"] in result.reason

    def test_batch_classify(self, classifier):
        """Test batch classification of multiple metrics."""
        metrics = [
            "http_requests_total",
            "api_calls_total",
            "messages_processed_total",
            "payment_transactions_total",
            "memory_usage_bytes",  # Not a throughput metric
            "request_duration_seconds",  # Not a throughput metric
        ]

        results = classifier.batch_classify(metrics)

        # Should classify throughput-related metrics
        classified_metrics = [r.metric_name for r in results]
        assert "http_requests_total" in classified_metrics
        assert "api_calls_total" in classified_metrics
        assert "messages_processed_total" in classified_metrics
        assert "payment_transactions_total" in classified_metrics

        # Should not classify non-throughput metrics
        assert "memory_usage_bytes" not in classified_metrics
        assert "request_duration_seconds" not in classified_metrics

    def test_confidence_levels(self, classifier):
        """Test confidence levels for different throughput types."""
        # Request counter - should have highest confidence
        result = classifier.classify("http_requests_total")
        request_confidence = result.confidence

        # Processing counter - should have good confidence
        result = classifier.classify("messages_processed_total")
        processing_confidence = result.confidence

        # Transaction counter - should have good confidence
        result = classifier.classify("ecommerce_orders_total")
        transaction_confidence = result.confidence if result else 0.0

        # Request counters should have highest confidence
        assert request_confidence >= 0.8
        assert processing_confidence >= 0.6
        assert transaction_confidence >= 0.6
        assert request_confidence >= processing_confidence
        assert request_confidence >= transaction_confidence

    def test_suggested_promql_format(self, classifier):
        """Test that suggested PromQL follows expected format."""
        metrics = ["http_requests_total", "messages_processed_total", "payment_transactions_total"]

        for metric in metrics:
            result = classifier.classify(metric)
            assert result is not None

            # All throughput metrics should use rate() function
            assert result.suggested_promql.startswith("rate(")
            assert result.suggested_promql.endswith("[5m])")
            assert metric in result.suggested_promql

    def test_labels_needed_appropriateness(self, classifier):
        """Test that labels_needed are appropriate for metric types."""
        # HTTP request metrics should have HTTP-related labels
        result = classifier.classify("http_requests_total")
        http_labels = set(result.labels_needed)
        expected_http_labels = {"method", "endpoint", "path", "route", "handler"}
        assert len(http_labels.intersection(expected_http_labels)) > 0

        # Processing metrics should have processing-related labels
        result = classifier.classify("messages_processed_total")
        processing_labels = set(result.labels_needed)
        expected_processing_labels = {"queue", "topic", "worker", "processor", "type"}
        assert len(processing_labels.intersection(expected_processing_labels)) > 0

        # Transaction metrics should have business-related labels
        result = classifier.classify("payment_transactions_total")
        transaction_labels = set(result.labels_needed)
        expected_transaction_labels = {"status", "result", "type", "category", "user_type"}
        assert len(transaction_labels.intersection(expected_transaction_labels)) > 0
