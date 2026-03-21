"""Rule to detect services missing error rate metrics."""

from ..classifiers.base import ClassificationResult, SLIType
from ..discovery import ServiceMetrics
from .base import BaseRule, GapResult, GapSeverity


class MissingErrorRateRule(BaseRule):
    """Detects services that have latency and/or throughput metrics but lack error rate metrics.

    This identifies services that can measure request volume and response times but
    cannot distinguish between successful and failed requests.
    """

    @property
    def rule_name(self) -> str:
        return "Missing Error Rate Metrics"

    def check(self, service: ServiceMetrics, classifications: list[ClassificationResult]) -> list[GapResult]:
        """Check if service has latency/throughput metrics but lacks error rate metrics.

        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service

        Returns:
            List containing gap result if error rate metrics are missing, empty list otherwise
        """
        # Check if service has error rate metrics
        has_error_rate = self._has_sli_type(classifications, SLIType.ERROR_RATE)

        # If error rate metrics exist, no gap
        if has_error_rate:
            return []

        # Check if service has other request-related metrics
        has_latency = self._has_sli_type(classifications, SLIType.LATENCY)
        has_throughput = self._has_sli_type(classifications, SLIType.THROUGHPUT)

        # Only flag as a gap if service handles requests (has latency OR throughput)
        if not (has_latency or has_throughput):
            return []

        # Determine severity based on what metrics are available
        if has_latency and has_throughput:
            severity = GapSeverity.HIGH
            message = f"Service '{service.name}' tracks both latency and throughput but lacks error rate metrics"
        elif has_latency:
            severity = GapSeverity.MEDIUM
            message = f"Service '{service.name}' tracks request latency but lacks error rate metrics"
        else:  # has_throughput
            severity = GapSeverity.MEDIUM
            message = f"Service '{service.name}' tracks request throughput but lacks error rate metrics"

        recommendation = (
            "Add error tracking metrics to distinguish successful from failed requests. "
            "Consider adding HTTP status code labels to request counters, or separate error counters "
            "like '{service}_errors_total' to enable error rate SLOs."
        ).replace("{service}", service.name.lower())

        # Get the names of metrics that suggest this service handles requests
        affected_metrics = []
        for classification in classifications:
            if classification.sli_type in [SLIType.LATENCY, SLIType.THROUGHPUT]:
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
