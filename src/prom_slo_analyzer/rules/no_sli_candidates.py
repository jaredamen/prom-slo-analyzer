"""Rule to detect services with no SLI candidates."""

from typing import List

from .base import BaseRule, GapResult, GapSeverity
from ..discovery import ServiceMetrics
from ..classifiers.base import ClassificationResult


class NoSLICandidatesRule(BaseRule):
    """Detects services that exist in Prometheus but have no metrics suitable for SLIs.
    
    This identifies services that are being scraped but lack the fundamental metrics
    needed for any type of SLO.
    """
    
    @property
    def rule_name(self) -> str:
        return "No SLI Candidates"
    
    def check(self, service: ServiceMetrics, classifications: List[ClassificationResult]) -> List[GapResult]:
        """Check if service has any metrics suitable for SLIs.
        
        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service
            
        Returns:
            List containing gap result if no SLI candidates found, empty list otherwise
        """
        # If there are any classifications, service has SLI candidates
        if classifications:
            return []
        
        # If service has no metrics at all, it might not be properly instrumented
        if not service.metrics:
            severity = GapSeverity.CRITICAL
            message = f"Service '{service.name}' has no Prometheus metrics"
            recommendation = (
                "Service appears to be registered in Prometheus but has no metrics. "
                "Verify that the service is properly instrumented with a metrics library "
                "(e.g., prometheus_client for Python, micrometer for Java) and exposing metrics "
                "on the expected endpoint."
            )
        else:
            # Service has metrics but none are suitable for SLIs
            severity = GapSeverity.HIGH
            message = f"Service '{service.name}' has {len(service.metrics)} metrics but none are suitable for SLIs"
            recommendation = (
                "Service has metrics but they don't follow patterns suitable for SLOs. "
                "Consider adding standard SLI metrics: request counters (for throughput), "
                "error counters or HTTP status codes (for error rate), latency histograms "
                "(for response time), and health check metrics (for availability)."
            )
        
        return [GapResult(
            rule_name=self.rule_name,
            service_name=service.name,
            severity=severity,
            message=message,
            recommendation=recommendation,
            affected_metrics=service.metrics[:10]  # Include first 10 metrics as examples
        )]