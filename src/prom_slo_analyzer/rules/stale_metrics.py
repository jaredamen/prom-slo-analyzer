"""Rule to detect services with stale metrics."""

from typing import List

from .base import BaseRule, GapResult, GapSeverity
from ..discovery import ServiceMetrics
from ..classifiers.base import ClassificationResult


class StaleMetricsRule(BaseRule):
    """Detects services with metrics that haven't received data recently.
    
    # TODO: Follow the pattern in missing_latency.py — identify services where
    # SLI-suitable metrics exist but haven't been updated recently, indicating
    # potential issues with data collection, service health, or instrumentation.
    # 
    # Implementation approach:
    # 1. Query Prometheus for latest timestamp on each metric
    # 2. Compare against current time to detect stale metrics
    # 3. Consider different staleness thresholds for different metric types
    # 4. Distinguish between completely stale (no recent data) and intermittent
    """
    
    @property
    def rule_name(self) -> str:
        return "Stale Metrics"
    
    def check(self, service: ServiceMetrics, classifications: List[ClassificationResult]) -> List[GapResult]:
        """Check if service has metrics that haven't been updated recently.
        
        # TODO: Implement stale metrics detection logic
        # This will require querying Prometheus to check the last update time for metrics
        # 1. For each classification, query last data point timestamp
        # 2. Calculate time since last update
        # 3. Apply staleness thresholds (e.g., 5 minutes for high-frequency, 1 hour for batch)
        # 4. Create gap results for metrics that are stale
        # 5. Group by severity (missing vs intermittent)
        
        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service
            
        Returns:
            List of gap results for stale metrics, empty list if all metrics are fresh
        """
        # TODO: Implement stale metrics detection logic
        # This would require access to PrometheusClient to query metric timestamps
        return []