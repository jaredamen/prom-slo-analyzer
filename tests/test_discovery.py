"""Tests for service discovery functionality."""

from prom_slo_analyzer.discovery import ServiceDiscovery, ServiceMetrics


class TestServiceDiscovery:
    """Tests for ServiceDiscovery functionality."""

    def test_init(self, mock_prometheus_client):
        """Test ServiceDiscovery initialization."""
        discovery = ServiceDiscovery(mock_prometheus_client)
        assert discovery.client == mock_prometheus_client

    def test_discover_services(self, mock_prometheus_client, sample_metric_names):
        """Test service discovery from metrics."""
        discovery = ServiceDiscovery(mock_prometheus_client)
        services = discovery.discover_services()

        # Should discover services based on metric patterns
        service_names = [s.name for s in services]
        assert "api_gateway" in service_names
        assert "user_service" in service_names
        assert "payment_service" in service_names

        # Should not include system metrics as services
        assert "prometheus" not in service_names
        assert "go" not in service_names
        assert "process" not in service_names

    def test_discover_services_with_namespace_filter(self, mock_prometheus_client, sample_metric_names):
        """Test service discovery with namespace filtering."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        # Mock the _analyze_service_labels to return different namespaces

        def mock_analyze_labels(metrics):
            if any("api_gateway" in m for m in metrics):
                return "production", {}
            elif any("user_service" in m for m in metrics):
                return "staging", {}
            else:
                return "development", {}

        discovery._analyze_service_labels = mock_analyze_labels

        # Filter by production namespace
        services = discovery.discover_services(namespace_filter="production")
        service_names = [s.name for s in services]

        # Should only include api_gateway (mocked as production)
        assert "api_gateway" in service_names
        assert len([s for s in services if s.name == "api_gateway"]) == 1

    def test_group_metrics_by_service(self, mock_prometheus_client):
        """Test grouping metrics by inferred service name."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        metrics = [
            "api_gateway_requests_total",
            "api_gateway_errors_total",
            "api_gateway_latency_histogram_bucket",
            "user_service_http_requests_total",
            "user_service_database_connections",
            "payment_processor_transactions_total",
            "payment_processor_queue_depth",
            "up",  # System metric - should be filtered out
            "prometheus_rule_evaluations_total",  # System metric - should be filtered out
        ]

        grouped = discovery._group_metrics_by_service(metrics)

        # Should group by service prefix
        assert "api_gateway" in grouped
        assert "user_service" in grouped
        assert "payment_processor" in grouped

        # Check correct grouping
        assert "api_gateway_requests_total" in grouped["api_gateway"]
        assert "api_gateway_errors_total" in grouped["api_gateway"]
        assert "user_service_http_requests_total" in grouped["user_service"]

        # System metrics should not create services
        assert "up" not in grouped
        assert "prometheus" not in grouped

    def test_infer_service_name(self, mock_prometheus_client):
        """Test service name inference from metric names."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        # Test various service name patterns
        assert discovery._infer_service_name("api_gateway_requests_total") == "api_gateway"
        assert discovery._infer_service_name("user_service_http_requests_total") == "user_service"
        assert discovery._infer_service_name("payment_transactions_total") == "payment"
        assert discovery._infer_service_name("order_processing_latency_seconds") == "order"

        # Test system metrics (should return None)
        assert discovery._infer_service_name("up") is None
        assert discovery._infer_service_name("prometheus_rule_evaluations_total") is None
        assert discovery._infer_service_name("go_memstats_alloc_bytes") is None
        assert discovery._infer_service_name("process_cpu_seconds_total") is None

        # Test generic terms (should return None)
        assert discovery._infer_service_name("http_requests_total") is None
        assert discovery._infer_service_name("request_duration_seconds") is None

    def test_is_system_metric(self, mock_prometheus_client):
        """Test system metric detection."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        # System metrics should be detected
        assert discovery._is_system_metric("prometheus_rule_evaluations_total") is True
        assert discovery._is_system_metric("go_memstats_alloc_bytes") is True
        assert discovery._is_system_metric("process_cpu_seconds_total") is True
        assert discovery._is_system_metric("node_cpu_seconds_total") is True
        assert discovery._is_system_metric("container_memory_usage_bytes") is True
        assert discovery._is_system_metric("up") is True
        assert discovery._is_system_metric("scrape_duration_seconds") is True

        # Application metrics should not be detected as system
        assert discovery._is_system_metric("api_gateway_requests_total") is False
        assert discovery._is_system_metric("user_service_http_requests_total") is False
        assert discovery._is_system_metric("payment_transactions_total") is False

    def test_is_generic_term(self, mock_prometheus_client):
        """Test generic term detection."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        # Generic terms should be detected
        assert discovery._is_generic_term("http") is True
        assert discovery._is_generic_term("api") is True
        assert discovery._is_generic_term("request") is True
        assert discovery._is_generic_term("error") is True
        assert discovery._is_generic_term("latency") is True
        assert discovery._is_generic_term("total") is True
        assert discovery._is_generic_term("count") is True

        # Service names should not be generic
        assert discovery._is_generic_term("api_gateway") is False
        assert discovery._is_generic_term("user_service") is False
        assert discovery._is_generic_term("payment") is False
        assert discovery._is_generic_term("orders") is False

        # Very short terms should be generic
        assert discovery._is_generic_term("a") is True
        assert discovery._is_generic_term("") is True

    def test_analyze_service_labels(self, mock_prometheus_client):
        """Test service label analysis."""
        discovery = ServiceDiscovery(mock_prometheus_client)

        metrics = ["api_gateway_requests_total", "api_gateway_errors_total"]

        namespace, labels = discovery._analyze_service_labels(metrics)

        # Should return detected labels (mocked to return common HTTP labels)
        assert isinstance(labels, dict)
        # The mock returns method, status, endpoint for HTTP-related metrics
        assert "method" in labels or "status" in labels or "endpoint" in labels


class TestServiceMetrics:
    """Tests for ServiceMetrics data class."""

    def test_service_metrics_creation(self):
        """Test ServiceMetrics creation and initialization."""
        service = ServiceMetrics(
            name="test_service",
            namespace="production",
            metrics=["metric1", "metric2"],
            labels={"label1": {"value1", "value2"}},
        )

        assert service.name == "test_service"
        assert service.namespace == "production"
        assert service.metrics == ["metric1", "metric2"]
        assert service.labels == {"label1": {"value1", "value2"}}

    def test_service_metrics_post_init(self):
        """Test ServiceMetrics post-initialization."""
        # Test with None labels (should be converted to empty dict)
        service = ServiceMetrics(name="test_service", namespace=None, metrics=[], labels=None)

        assert service.labels == {}

        # Test with proper labels dict
        service = ServiceMetrics(name="test_service", namespace=None, metrics=[], labels={"key": {"value"}})

        assert service.labels == {"key": {"value"}}
