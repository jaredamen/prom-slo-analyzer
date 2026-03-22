"""Latency metric classifier for histogram and summary metrics."""

from typing import Any, Optional

from .base import BaseClassifier, ClassificationResult, SLIType


class LatencyClassifier(BaseClassifier):
    """Classifies metrics suitable for latency SLIs.

    Detects histogram and summary metrics that measure request/response latency,
    operation duration, or processing time.
    """

    @property
    def sli_type(self) -> SLIType:
        return SLIType.LATENCY

    def classify(self, metric_name: str, metadata: Optional[dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify metric for latency SLI suitability.

        Looks for:
        - Histogram metrics (ending with _bucket, _count, _sum)
        - Summary metrics (ending with quantile indicators)
        - Duration/latency keywords in name
        - Time-based units (seconds, milliseconds, etc.)

        Args:
            metric_name: The Prometheus metric name
            metadata: Optional metric metadata

        Returns:
            ClassificationResult if metric is suitable for latency SLI, None otherwise
        """
        # Check if it's a histogram metric
        if self._is_histogram_metric(metric_name):
            return self._classify_histogram(metric_name, metadata)

        # Check if it's a summary metric
        if self._is_summary_metric(metric_name):
            return self._classify_summary(metric_name, metadata)

        # Check for direct latency/duration metrics
        if self._is_duration_metric(metric_name):
            return self._classify_duration(metric_name, metadata)

        return None

    def _is_histogram_metric(self, metric_name: str) -> bool:
        """Check if metric is a histogram type."""
        histogram_suffixes = ["_bucket", "_count", "_sum"]
        return any(metric_name.endswith(suffix) for suffix in histogram_suffixes)

    def _is_summary_metric(self, metric_name: str) -> bool:
        """Check if metric is a summary type."""
        # Summary metrics often have quantile in the name or labels
        return "_quantile" in metric_name.lower() or metric_name.endswith("_summary")

    def _is_duration_metric(self, metric_name: str) -> bool:
        """Check if metric measures duration/latency."""
        duration_patterns = [
            "latency",
            "duration",
            "response_time",
            "request_time",
            "processing_time",
            "execution_time",
            "roundtrip",
            "rtt",
            "delay",
            "wait_time",
        ]

        time_units = ["_seconds", "_milliseconds", "_microseconds", "_nanoseconds", "_ms", "_us", "_ns", "_time"]
        # More specific time unit patterns to avoid false positives
        time_unit_patterns = [
            r"_seconds$",
            r"seconds$",
            r"_ms$",
            r"_milliseconds$",
            r"_us$",
            r"_microseconds$",
            r"_ns$",
            r"_nanoseconds$",
        ]

        name_lower = metric_name.lower()

        # Check for duration keywords
        has_duration_keyword = any(pattern in name_lower for pattern in duration_patterns)

        # Check for time units (more specific matching)
        import re

        has_time_unit = any(unit in name_lower for unit in time_units) or any(
            re.search(pattern, name_lower) for pattern in time_unit_patterns
        )

        # Additional check: avoid classifying temperature or other non-time metrics
        non_time_keywords = [
            "temperature",
            "cpu",
            "memory",
            "disk",
            "network",
            "bytes",
            "percent",
            "celsius",
            "fahrenheit",
        ]
        has_non_time_keyword = any(keyword in name_lower for keyword in non_time_keywords)

        return (has_duration_keyword or has_time_unit) and not has_non_time_keyword

    def _classify_histogram(self, metric_name: str, metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify histogram metric for latency SLI."""

        # Determine the base metric name (remove _bucket, _count, _sum suffix)
        base_name = metric_name
        for suffix in ["_bucket", "_count", "_sum"]:
            if metric_name.endswith(suffix):
                base_name = metric_name[: -len(suffix)]
                break

        # Calculate confidence based on metric name patterns
        positive_patterns = [
            "latency",
            "duration",
            "response_time",
            "request_time",
            "http_request_duration",
            "grpc_server_handling_seconds",
            "processing_time",
            "execution_time",
        ]

        negative_patterns = ["batch", "queue", "size", "count", "total", "bytes"]

        confidence = self._calculate_confidence(base_name, positive_patterns, negative_patterns)

        # Boost confidence if it's clearly a latency histogram
        if any(pattern in base_name.lower() for pattern in ["latency", "duration", "response_time"]):
            confidence = min(1.0, confidence + 0.3)

        # Generate suggested PromQL for percentiles
        suggested_promql = f"histogram_quantile(0.95, rate({base_name}_bucket[5m]))"

        reason = "Histogram metric suitable for latency percentile calculations"
        if metadata and metadata.get("help"):
            reason += f": {metadata['help']}"

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=["le"],  # Histogram buckets use 'le' label
        )

    def _classify_summary(self, metric_name: str, _metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify summary metric for latency SLI."""

        positive_patterns = ["latency", "duration", "response_time", "request_time"]

        confidence = self._calculate_confidence(metric_name, positive_patterns)

        # Summaries are less preferred than histograms for latency SLIs
        confidence = min(0.8, confidence)

        suggested_promql = f'{metric_name}{{quantile="0.95"}}'

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason="Summary metric with pre-calculated quantiles",
            labels_needed=["quantile"],
        )

    def _classify_duration(self, metric_name: str, _metadata: Optional[dict[str, Any]]) -> ClassificationResult:
        """Classify direct duration metric for latency SLI."""

        positive_patterns = [
            "latency",
            "duration",
            "response_time",
            "request_time",
            "seconds",
            "milliseconds",
            "processing_time",
        ]

        confidence = self._calculate_confidence(metric_name, positive_patterns)

        # Direct duration metrics might need aggregation
        suggested_promql = f"rate({metric_name}[5m])"

        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason="Duration metric requiring aggregation for SLI",
            labels_needed=[],
        )
