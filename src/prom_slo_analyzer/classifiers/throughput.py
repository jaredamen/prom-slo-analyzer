"""Throughput metric classifier for request rate and volume metrics."""

from typing import Any, Optional

from .base import BaseClassifier, ClassificationResult, SLIType


class ThroughputClassifier(BaseClassifier):
    """Classifies metrics suitable for throughput SLIs.

    Detects counter metrics that track request rates, transaction volumes,
    message processing rates, or other throughput indicators.
    """

    @property
    def sli_type(self) -> SLIType:
        return SLIType.THROUGHPUT

    def classify(self, metric_name: str, metadata: Optional[dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify metric for throughput SLI suitability.

        Looks for:
        - Request counter metrics (_requests_total, _processed_total, etc.)
        - Transaction/operation counters
        - Message/event processing counters
        - API call counters

        Args:
            metric_name: The Prometheus metric name
            metadata: Optional metric metadata

        Returns:
            ClassificationResult if metric is suitable for throughput SLI, None otherwise
        """

        # Check for request counters
        if self._is_request_counter(metric_name):
            return self._classify_request_counter(metric_name, metadata)

        # Check for processing counters
        if self._is_processing_counter(metric_name):
            return self._classify_processing_counter(metric_name, metadata)

        # Check for transaction counters
        if self._is_transaction_counter(metric_name):
            return self._classify_transaction_counter(metric_name, metadata)

        return None

    def _is_request_counter(self, metric_name: str) -> bool:
        """Check if metric is a request counter."""
        request_patterns = [
            "_requests_total",
            "_request_total",
            "_requests",
            "http_requests_total",
            "grpc_requests_total",
            "_calls_total",
            "_call_total",
            "_invocations_total",
            "_hits_total",
            "_accesses_total",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in request_patterns)

    def _is_processing_counter(self, metric_name: str) -> bool:
        """Check if metric tracks processing volume."""
        processing_patterns = [
            "_processed_total",
            "_processed",
            "_handled_total",
            "_completed_total",
            "_finished_total",
            "_executed_total",
            "_messages_total",
            "_events_total",
            "_items_total",
            "_operations_total",
            "_tasks_total",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in processing_patterns)

    def _is_transaction_counter(self, metric_name: str) -> bool:
        """Check if metric tracks transactions or business operations."""
        transaction_patterns = [
            "_transactions_total",
            "_transaction_total",
            "_orders_total",
            "_purchases_total",
            "_payments_total",
            "_uploads_total",
            "_downloads_total",
            "_queries_total",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in transaction_patterns)

    def _classify_request_counter(self, metric_name: str, metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify request counter for throughput SLI."""

        # High confidence for request counters
        positive_patterns = ["requests", "calls", "invocations", "hits", "accesses"]

        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(1.0, confidence + 0.4)  # High confidence for request metrics

        # Suggest PromQL for request rate
        suggested_promql = f"rate({metric_name}[5m])"

        reason = "Request counter suitable for throughput rate calculation"
        if metadata and metadata.get("help"):
            reason += f": {metadata['help']}"

        # Common labels for request metrics
        labels_needed = ["method", "endpoint", "path", "route", "handler"]

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed,
        )

    def _classify_processing_counter(
        self, metric_name: str, _metadata: Optional[dict[str, Any]]
    ) -> ClassificationResult:
        """Classify processing counter for throughput SLI."""

        positive_patterns = [
            "processed",
            "handled",
            "completed",
            "finished",
            "executed",
            "messages",
            "events",
            "items",
            "operations",
            "tasks",
        ]

        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.9, confidence + 0.3)  # Good confidence for processing metrics

        # Suggest PromQL for processing rate
        suggested_promql = f"rate({metric_name}[5m])"

        reason = "Processing counter suitable for throughput calculation"

        # Common labels for processing metrics
        labels_needed = ["queue", "topic", "worker", "processor", "type"]

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed,
        )

    def _classify_transaction_counter(
        self, metric_name: str, _metadata: Optional[dict[str, Any]]
    ) -> ClassificationResult:
        """Classify transaction counter for throughput SLI."""

        positive_patterns = ["transactions", "orders", "purchases", "payments", "uploads", "downloads", "queries"]

        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.85, confidence + 0.2)  # Good confidence for business metrics

        # Suggest PromQL for transaction rate
        suggested_promql = f"rate({metric_name}[5m])"

        reason = "Transaction counter suitable for business throughput calculation"

        # Common labels for transaction metrics
        labels_needed = ["status", "result", "type", "category", "user_type"]

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed,
        )
