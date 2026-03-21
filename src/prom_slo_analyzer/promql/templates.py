"""PromQL templates for common SLO expressions."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..classifiers.base import SLIType


class TimeWindow(Enum):
    """Standard time windows for SLO calculations."""

    SHORT = "5m"
    MEDIUM = "1h"
    LONG = "24h"
    MONTHLY = "30d"


@dataclass
class PromQLTemplate:
    """A PromQL template with metadata."""

    name: str
    description: str
    expression: str
    sli_type: SLIType
    time_window: TimeWindow
    variables: list[str]  # List of variables that need to be substituted


class SLOTemplates:
    """Collection of working PromQL templates for SLO calculations."""

    def __init__(self) -> None:
        """Initialize with standard SLO templates."""
        self._templates = self._build_templates()

    def get_templates_for_sli_type(self, sli_type: SLIType) -> list[PromQLTemplate]:
        """Get all templates for a specific SLI type.

        Args:
            sli_type: The SLI type to filter by

        Returns:
            List of matching templates
        """
        return [t for t in self._templates if t.sli_type == sli_type]

    def get_template(self, name: str) -> Optional[PromQLTemplate]:
        """Get a specific template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        for template in self._templates:
            if template.name == name:
                return template
        return None

    def substitute_variables(self, template: PromQLTemplate, variables: dict[str, str]) -> str:
        """Substitute variables in a template expression.

        Args:
            template: The template to use
            variables: Dictionary of variable name -> value mappings

        Returns:
            PromQL expression with variables substituted
        """
        expression = template.expression
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            expression = expression.replace(placeholder, var_value)
        return expression

    def _build_templates(self) -> list[PromQLTemplate]:
        """Build the standard set of SLO templates."""
        templates = []

        # Availability templates
        templates.extend(
            [
                PromQLTemplate(
                    name="availability_up_ratio",
                    description="Basic availability using 'up' metric",
                    expression="avg_over_time(up{{job='{job}'}[{time_window}])",
                    sli_type=SLIType.AVAILABILITY,
                    time_window=TimeWindow.SHORT,
                    variables=["job", "time_window"],
                ),
                PromQLTemplate(
                    name="availability_health_check",
                    description="Availability using custom health check metric",
                    expression="avg_over_time({health_metric}[{time_window}])",
                    sli_type=SLIType.AVAILABILITY,
                    time_window=TimeWindow.SHORT,
                    variables=["health_metric", "time_window"],
                ),
            ]
        )

        # Error rate templates
        templates.extend(
            [
                PromQLTemplate(
                    name="error_rate_ratio",
                    description="Error rate from separate error and request counters",
                    expression="rate({error_metric}[{time_window}]) / rate({request_metric}[{time_window}])",
                    sli_type=SLIType.ERROR_RATE,
                    time_window=TimeWindow.SHORT,
                    variables=["error_metric", "request_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="error_rate_http_status",
                    description="HTTP 5xx error rate from status code labeled metrics",
                    expression='rate({request_metric}{{status=~"5.."}[{time_window}]) / rate({request_metric}[{time_window}])',
                    sli_type=SLIType.ERROR_RATE,
                    time_window=TimeWindow.SHORT,
                    variables=["request_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="success_rate",
                    description="Success rate (inverse of error rate) for SLO targets",
                    expression="1 - (rate({error_metric}[{time_window}]) / rate({request_metric}[{time_window}]))",
                    sli_type=SLIType.ERROR_RATE,
                    time_window=TimeWindow.SHORT,
                    variables=["error_metric", "request_metric", "time_window"],
                ),
            ]
        )

        # Latency templates
        templates.extend(
            [
                PromQLTemplate(
                    name="latency_p50",
                    description="50th percentile latency from histogram",
                    expression="histogram_quantile(0.50, rate({histogram_metric}_bucket[{time_window}]))",
                    sli_type=SLIType.LATENCY,
                    time_window=TimeWindow.SHORT,
                    variables=["histogram_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="latency_p90",
                    description="90th percentile latency from histogram",
                    expression="histogram_quantile(0.90, rate({histogram_metric}_bucket[{time_window}]))",
                    sli_type=SLIType.LATENCY,
                    time_window=TimeWindow.SHORT,
                    variables=["histogram_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="latency_p95",
                    description="95th percentile latency from histogram",
                    expression="histogram_quantile(0.95, rate({histogram_metric}_bucket[{time_window}]))",
                    sli_type=SLIType.LATENCY,
                    time_window=TimeWindow.SHORT,
                    variables=["histogram_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="latency_p99",
                    description="99th percentile latency from histogram",
                    expression="histogram_quantile(0.99, rate({histogram_metric}_bucket[{time_window}]))",
                    sli_type=SLIType.LATENCY,
                    time_window=TimeWindow.SHORT,
                    variables=["histogram_metric", "time_window"],
                ),
            ]
        )

        # Throughput templates
        templates.extend(
            [
                PromQLTemplate(
                    name="request_rate",
                    description="Request rate (requests per second)",
                    expression="rate({request_metric}[{time_window}])",
                    sli_type=SLIType.THROUGHPUT,
                    time_window=TimeWindow.SHORT,
                    variables=["request_metric", "time_window"],
                ),
                PromQLTemplate(
                    name="throughput_per_minute",
                    description="Throughput in requests per minute",
                    expression="rate({request_metric}[{time_window}]) * 60",
                    sli_type=SLIType.THROUGHPUT,
                    time_window=TimeWindow.SHORT,
                    variables=["request_metric", "time_window"],
                ),
            ]
        )

        # TODO stubs for advanced templates
        templates.extend(
            [
                # TODO: Burn rate alert expressions
                # PromQLTemplate(
                #     name="burn_rate_1h_5m",
                #     description="1-hour burn rate based on 5-minute error rate",
                #     expression="# TODO: Implement burn rate calculation",
                #     sli_type=SLIType.ERROR_RATE,
                #     time_window=TimeWindow.SHORT,
                #     variables=["error_budget", "target_slo"]
                # ),
                # TODO: Multi-window alert expressions
                # PromQLTemplate(
                #     name="multi_window_burn_rate",
                #     description="Multi-window burn rate for faster alerting",
                #     expression="# TODO: Implement multi-window burn rate logic",
                #     sli_type=SLIType.ERROR_RATE,
                #     time_window=TimeWindow.SHORT,
                #     variables=["short_window", "long_window", "error_budget"]
                # ),
                # TODO: Composite SLI expressions
                # PromQLTemplate(
                #     name="composite_request_success",
                #     description="Composite SLI combining latency and error rate",
                #     expression="# TODO: Implement composite SLI logic",
                #     sli_type=SLIType.ERROR_RATE,  # or create composite type
                #     time_window=TimeWindow.SHORT,
                #     variables=["latency_threshold", "error_threshold"]
                # )
            ]
        )

        return templates

    def get_all_templates(self) -> list[PromQLTemplate]:
        """Get all available templates.

        Returns:
            List of all templates
        """
        return self._templates.copy()
