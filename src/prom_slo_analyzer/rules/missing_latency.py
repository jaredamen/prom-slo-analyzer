"""Rule to detect services missing latency metrics."""

from ..classifiers.base import ClassificationResult, SLIType
from ..discovery import ServiceMetrics
from .base import BaseRule, GapResult, GapSeverity


class MissingLatencyRule(BaseRule):
    """Detects services that have error rate and/or throughput metrics but lack latency metrics.

    This is a common gap where services track requests and errors but don't measure
    response times, making it impossible to set latency-based SLOs.
    """

    @property
    def rule_name(self) -> str:
        return "Missing Latency Metrics"

    def check(self, service: ServiceMetrics, classifications: list[ClassificationResult]) -> list[GapResult]:
        """Check if service has error/throughput metrics but lacks latency metrics.

        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service

        Returns:
            List containing gap result if latency metrics are missing, empty list otherwise
        """
        # Check if service has latency metrics
        has_latency = self._has_sli_type(classifications, SLIType.LATENCY)

        # If latency metrics exist, no gap
        if has_latency:
            return []

        # Check if service has other request-related metrics
        has_error_rate = self._has_sli_type(classifications, SLIType.ERROR_RATE)
        has_throughput = self._has_sli_type(classifications, SLIType.THROUGHPUT)

        # Only flag as a gap if service handles requests (has error rate OR throughput)
        if not (has_error_rate or has_throughput):
            return []

        # Determine severity based on what metrics are available
        if has_error_rate and has_throughput:
            severity = GapSeverity.HIGH
            message = f"Service '{service.name}' tracks both errors and throughput but lacks latency metrics"
        elif has_throughput:
            severity = GapSeverity.MEDIUM
            message = f"Service '{service.name}' tracks request throughput but lacks latency metrics"
        else:  # has_error_rate
            severity = GapSeverity.MEDIUM
            message = f"Service '{service.name}' tracks errors but lacks latency metrics"

        recommendation = (
            "Add histogram metrics for request/response latency. "
            "Consider instrumenting with metrics like 'http_request_duration_seconds' "
            "or 'grpc_server_handling_seconds' to enable latency-based SLOs."
        )

        # Get the names of metrics that suggest this service handles requests
        affected_metrics = []
        for classification in classifications:
            if classification.sli_type in [SLIType.ERROR_RATE, SLIType.THROUGHPUT]:
                affected_metrics.append(classification.metric_name)

        return [
            GapResult(
                rule_name=self.rule_name,
                service_name=service.name,
                severity=severity,
                message=message,
                recommendation=recommendation,
                affected_metrics=affected_metrics,
            )
        ]
