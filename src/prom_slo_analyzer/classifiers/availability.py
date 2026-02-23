"""Availability metric classifier for up/health check metrics."""

import re
from typing import Optional, Dict, Any

from .base import BaseClassifier, ClassificationResult, SLIType


class AvailabilityClassifier(BaseClassifier):
    """Classifies metrics suitable for availability SLIs.
    
    Detects gauge metrics that track service health, uptime status,
    or other availability indicators.
    """
    
    @property
    def sli_type(self) -> SLIType:
        return SLIType.AVAILABILITY
    
    def classify(self, metric_name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[ClassificationResult]:
        """Classify metric for availability SLI suitability.
        
        Looks for:
        - 'up' metrics (standard Prometheus convention)
        - Health check metrics (_healthy, _alive, _ready)
        - Status/state metrics (_status, _state)
        - Probe result metrics
        
        Args:
            metric_name: The Prometheus metric name
            metadata: Optional metric metadata
            
        Returns:
            ClassificationResult if metric is suitable for availability SLI, None otherwise
        """
        
        # Check for 'up' metrics (highest confidence)
        if self._is_up_metric(metric_name):
            return self._classify_up_metric(metric_name, metadata)
        
        # Check for health check metrics
        if self._is_health_metric(metric_name):
            return self._classify_health_metric(metric_name, metadata)
            
        # Check for status/state metrics
        if self._is_status_metric(metric_name):
            return self._classify_status_metric(metric_name, metadata)
            
        # Check for probe metrics
        if self._is_probe_metric(metric_name):
            return self._classify_probe_metric(metric_name, metadata)
        
        return None
    
    def _is_up_metric(self, metric_name: str) -> bool:
        """Check if metric is the standard 'up' metric."""
        return metric_name == 'up' or metric_name.endswith('_up')
    
    def _is_health_metric(self, metric_name: str) -> bool:
        """Check if metric measures health status."""
        health_patterns = [
            '_healthy', '_health', '_alive', '_ready', '_available',
            '_running', '_active', '_enabled', '_online'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in health_patterns)
    
    def _is_status_metric(self, metric_name: str) -> bool:
        """Check if metric measures service status or state."""
        status_patterns = [
            '_status', '_state', '_condition', '_mode'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in status_patterns)
    
    def _is_probe_metric(self, metric_name: str) -> bool:
        """Check if metric is from health probes."""
        probe_patterns = [
            'probe_success', 'probe_duration', 'healthcheck',
            'liveness', 'readiness', 'startup'
        ]
        
        name_lower = metric_name.lower()
        return any(pattern in name_lower for pattern in probe_patterns)
    
    def _classify_up_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify 'up' metric for availability SLI."""
        
        # Maximum confidence for 'up' metrics - this is the Prometheus standard
        confidence = 1.0
        
        # Standard PromQL for availability calculation
        suggested_promql = f'avg_over_time({metric_name}[5m])'
        
        reason = "Standard Prometheus 'up' metric indicating target availability"
        if metadata and metadata.get('help'):
            reason += f": {metadata['help']}"
        
        # Common labels for 'up' metrics
        labels_needed = ['job', 'instance']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )
    
    def _classify_health_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify health check metric for availability SLI."""
        
        # High confidence for health metrics
        positive_patterns = [
            'healthy', 'health', 'alive', 'ready', 'available',
            'running', 'active', 'enabled', 'online'
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.95, confidence + 0.4)  # Very high confidence for health metrics
        
        # PromQL for health-based availability
        suggested_promql = f'avg_over_time({metric_name}[5m])'
        
        reason = "Health check metric suitable for availability monitoring"
        
        # Common labels for health metrics
        labels_needed = ['service', 'component', 'check_type', 'endpoint']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )
    
    def _classify_status_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify status/state metric for availability SLI."""
        
        positive_patterns = [
            'status', 'state', 'condition', 'mode'
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.8, confidence + 0.2)  # Good confidence for status metrics
        
        # Status metrics might need value interpretation (e.g., status == 1 means up)
        suggested_promql = f'{metric_name} == 1'
        
        reason = "Status/state metric that may indicate availability"
        
        # Common labels for status metrics  
        labels_needed = ['status', 'state', 'value', 'condition']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )
    
    def _classify_probe_metric(self, metric_name: str, metadata: Optional[Dict[str, Any]]) -> ClassificationResult:
        """Classify probe metric for availability SLI."""
        
        positive_patterns = [
            'probe', 'success', 'healthcheck', 'liveness', 'readiness', 'startup'
        ]
        
        confidence = self._calculate_confidence(metric_name, positive_patterns)
        confidence = min(0.9, confidence + 0.3)  # High confidence for probe metrics
        
        # Probe success metrics are typically binary (1 = success, 0 = failure)
        if 'success' in metric_name.lower():
            suggested_promql = f'avg_over_time({metric_name}[5m])'
        else:
            # For duration-based probes, success might be indicated by non-zero values
            suggested_promql = f'({metric_name} > 0)'
        
        reason = "Health probe metric suitable for availability calculation"
        
        # Common labels for probe metrics
        labels_needed = ['probe_type', 'endpoint', 'target', 'check']
        
        return ClassificationResult(
            metric_name=metric_name,
            sli_type=self.sli_type,
            confidence=confidence,
            suggested_promql=suggested_promql,
            reason=reason,
            labels_needed=labels_needed
        )