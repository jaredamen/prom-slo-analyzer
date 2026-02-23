"""Saturation metric classifier for resource utilization metrics."""

import re
from typing import Optional, Dict, Any

from .base import BaseClassifier, ClassificationResult, SLIType


class SaturationClassifier(BaseClassifier):
    """Classifies metrics suitable for saturation SLIs.
    
    Detects gauge metrics that track resource utilization, capacity usage,
    or other saturation indicators that can signal when services are approaching limits.
    """
    
    @property
    def sli_type(self) -> SLIType:
        return SLIType.SATURATION
    
    def classify(self, metric_name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify metric for saturation SLI suitability.
        
        Looks for:
        - Resource utilization metrics (CPU, memory, disk, etc.)
        - Capacity usage metrics (_usage, _utilization, _capacity)
        - Pool/queue size metrics
        - Connection/thread pool metrics
        - Cache utilization metrics
        
        Args:
            metric_name: The Prometheus metric name
            metadata: Optional metric metadata
            
        Returns:
            ClassificationResult if metric is suitable for saturation SLI, None otherwise
        """
        
        # Check for resource utilization metrics
        if self._is_resource_utilization(metric_name):
            return self._classify_resource_utilization(metric_name, metadata)
        
        # Check for capacity metrics
        if self._is_capacity_metric(metric_name):
            return self._classify_capacity_metric(metric_name, metadata)
            
        # Check for pool/queue metrics
        if self._is_pool_metric(metric_name):
            return self._classify_pool_metric(metric_name, metadata)
        
        return None
    
    def _is_resource_utilization(self, metric_name: str) -> bool:
        """Check if metric measures resource utilization."""
        resource_patterns = [
            '_cpu_usage', '_cpu_utilization', '_cpu_percent',
            '_memory_usage', '_memory_utilization', '_memory_percent',
            '_disk_usage', '_disk_utilization', '_disk_percent',
            '_network_usage', '_bandwidth_usage', '_io_usage'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in resource_patterns)
    
    def _is_capacity_metric(self, metric_name: str) -> bool:
        """Check if metric measures capacity or usage against limits."""
        capacity_patterns = [
            '_capacity', '_usage', '_utilization', '_used', '_consumed',
            '_limit', '_quota', '_allocation', '_reserved',
            '_available', '_free', '_remaining'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in capacity_patterns)
    
    def _is_pool_metric(self, metric_name: str) -> bool:
        """Check if metric measures pool or queue utilization."""
        pool_patterns = [
            '_pool_size', '_pool_usage', '_pool_utilization',
            '_queue_size', '_queue_length', '_queue_depth',
            '_buffer_size', '_buffer_usage', '_active_connections',
            '_thread_count', '_worker_count', '_pending_count'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in pool_patterns)
    
    def _classify_resource_utilization(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify resource utilization metric for saturation SLI."""
        
        # High confidence for resource utilization
        positive_patterns = [
            'cpu', 'memory', 'disk', 'network', 'bandwidth', 'io',
            'usage', 'utilization', 'percent'
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(1.0, confidence + 0.4)  # High confidence for resource metrics
        
        # Suggest PromQL for resource saturation threshold
        suggested_promql = f'{metric_name} > 0.8'  # 80% utilization threshold
        
        reason = "Resource utilization metric suitable for saturation monitoring"
        if metadata and metadata.get('help'):
            reason += f": {metadata['help']}"
        
        # Common labels for resource metrics
        labels_needed = ['instance', 'device', 'mount', 'interface', 'cpu']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )
    
    def _classify_capacity_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify capacity metric for saturation SLI."""
        
        positive_patterns = [
            'capacity', 'usage', 'utilization', 'used', 'consumed',
            'limit', 'quota', 'allocation'
        ]
        
        negative_patterns = [
            'available', 'free', 'remaining'  # These are inverse saturation metrics
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns, negative_patterns)
        confidence = min(0.9, confidence + 0.3)  # Good confidence for capacity metrics
        
        # Different PromQL depending on metric type
        if any(pattern in metric_name.lower() for pattern in ['available', 'free', 'remaining']):
            # For inverse metrics (available/free), low values indicate saturation
            suggested_promql = f'{metric_name} < 0.2'  # Less than 20% remaining
        else:
            # For usage metrics, high values indicate saturation
            suggested_promql = f'{metric_name} > 0.8'  # More than 80% used
        
        reason = "Capacity metric suitable for saturation threshold monitoring"
        
        # Common labels for capacity metrics
        labels_needed = ['resource', 'pool', 'namespace', 'service']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )
    
    def _classify_pool_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify pool/queue metric for saturation SLI."""
        
        positive_patterns = [
            'pool', 'queue', 'buffer', 'connections', 'threads', 'workers',
            'size', 'length', 'depth', 'count', 'pending', 'active'
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.85, confidence + 0.2)  # Good confidence for pool metrics
        
        # Pool metrics usually need to be compared against their maximum
        # This is a simplified example - real implementation might need max values
        suggested_promql = f'{metric_name} / {metric_name}_max > 0.8'
        
        reason = "Pool/queue metric suitable for saturation monitoring"
        
        # Common labels for pool metrics
        labels_needed = ['pool', 'queue', 'worker', 'type']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )