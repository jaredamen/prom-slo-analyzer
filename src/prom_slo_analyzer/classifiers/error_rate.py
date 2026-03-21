"""Error rate metric classifier for detecting error ratio metrics."""

from typing import Any, Optional

from .base import BaseClassifier, ClassificationResult, SLIType


class ErrorRateClassifier(BaseClassifier):
    """Classifies metrics suitable for error rate SLIs.

    Detects counter metrics that track errors, failures, or HTTP error status codes
    that can be used to calculate error ratios.
    """

    @property
    def sli_type(self) -> SLIType:
        return SLIType.ERROR_RATE

    def classify(self, metric_name: str, metadata: Optional[dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify metric for error rate SLI suitability.

        Looks for:
        - Error/failure counter metrics (_errors_total, _failed_total, etc.)
        - HTTP status code metrics with error status codes
        - Exception/fault counters
        - Retry/timeout counters

        Args:
            metric_name: The Prometheus metric name
            metadata: Optional metric metadata

        Returns:
            ClassificationResult if metric is suitable for error rate SLI, None otherwise
        """

        # Check for direct error counters
        if self._is_error_counter(metric_name):
            return self._classify_error_counter(metric_name, metadata)

        # Check for HTTP status code metrics
        if self._is_http_status_metric(metric_name):
            return self._classify_http_status(metric_name, metadata)

        # Check for exception/failure metrics
        if self._is_exception_metric(metric_name):
            return self._classify_exception(metric_name, metadata)

        return None

    def _is_error_counter(self, metric_name: str) -> bool:
        """Check if metric is a direct error counter."""
        error_patterns = [
            "_errors_total",
            "_error_total",
            "_errors",
            "_error_count",
            "_failed_total",
            "_failures_total",
            "_failure_total",
            "_faults_total",
            "_fault_total",
            "_timeouts_total",
            "_retries_total",
            "_retry_total",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in error_patterns)

    def _is_http_status_metric(self, metric_name: str) -> bool:
        """Check if metric tracks HTTP status codes."""
        http_patterns = [
            "http_requests_total",
            "http_request_total",
            "requests_total",
            "http_responses_total",
            "response_total",
            "status_code",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in http_patterns)

    def _is_exception_metric(self, metric_name: str) -> bool:
        """Check if metric tracks exceptions or application errors."""
        exception_patterns = [
            "exceptions_total",
            "exception_total",
            "panics_total",
            "crashes_total",
            "abort_total",
            "rejected_total",
        ]

        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in exception_patterns)

    def _classify_error_counter(self, metric_name: str, metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify direct error counter for error rate SLI."""

        # High confidence for direct error counters
        positive_patterns = ["errors", "failed", "failures", "faults", "timeouts", "retries"]

        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(1.0, confidence + 0.4)  # High confidence for direct error metrics

        # Suggest PromQL for error rate calculation
        # This assumes there's a corresponding total requests metric
        base_name = self._extract_base_name(metric_name)
        suggested_promql = f"rate({metric_name}[5m]) / rate({base_name}_requests_total[5m])"

        reason = "Direct error counter suitable for error rate calculation"
        if metadata and metadata.get("help"):
            reason += f": {metadata['help']}"

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=[],
        )

    def _classify_http_status(self, metric_name: str, _metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify HTTP status code metric for error rate SLI."""

        confidence = 0.8  # Good confidence for HTTP metrics

        # PromQL to calculate 5xx error rate
        suggested_promql = f'rate({metric_name}{{{{status=~"5.."}}}}[5m]) / ' f"rate({metric_name}[5m])"

        reason = "HTTP status code metric suitable for 5xx error rate calculation"

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=["status", "code", "status_code"],  # Common HTTP status labels
        )

    def _classify_exception(self, metric_name: str, _metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify exception metric for error rate SLI."""

        positive_patterns = ["exceptions", "panics", "crashes", "abort", "rejected"]

        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.9, confidence + 0.3)  # High confidence for exception metrics

        # Suggest PromQL for exception rate
        base_name = self._extract_base_name(metric_name)
        suggested_promql = f"rate({metric_name}[5m]) / rate({base_name}_requests_total[5m])"

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason="Exception/fault metric suitable for error rate calculation",
            labels_needed=["type", "class", "exception_type"],  # Common exception labels
        )

    def _extract_base_name(self, metric_name: str) -> str:
        """Extract base service name from error metric for building total request metric name.

        Args:
            metric_name: Full metric name (e.g., 'api_gateway_errors_total')

        Returns:
            Base name (e.g., 'api_gateway')
        """
        # Remove common error suffixes
        error_suffixes = [
            "_errors_total",
            "_error_total",
            "_errors",
            "_error_count",
            "_failed_total",
            "_failures_total",
            "_failure_total",
            "_faults_total",
            "_fault_total",
            "_timeouts_total",
            "_retries_total",
            "_retry_total",
            "_exceptions_total",
        ]

        base_name = metric_name
        for suffix in error_suffixes:
            if metric_name.endswith(suffix):
                base_name = metric_name[: -len(suffix)]
                break

        return base_name
