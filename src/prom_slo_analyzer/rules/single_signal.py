"""Rule to detect services with only one SLI type."""

from typing import List

from .base import BaseRule, GapResult, GapSeverity
from ..discovery import ServiceMetrics
from ..classifiers.base import ClassificationResult


class SingleSignalRule(BaseRule):
    """Detects services that only have one type of SLI metric.
    
    # TODO: Follow the pattern in missing_latency.py — identify services that have
    # only one SLI type (e.g., only throughput, only error rate, only availability)
    # and recommend adding complementary metrics for more comprehensive SLO coverage.
    # 
    # A robust SLO strategy typically includes multiple signal types:
    # - Request-based services should have: throughput + error rate + latency
    # - Background services might have: throughput + error rate + queue depth
    # - Infrastructure services need: availability + saturation + error rate
    """
    
    @property
    def rule_name(self) -> str:
        return "Single SLI Signal Type"
    
    def check(self, service: ServiceMetrics, classifications: List[ClassificationResult]) -> List[GapResult]:
        """Check if service has only one type of SLI metric.
        
        # TODO: Implement single signal detection logic
        # 1. Group classifications by SLI type
        # 2. If only one SLI type is present, create a gap result
        # 3. Provide specific recommendations based on the existing signal type
        # 4. Set severity based on service type (request-based vs background vs infrastructure)
        
        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service
            
        Returns:
            List containing gap result if only one SLI type found, empty list otherwise
        """
        # TODO: Implement single signal detection logic
        return []