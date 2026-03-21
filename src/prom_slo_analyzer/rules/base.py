"""Base rule for gap detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..classifiers.base import ClassificationResult, SLIType
from ..discovery import ServiceMetrics


class GapSeverity(Enum):
    """Severity levels for SLO readiness gaps."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GapResult:
    """Result of a gap detection rule."""

    rule_name: str
    service_name: str
    severity: GapSeverity
    message: str
    recommendation: str
    affected_metrics: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Ensure affected_metrics is properly initialized."""
        if self.affected_metrics is None:
            self.affected_metrics = []


class BaseRule(ABC):
    """Abstract base class for gap detection rules.

    Each rule analyzes a service and its classified metrics to identify
    gaps in SLO readiness.
    """

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Name of this gap detection rule."""
        pass

    @abstractmethod
    def check(self, service: ServiceMetrics, classifications: list[ClassificationResult]) -> list[GapResult]:
        """Check for gaps in SLO readiness for a service.

        Args:
            service: The service to analyze
            classifications: List of metric classifications for this service

        Returns:
            List of gap results (empty list if no gaps found)
        """
        pass

    def _get_classifications_by_type(
        self, classifications: list[ClassificationResult], sli_type: SLIType
    ) -> list[ClassificationResult]:
        """Filter classifications by SLI type.

        Args:
            classifications: List of all classifications
            sli_type: SLI type to filter for (from SLIType enum)

        Returns:
            List of classifications matching the specified type
        """
        return [c for c in classifications if c.sli_type == sli_type]

    def _has_sli_type(self, classifications: list[ClassificationResult], sli_type: SLIType) -> bool:
        """Check if classifications contain a specific SLI type.

        Args:
            classifications: List of all classifications
            sli_type: SLI type to check for (from SLIType enum)

        Returns:
            True if any classification matches the SLI type
        """
        return len(self._get_classifications_by_type(classifications, sli_type)) > 0
