"""Service discovery and metric grouping from Prometheus metrics."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .client import PrometheusClient


@dataclass
class ServiceMetrics:
    """Represents metrics discovered for a specific service."""

    name: str
    namespace: Optional[str]
    metrics: list[str]
    labels: Optional[dict[str, set[str]]] = None  # label_name -> set of values

    def __post_init__(self) -> None:
        """Ensure labels is properly initialized."""
        if self.labels is None:
            self.labels = {}


class ServiceDiscovery:
    """Discovers services and groups metrics by service from Prometheus."""

    def __init__(self, client: PrometheusClient) -> None:
        """Initialize service discovery.

        Args:
            client: Prometheus client for API interactions
        """
        self.client = client

    def discover_services(self, namespace_filter: Optional[str] = None) -> list[ServiceMetrics]:
        """Discover services and their associated metrics.

        Args:
            namespace_filter: Optional namespace filter (e.g., 'production')

        Returns:
            List of discovered services with their metrics
        """
        metric_names = self.client.get_metric_names()

        # Group metrics by service
        service_groups = self._group_metrics_by_service(metric_names)

        services = []
        for service_name, metrics in service_groups.items():
            # Extract namespace and labels for this service
            namespace, labels = self._analyze_service_labels(metrics)

            # Apply namespace filter if specified
            if namespace_filter and namespace != namespace_filter:
                continue

            service = ServiceMetrics(name=service_name, namespace=namespace, metrics=metrics, labels=labels)
            services.append(service)

        return sorted(services, key=lambda s: s.name)

    def _group_metrics_by_service(self, metric_names: list[str]) -> dict[str, list[str]]:
        """Group metrics by inferred service name.

        Args:
            metric_names: List of all metric names

        Returns:
            Dictionary mapping service names to their metrics
        """
        service_groups = defaultdict(list)

        for metric in metric_names:
            service_name = self._infer_service_name(metric)
            if service_name:
                service_groups[service_name].append(metric)

        return dict(service_groups)

    def _infer_service_name(self, metric_name: str) -> Optional[str]:
        """Infer service name from metric name.

        Uses common patterns to extract service names from metrics:
        - service_name_metric_name (e.g., api_gateway_requests_total -> api_gateway)
        - metric_name{service="service_name"} (handled in label analysis)
        - namespace_service_metric (e.g., prod_api_requests_total -> api)

        Args:
            metric_name: Prometheus metric name

        Returns:
            Inferred service name or None if no pattern matches
        """
        # Skip system/infrastructure metrics
        if self._is_system_metric(metric_name):
            return None

        # Common service prefixes
        service_patterns = [
            # Direct service prefix patterns
            r"^([a-zA-Z][a-zA-Z0-9_]*?)_(?:requests?|http|errors?|latency|duration|status|health|up)_",
            r"^([a-zA-Z][a-zA-Z0-9_]*?)_(?:total|count|seconds?|bytes?|ratio)$",
            # Extract middle component as service name
            r"^[a-z]+_([a-zA-Z][a-zA-Z0-9_]*?)_(?:requests?|http|errors?|latency|duration)_",
        ]

        for pattern in service_patterns:
            match = re.match(pattern, metric_name)
            if match:
                service_name = match.group(1)
                # Filter out generic terms that aren't real service names
                if not self._is_generic_term(service_name):
                    return service_name

        # Fallback: use first component if it looks like a service name
        parts = metric_name.split("_")
        if len(parts) >= 2 and not self._is_generic_term(parts[0]):
            return parts[0]

        return None

    def _is_system_metric(self, metric_name: str) -> bool:
        """Check if metric is a system/infrastructure metric rather than application metric.

        Args:
            metric_name: Prometheus metric name

        Returns:
            True if this is a system metric that should be ignored
        """
        system_prefixes = [
            "prometheus_",
            "go_",
            "process_",
            "node_",
            "container_",
            "kubernetes_",
            "kube_",
            "cadvisor_",
            "up",
            "scrape_",
            "net_conntrack_",
            "rate_",
            "increase_",
            "histogram_quantile",
        ]

        return any(metric_name.startswith(prefix) for prefix in system_prefixes)

    def _is_generic_term(self, term: str) -> bool:
        """Check if term is too generic to be a service name.

        Args:
            term: Potential service name

        Returns:
            True if term is generic and should be filtered out
        """
        generic_terms = {
            "http",
            "https",
            "tcp",
            "udp",
            "grpc",
            "rest",
            "api",
            "request",
            "requests",
            "response",
            "responses",
            "error",
            "errors",
            "status",
            "health",
            "up",
            "down",
            "latency",
            "duration",
            "time",
            "seconds",
            "milliseconds",
            "count",
            "total",
            "sum",
            "avg",
            "max",
            "min",
            "bytes",
            "bits",
            "rate",
            "ratio",
            "percent",
            "gauge",
            "histogram",
            "summary",
            "counter",
            "metric",
        }

        return term.lower() in generic_terms or len(term) < 2

    def _analyze_service_labels(self, metrics: list[str]) -> tuple[Optional[str], dict[str, set[str]]]:
        """Analyze labels across all metrics for a service to extract common patterns.

        Args:
            metrics: List of metric names for this service

        Returns:
            Tuple of (namespace, labels_dict) where labels_dict maps label names to sets of values
        """
        all_labels = defaultdict(set)
        namespace = None

        # Sample a few metrics to get label information (avoid querying all)
        sample_metrics = metrics[:5]  # Limit to first 5 metrics for performance

        for metric in sample_metrics:
            labels = self.client.get_metric_labels(metric)

            for label_name in labels:
                # For now, just track that this label exists
                # In a real implementation, you'd query for actual values
                all_labels[label_name].add("*")  # Placeholder

                # Extract namespace from common label patterns
                if label_name in ["namespace", "ns"] and not namespace:
                    namespace = "detected"  # Placeholder - would extract actual value

        return namespace, dict(all_labels)
