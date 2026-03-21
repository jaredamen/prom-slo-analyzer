"""Tests for PrometheusClient."""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from prom_slo_analyzer.client import PrometheusClient


class TestPrometheusClient:
    """Tests for PrometheusClient functionality."""

    def test_init(self):
        """Test client initialization."""
        client = PrometheusClient("http://localhost:9090")
        assert client.base_url == "http://localhost:9090"
        assert client.timeout == 30

        # Test URL cleanup
        client = PrometheusClient("http://localhost:9090/")
        assert client.base_url == "http://localhost:9090"

    @patch("requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "success", "data": ["metric1", "metric2"]}
        mock_get.return_value = mock_response

        client = PrometheusClient("http://localhost:9090")
        result = client._make_request("/api/v1/test")

        assert result["status"] == "success"
        assert result["data"] == ["metric1", "metric2"]
        mock_get.assert_called_once_with("http://localhost:9090/api/v1/test", params={}, timeout=30)

    @patch("requests.get")
    def test_make_request_connection_error(self, mock_get):
        """Test connection error handling."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        client = PrometheusClient("http://localhost:9090")

        with pytest.raises(requests.RequestException, match="Failed to connect to Prometheus"):
            client._make_request("/api/v1/test")

    @patch("requests.get")
    def test_make_request_prometheus_error(self, mock_get):
        """Test Prometheus API error response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "error", "error": "bad_data"}
        mock_get.return_value = mock_response

        client = PrometheusClient("http://localhost:9090")

        with pytest.raises(ValueError, match="Prometheus API error: bad_data"):
            client._make_request("/api/v1/test")

    @patch("requests.get")
    def test_make_request_invalid_json(self, mock_get):
        """Test invalid JSON response handling."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        client = PrometheusClient("http://localhost:9090")

        with pytest.raises(ValueError, match="Invalid JSON response from Prometheus"):
            client._make_request("/api/v1/test")

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_names(self, mock_make_request):
        """Test getting metric names."""
        mock_make_request.return_value = {"data": ["metric1", "metric2", "metric3"]}

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_names()

        assert result == ["metric1", "metric2", "metric3"]
        mock_make_request.assert_called_once_with("/api/v1/label/__name__/values")

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_metadata_success(self, mock_make_request):
        """Test getting metric metadata successfully."""
        mock_make_request.return_value = {
            "data": {"test_metric": [{"type": "counter", "help": "Test metric description"}]}
        }

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_metadata("test_metric")

        assert result["type"] == "counter"
        assert result["help"] == "Test metric description"
        mock_make_request.assert_called_once_with("/api/v1/metadata", params={"metric": "test_metric"})

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_metadata_not_found(self, mock_make_request):
        """Test getting metadata for non-existent metric."""
        mock_make_request.return_value = {"data": {}}

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_metadata("nonexistent_metric")

        assert result is None

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_metadata_error(self, mock_make_request):
        """Test metadata request error handling."""
        mock_make_request.side_effect = requests.RequestException("Request failed")

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_metadata("test_metric")

        assert result is None

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_labels_success(self, mock_make_request):
        """Test getting metric labels successfully."""
        mock_make_request.return_value = {
            "data": {
                "result": [
                    {
                        "metric": {
                            "__name__": "test_metric",
                            "job": "test_job",
                            "instance": "localhost:8080",
                            "method": "GET",
                        }
                    }
                ]
            }
        }

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_labels("test_metric")

        # Should exclude __name__ but include other labels
        assert "job" in result
        assert "instance" in result
        assert "method" in result
        assert "__name__" not in result

    @patch.object(PrometheusClient, "_make_request")
    def test_get_metric_labels_error(self, mock_make_request):
        """Test label request error handling."""
        mock_make_request.side_effect = requests.RequestException("Request failed")

        client = PrometheusClient("http://localhost:9090")
        result = client.get_metric_labels("test_metric")

        assert result == []

    @patch.object(PrometheusClient, "_make_request")
    def test_query(self, mock_make_request):
        """Test PromQL query execution."""
        expected_result = {"data": {"result": []}}
        mock_make_request.return_value = expected_result

        client = PrometheusClient("http://localhost:9090")
        result = client.query("up")

        assert result == expected_result
        mock_make_request.assert_called_once_with("/api/v1/query", params={"query": "up"})

    @patch.object(PrometheusClient, "_make_request")
    def test_query_range(self, mock_make_request):
        """Test PromQL range query execution."""
        expected_result = {"data": {"result": []}}
        mock_make_request.return_value = expected_result

        client = PrometheusClient("http://localhost:9090")
        result = client.query_range("up", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z", "5m")

        assert result == expected_result
        mock_make_request.assert_called_once_with(
            "/api/v1/query_range",
            params={"query": "up", "start": "2023-01-01T00:00:00Z", "end": "2023-01-01T01:00:00Z", "step": "5m"},
        )

    @patch.object(PrometheusClient, "_make_request")
    def test_check_connectivity_success(self, mock_make_request):
        """Test successful connectivity check."""
        mock_make_request.return_value = {"status": "success"}

        client = PrometheusClient("http://localhost:9090")
        result = client.check_connectivity()

        assert result is True
        mock_make_request.assert_called_once_with("/api/v1/status/config")

    @patch.object(PrometheusClient, "_make_request")
    def test_check_connectivity_failure(self, mock_make_request):
        """Test connectivity check failure."""
        mock_make_request.side_effect = requests.RequestException("Connection failed")

        client = PrometheusClient("http://localhost:9090")
        result = client.check_connectivity()

        assert result is False
