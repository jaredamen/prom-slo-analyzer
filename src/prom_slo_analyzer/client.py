"""Prometheus API client for metric discovery and querying."""

import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

import requests


class PrometheusClient:
    """Client for interacting with Prometheus HTTP API."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize Prometheus client.
        
        Args:
            base_url: Base URL of Prometheus instance (e.g., 'http://localhost:9090')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to Prometheus API.
        
        Args:
            endpoint: API endpoint (e.g., '/api/v1/label/__name__/values')
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: If request fails
            ValueError: If response is not valid JSON or has error status
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = requests.get(url, params=params or {}, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'success':
                raise ValueError(f"Prometheus API error: {data.get('error', 'Unknown error')}")
                
            return data
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to connect to Prometheus at {url}: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from Prometheus: {e}")
    
    def get_metric_names(self) -> List[str]:
        """Get all metric names from Prometheus.
        
        Returns:
            List of metric names
        """
        data = self._make_request('/api/v1/label/__name__/values')
        return data['data']
    
    def get_metric_metadata(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Metric metadata or None if not found
        """
        try:
            data = self._make_request('/api/v1/metadata', params={'metric': metric_name})
            metadata = data['data'].get(metric_name)
            return metadata[0] if metadata else None
        except (requests.RequestException, ValueError, KeyError):
            return None
    
    def get_metric_labels(self, metric_name: str) -> List[str]:
        """Get label names for a specific metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            List of label names
        """
        try:
            # Query the metric to get its labels
            data = self._make_request('/api/v1/query', params={'query': f'{metric_name}{{}}[1m]'})
            
            # Extract unique label names from all series
            label_names = set()
            for series in data.get('data', {}).get('result', []):
                if 'metric' in series:
                    label_names.update(series['metric'].keys())
            
            # Remove __name__ label which is the metric name itself
            label_names.discard('__name__')
            return list(label_names)
            
        except (requests.RequestException, ValueError, KeyError):
            return []
    
    def query(self, query: str) -> Dict[str, Any]:
        """Execute a PromQL query.
        
        Args:
            query: PromQL query string
            
        Returns:
            Query result data
        """
        return self._make_request('/api/v1/query', params={'query': query})
    
    def query_range(self, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """Execute a PromQL range query.
        
        Args:
            query: PromQL query string
            start: Start time (RFC3339 or Unix timestamp)
            end: End time (RFC3339 or Unix timestamp)  
            step: Query resolution step
            
        Returns:
            Query result data
        """
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        return self._make_request('/api/v1/query_range', params=params)
    
    def check_connectivity(self) -> bool:
        """Check if Prometheus is reachable and responding.
        
        Returns:
            True if Prometheus is accessible, False otherwise
        """
        try:
            self._make_request('/api/v1/status/config')
            return True
        except (requests.RequestException, ValueError):
            return False