"""Base classifier for metric classification."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class SLIType(Enum):
    """Types of SLIs that can be derived from metrics."""

    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    SATURATION = "saturation"
    AVAILABILITY = "availability"
    QUEUE_DEPTH = "queue_depth"
    CONNECTION_POOL = "connection_pool"
    CACHE_HIT_RATIO = "cache_hit_ratio"


@dataclass
class ClassificationResult:
    """Result of classifying a metric for SLI suitability."""

    metric_name: str
    sli_type: SLIType
    confidence: float  # 0.0 to 1.0
    suggested_promql: Optional[str] = None
    reason: Optional[str] = None
    labels_needed: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Ensure labels_needed is properly initialized."""
        if self.labels_needed is None:
            self.labels_needed = []


class BaseClassifier(ABC):
    """Abstract base class for metric classifiers.

    Each classifier implements logic to detect if a metric is suitable
    for a specific type of SLI (Service Level Indicator).
    """

    @property
    @abstractmethod
    def sli_type(self) -> SLIType:
        """The SLI type this classifier detects."""
        pass

    @abstractmethod
    def classify(self, metric_name: str, metadata: Optional[dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify a metric for SLI suitability.

        Args:
            metric_name: The Prometheus metric name to classify
            metadata: Optional metric metadata from Prometheus API

        Returns:
            ClassificationResult if the metric matches this SLI type, None otherwise
        """
        pass

    def batch_classify(
        self, metrics: list[str], metadata_map: Optional[dict[str, dict[str, Any]]] = None
    ) -> list[ClassificationResult]:
        """Classify multiple metrics.

        Args:
            metrics: List of metric names to classify
            metadata_map: Optional mapping of metric names to their metadata

        Returns:
            List of classification results (only successful classifications)
        """
        results = []
        metadata_map = metadata_map or {}

        for metric in metrics:
            metadata = metadata_map.get(metric)
            result = self.classify(metric, metadata)
            if result:
                results.append(result)

        return results

    def _calculate_confidence(
        self, metric_name: str, positive_patterns: list[str], negative_patterns: Optional[list[str]] = None
    ) -> float:
        """Calculate confidence score based on pattern matching.

        Args:
            metric_name: The metric name to evaluate
            positive_patterns: Patterns that increase confidence
            negative_patterns: Patterns that decrease confidence

        Returns:
            Confidence score between 0.0 and 1.0
        """
        negative_patterns = negative_patterns or []

        # Start with base confidence
        confidence = 0.0

        # Check positive patterns
        for pattern in positive_patterns:
            if pattern.lower() in metric_name.lower():
                confidence += 0.3  # Each positive match adds confidence

        # Check negative patterns
        for pattern in negative_patterns:
            if pattern.lower() in metric_name.lower():
                confidence -= 0.2  # Each negative match reduces confidence

        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, confidence))
