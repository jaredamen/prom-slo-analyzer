"""Tests for ErrorRateClassifier."""

import pytest

from src.prom_slo_analyzer.classifiers.error_rate import ErrorRateClassifier
from src.prom_slo_analyzer.classifiers.base import SLIType


class TestErrorRateClassifier:
    """Tests for ErrorRateClassifier functionality."""
    
    @pytest.fixture
    def classifier(self):
        """Create ErrorRateClassifier instance for testing."""
        return ErrorRateClassifier()
    
    def test_sli_type(self, classifier):
        """Test SLI type property."""
        assert classifier.sli_type == SLIType.ERROR_RATE
    
    def test_is_error_counter(self, classifier):
        """Test error counter detection."""
        # Direct error counters
        assert classifier._is_error_counter("api_gateway_errors_total") is True
        assert classifier._is_error_counter("service_error_count") is True
        assert classifier._is_error_counter("http_failed_total") is True
        assert classifier._is_error_counter("transaction_failures_total") is True
        assert classifier._is_error_counter("request_faults_total") is True
        assert classifier._is_error_counter("connection_timeouts_total") is True
        assert classifier._is_error_counter("operation_retries_total") is True
        
        # Non-error counters
        assert classifier._is_error_counter("http_requests_total") is False
        assert classifier._is_error_counter("memory_usage_bytes") is False
        assert classifier._is_error_counter("cpu_seconds_total") is False
    
    def test_is_http_status_metric(self, classifier):
        """Test HTTP status metric detection.""" 
        assert classifier._is_http_status_metric("http_requests_total") is True
        assert classifier._is_http_status_metric("http_request_total") is True
        assert classifier._is_http_status_metric("requests_total") is True
        assert classifier._is_http_status_metric("http_responses_total") is True
        assert classifier._is_http_status_metric("api_status_code_total") is True
        
        # Non-HTTP status metrics
        assert classifier._is_http_status_metric("database_connections") is False
        assert classifier._is_http_status_metric("memory_usage_bytes") is False
    
    def test_is_exception_metric(self, classifier):
        """Test exception metric detection."""
        assert classifier._is_exception_metric("application_exceptions_total") is True
        assert classifier._is_exception_metric("service_panics_total") is True
        assert classifier._is_exception_metric("system_crashes_total") is True
        assert classifier._is_exception_metric("requests_rejected_total") is True
        
        # Non-exception metrics
        assert classifier._is_exception_metric("http_requests_total") is False
        assert classifier._is_exception_metric("cpu_usage_percent") is False
    
    def test_classify_direct_error_counter(self, classifier):
        """Test classification of direct error counters."""
        result = classifier.classify("api_gateway_errors_total")
        
        assert result is not None
        assert result.metric_name == "api_gateway_errors_total"
        assert result.sli_type == SLIType.ERROR_RATE
        assert result.confidence > 0.7  # High confidence for direct error metrics
        assert "rate(" in result.suggested_promql
        assert "api_gateway_requests_total" in result.suggested_promql  # Should reference total requests
    
    def test_classify_http_status_metric(self, classifier):
        """Test classification of HTTP status code metrics."""
        result = classifier.classify("http_requests_total")
        
        assert result is not None
        assert result.metric_name == "http_requests_total"
        assert result.sli_type == SLIType.ERROR_RATE
        assert result.confidence == 0.8  # Fixed confidence for HTTP metrics
        assert 'status=~"5.."' in result.suggested_promql  # Should filter for 5xx errors
        assert "status" in result.labels_needed or "code" in result.labels_needed
    
    def test_classify_exception_metric(self, classifier):
        """Test classification of exception metrics."""
        result = classifier.classify("application_exceptions_total")
        
        assert result is not None
        assert result.metric_name == "application_exceptions_total"
        assert result.sli_type == SLIType.ERROR_RATE
        assert result.confidence > 0.6
        assert "rate(" in result.suggested_promql
        assert "type" in result.labels_needed or "class" in result.labels_needed
    
    def test_classify_non_error_metric(self, classifier):
        """Test that non-error metrics are not classified."""
        # Success counter
        result = classifier.classify("successful_requests_total")
        assert result is None
        
        # Latency metric
        result = classifier.classify("request_duration_seconds")
        assert result is None
        
        # Memory metric
        result = classifier.classify("memory_usage_bytes")
        assert result is None
    
    def test_extract_base_name(self, classifier):
        """Test extraction of base service name from error metrics."""
        assert classifier._extract_base_name("api_gateway_errors_total") == "api_gateway"
        assert classifier._extract_base_name("user_service_failed_total") == "user_service"
        assert classifier._extract_base_name("payment_faults_total") == "payment"
        assert classifier._extract_base_name("order_timeouts_total") == "order"
        assert classifier._extract_base_name("auth_exceptions_total") == "auth"
        
        # Metrics without error suffixes should return unchanged
        assert classifier._extract_base_name("generic_metric") == "generic_metric"
    
    def test_classify_with_metadata(self, classifier):
        """Test classification with additional metadata."""
        metadata = {
            "type": "counter",
            "help": "Total number of failed requests"
        }
        
        result = classifier.classify("api_errors_total", metadata)
        
        assert result is not None
        assert metadata["help"] in result.reason
    
    def test_batch_classify(self, classifier):
        """Test batch classification of multiple metrics."""
        metrics = [
            "api_gateway_errors_total",
            "http_requests_total", 
            "user_service_exceptions_total",
            "memory_usage_bytes",  # Not an error metric
            "payment_failed_total"
        ]
        
        results = classifier.batch_classify(metrics)
        
        # Should classify error-related metrics
        classified_metrics = [r.metric_name for r in results]
        assert "api_gateway_errors_total" in classified_metrics
        assert "http_requests_total" in classified_metrics
        assert "user_service_exceptions_total" in classified_metrics
        assert "payment_failed_total" in classified_metrics
        
        # Should not classify non-error metrics
        assert "memory_usage_bytes" not in classified_metrics
    
    def test_confidence_levels(self, classifier):
        """Test different confidence levels for different error types."""
        # Direct error counter - should have highest confidence
        result = classifier.classify("api_errors_total")
        direct_confidence = result.confidence
        
        # HTTP status metric - should have good confidence
        result = classifier.classify("http_requests_total")
        http_confidence = result.confidence
        
        # Exception metric - should have good confidence
        result = classifier.classify("exceptions_total")
        exception_confidence = result.confidence
        
        # All should be reasonably high, with direct errors being highest
        assert direct_confidence >= 0.8
        assert http_confidence >= 0.7
        assert exception_confidence >= 0.7
        assert direct_confidence >= http_confidence