"""Shared test fixtures and mock data for prom-slo-analyzer tests."""

from unittest.mock import Mock

import pytest

from prom_slo_analyzer.classifiers.base import ClassificationResult, SLIType
from prom_slo_analyzer.client import PrometheusClient
from prom_slo_analyzer.discovery import ServiceMetrics


@pytest.fixture
def mock_prometheus_response():
    """Mock Prometheus API response data."""
    return {"status": "success", "data": []}


@pytest.fixture
def sample_metric_names():
    """Sample Prometheus metric names for testing."""
    return [
        # API Gateway metrics
        "api_gateway_requests_total",
        "api_gateway_request_duration_seconds_bucket",
        "api_gateway_request_duration_seconds_count",
        "api_gateway_request_duration_seconds_sum",
        "api_gateway_errors_total",
        # User Service metrics
        "user_service_http_requests_total",
        "user_service_http_request_duration_seconds_bucket",
        "user_service_database_connections_active",
        "user_service_memory_usage_bytes",
        # Payment Service metrics
        "payment_service_transactions_total",
        "payment_service_transaction_errors_total",
        "payment_service_transaction_duration_histogram_bucket",
        "payment_service_queue_size",
        # Infrastructure metrics (should be filtered out)
        "up",
        "prometheus_rule_evaluations_total",
        "go_memstats_alloc_bytes",
        "process_cpu_seconds_total",
        # Availability metrics
        "service_health_check",
        "endpoint_up",
        "payment_service_healthy",
    ]


@pytest.fixture
def mock_prometheus_client(sample_metric_names):
    """Mock PrometheusClient with realistic responses."""
    mock_client = Mock(spec=PrometheusClient)

    # Mock connectivity check
    mock_client.check_connectivity.return_value = True

    # Mock metric names
    mock_client.get_metric_names.return_value = sample_metric_names

    # Mock metadata responses
    def mock_get_metadata(metric_name: str):
        metadata_map = {
            "api_gateway_requests_total": {"type": "counter", "help": "Total number of HTTP requests to API gateway"},
            "api_gateway_request_duration_seconds_bucket": {"type": "histogram", "help": "Request duration in seconds"},
            "user_service_http_requests_total": {"type": "counter", "help": "Total HTTP requests to user service"},
            "payment_service_transactions_total": {"type": "counter", "help": "Total payment transactions processed"},
        }
        return metadata_map.get(metric_name)

    mock_client.get_metric_metadata.side_effect = mock_get_metadata

    # Mock label responses
    def mock_get_labels(metric_name: str):
        if "http" in metric_name.lower() or "request" in metric_name.lower() or "gateway" in metric_name.lower():
            return ["method", "status", "endpoint"]
        elif "transaction" in metric_name.lower():
            return ["type", "status", "payment_method"]
        return ["job", "instance"]

    mock_client.get_metric_labels.side_effect = mock_get_labels

    return mock_client


@pytest.fixture
def sample_services():
    """Sample discovered services for testing."""
    return [
        ServiceMetrics(
            name="api_gateway",
            namespace="production",
            metrics=[
                "api_gateway_requests_total",
                "api_gateway_request_duration_seconds_bucket",
                "api_gateway_request_duration_seconds_count",
                "api_gateway_request_duration_seconds_sum",
                "api_gateway_errors_total",
            ],
            labels={"method": {"GET", "POST"}, "status": {"200", "404", "500"}},
        ),
        ServiceMetrics(
            name="user_service",
            namespace="production",
            metrics=[
                "user_service_http_requests_total",
                "user_service_http_request_duration_seconds_bucket",
                "user_service_database_connections_active",
                "user_service_memory_usage_bytes",
            ],
            labels={"endpoint": {"/users", "/auth"}},
        ),
        ServiceMetrics(
            name="payment_service",
            namespace="production",
            metrics=[
                "payment_service_transactions_total",
                "payment_service_transaction_errors_total",
                "payment_service_transaction_duration_histogram_bucket",
                "payment_service_queue_size",
            ],
            labels={"payment_method": {"credit_card", "paypal"}},
        ),
        ServiceMetrics(
            name="incomplete_service",
            namespace="staging",
            metrics=["incomplete_service_requests_total"],  # Only throughput, missing latency/errors
            labels={},
        ),
        ServiceMetrics(
            name="no_sli_service",
            namespace="development",
            metrics=["no_sli_service_build_info", "no_sli_service_config_hash"],  # Not suitable for SLIs
            labels={},
        ),
    ]


@pytest.fixture
def sample_latency_classifications():
    """Sample latency classifications for testing."""
    return [
        ClassificationResult(
            metric_name="api_gateway_request_duration_seconds_bucket",
            sli_type=SLIType.LATENCY,
            confidence=0.9,
            suggested_promql="histogram_quantile(0.95, rate(api_gateway_request_duration_seconds_bucket[5m]))",
            reason="Histogram metric suitable for latency percentile calculations",
            labels_needed=["le"],
        ),
        ClassificationResult(
            metric_name="user_service_http_request_duration_seconds_bucket",
            sli_type=SLIType.LATENCY,
            confidence=0.9,
            suggested_promql="histogram_quantile(0.95, rate(user_service_http_request_duration_seconds_bucket[5m]))",
            reason="Histogram metric suitable for latency percentile calculations",
            labels_needed=["le"],
        ),
    ]


@pytest.fixture
def sample_error_classifications():
    """Sample error rate classifications for testing."""
    return [
        ClassificationResult(
            metric_name="api_gateway_errors_total",
            sli_type=SLIType.ERROR_RATE,
            confidence=0.9,
            suggested_promql="rate(api_gateway_errors_total[5m]) / rate(api_gateway_requests_total[5m])",
            reason="Direct error counter suitable for error rate calculation",
            labels_needed=[],
        ),
        ClassificationResult(
            metric_name="payment_service_transaction_errors_total",
            sli_type=SLIType.ERROR_RATE,
            confidence=0.9,
            suggested_promql="rate(payment_service_transaction_errors_total[5m]) / rate(payment_service_transactions_total[5m])",
            reason="Direct error counter suitable for error rate calculation",
            labels_needed=[],
        ),
    ]


@pytest.fixture
def sample_throughput_classifications():
    """Sample throughput classifications for testing."""
    return [
        ClassificationResult(
            metric_name="api_gateway_requests_total",
            sli_type=SLIType.THROUGHPUT,
            confidence=0.9,
            suggested_promql="rate(api_gateway_requests_total[5m])",
            reason="Request counter suitable for throughput rate calculation",
            labels_needed=["method", "endpoint", "path", "route", "handler"],
        ),
        ClassificationResult(
            metric_name="payment_service_transactions_total",
            sli_type=SLIType.THROUGHPUT,
            confidence=0.85,
            suggested_promql="rate(payment_service_transactions_total[5m])",
            reason="Transaction counter suitable for business throughput calculation",
            labels_needed=["status", "result", "type", "category", "user_type"],
        ),
    ]


@pytest.fixture
def all_sample_classifications(
    sample_latency_classifications, sample_error_classifications, sample_throughput_classifications
):
    """All sample classifications combined."""
    return sample_latency_classifications + sample_error_classifications + sample_throughput_classifications
