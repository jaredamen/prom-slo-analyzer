"""Markdown report generation for SLO analysis results."""

from typing import List, Dict, TextIO
from collections import defaultdict, Counter
from datetime import datetime

from ..discovery import ServiceMetrics
from ..classifiers.base import ClassificationResult, SLIType  
from ..rules.base import GapResult, GapSeverity


class MarkdownReporter:
    """Generates markdown reports for SLO analysis results."""
    
    def __init__(self):
        """Initialize markdown reporter."""
        pass
    
    def generate_report(
        self,
        services: List[ServiceMetrics],
        all_classifications: List[ClassificationResult], 
        all_gaps: List[GapResult],
        prometheus_url: str = None
    ) -> str:
        """Generate complete markdown report.
        
        Args:
            services: List of analyzed services
            all_classifications: All metric classifications
            all_gaps: All detected gaps  
            prometheus_url: Prometheus instance URL
            
        Returns:
            Complete markdown report as string
        """
        lines = []
        
        # Header
        lines.extend(self._generate_header(prometheus_url))
        lines.append("")
        
        # Executive Summary
        lines.extend(self._generate_executive_summary(services, all_classifications, all_gaps))
        lines.append("")
        
        # Service Discovery Summary
        lines.extend(self._generate_discovery_summary(services))
        lines.append("")
        
        # SLI Classification Overview
        lines.extend(self._generate_classification_overview(all_classifications))
        lines.append("")
        
        # Gap Analysis Summary
        lines.extend(self._generate_gap_summary(all_gaps))
        lines.append("")
        
        # Detailed Service Analysis
        lines.extend(self._generate_service_details(services, all_classifications, all_gaps))
        lines.append("")
        
        # Recommendations
        lines.extend(self._generate_recommendations(all_gaps))
        lines.append("")
        
        # Appendix
        lines.extend(self._generate_appendix())
        
        return "\n".join(lines)
    
    def save_report(self, report_content: str, output_file: str):
        """Save report to file.
        
        Args:
            report_content: Generated report content
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def _generate_header(self, prometheus_url: str = None) -> List[str]:
        """Generate report header."""
        lines = [
            "# Prometheus SLO Readiness Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if prometheus_url:
            lines.append(f"**Prometheus URL:** {prometheus_url}")
            
        lines.extend([
            f"**Tool:** prom-slo-analyzer",
            "",
            "---"
        ])
        
        return lines
    
    def _generate_executive_summary(
        self, 
        services: List[ServiceMetrics], 
        classifications: List[ClassificationResult],
        gaps: List[GapResult]
    ) -> List[str]:
        """Generate executive summary."""
        lines = ["## Executive Summary"]
        
        services_with_slis = len([s for s in services if any(c.metric_name in s.metrics for c in classifications)])
        services_with_gaps = len(set(g.service_name for g in gaps))
        gap_severity_counts = Counter(g.severity for g in gaps)
        
        lines.extend([
            "",
            f"This analysis examined **{len(services)}** services from your Prometheus instance to assess their readiness for Service Level Objectives (SLOs).",
            "",
            "### Key Findings",
            "",
            f"- **{services_with_slis}/{len(services)}** services have metrics suitable for SLI definition",
            f"- **{len(classifications)}** total SLI candidate metrics identified",
            f"- ⚠️ **{len(gaps)}** gaps found across **{services_with_gaps}** services"
        ])
        
        if gap_severity_counts:
            lines.append("")
            lines.append("### Gap Severity Breakdown")
            lines.append("")
            for severity in [GapSeverity.CRITICAL, GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]:
                if severity in gap_severity_counts:
                    count = gap_severity_counts[severity]
                    emoji = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}[severity.value]
                    lines.append(f"- **{emoji}**: {count} issues")
        
        return lines
    
    def _generate_discovery_summary(self, services: List[ServiceMetrics]) -> List[str]:
        """Generate service discovery summary."""
        lines = ["## Service Discovery Summary"]
        
        if not services:
            lines.extend(["", "No services were discovered in the Prometheus instance."])
            return lines
        
        total_metrics = sum(len(service.metrics) for service in services)
        avg_metrics = total_metrics / len(services) if services else 0
        
        lines.extend([
            "",
            f"**Total Services:** {len(services)}",
            f"**Total Metrics:** {total_metrics:,}",
            f"**Average Metrics per Service:** {avg_metrics:.1f}",
            "",
            "| Service | Namespace | Metrics Count | Sample Metrics |",
            "|---------|-----------|---------------|----------------|"
        ])
        
        for service in services[:20]:  # Limit to first 20 services
            namespace = service.namespace or "unknown"
            sample_metrics = ", ".join(service.metrics[:3])
            if len(service.metrics) > 3:
                sample_metrics += f", ... (+{len(service.metrics) - 3} more)"
            
            lines.append(f"| {service.name} | {namespace} | {len(service.metrics)} | `{sample_metrics}` |")
        
        if len(services) > 20:
            lines.append(f"| ... | ... | ... | *({len(services) - 20} more services)* |")
        
        return lines
    
    def _generate_classification_overview(self, classifications: List[ClassificationResult]) -> List[str]:
        """Generate SLI classification overview.""" 
        lines = ["## SLI Classification Overview"]
        
        if not classifications:
            lines.extend(["", "No metrics were classified as SLI candidates."])
            return lines
        
        type_counts = Counter(c.sli_type for c in classifications)
        
        lines.extend([
            "",
            f"Found **{len(classifications)}** metrics suitable for SLI definition across **{len(type_counts)}** different SLI types.",
            "",
            "### SLI Type Distribution",
            "",
            "| SLI Type | Count | Description |",
            "|----------|-------|-------------|"
        ])
        
        sli_descriptions = {
            SLIType.LATENCY: "Request/response time measurements",
            SLIType.ERROR_RATE: "Error ratios and failure tracking",
            SLIType.THROUGHPUT: "Request rates and volume metrics", 
            SLIType.SATURATION: "Resource utilization indicators",
            SLIType.AVAILABILITY: "Uptime and health status",
            SLIType.QUEUE_DEPTH: "Queue length and backlog metrics",
            SLIType.CONNECTION_POOL: "Connection pool utilization",
            SLIType.CACHE_HIT_RATIO: "Cache performance metrics"
        }
        
        for sli_type, count in type_counts.most_common():
            type_name = sli_type.value.replace('_', ' ').title()
            description = sli_descriptions.get(sli_type, "")
            lines.append(f"| {type_name} | {count} | {description} |")
        
        return lines
    
    def _generate_gap_summary(self, gaps: List[GapResult]) -> List[str]:
        """Generate gap analysis summary."""
        lines = ["## Gap Analysis Summary"]
        
        if not gaps:
            lines.extend([
                "",
                "**Excellent!** No significant gaps were identified in your SLO readiness.",
                "",
                "All analyzed services have appropriate metrics for defining SLIs and SLOs."
            ])
            return lines
        
        gap_counts_by_rule = Counter(g.rule_name for g in gaps)
        severity_counts = Counter(g.severity for g in gaps)
        
        lines.extend([
            "",
            f"Identified **{len(gaps)}** gaps across **{len(gap_counts_by_rule)}** different rule types.",
            "",
            "### Gap Categories",
            "",
            "| Gap Type | Count | Description |",
            "|----------|-------|-------------|"
        ])
        
        rule_descriptions = {
            "Missing Latency Metrics": "Services tracking errors/throughput but lacking latency metrics",
            "Missing Error Rate Metrics": "Services with latency/throughput but no error tracking", 
            "No SLI Candidates": "Services without any SLI-suitable metrics",
            "Single SLI Signal Type": "Services with only one type of SLI metric",
            "Stale Metrics": "Services with metrics that haven't been updated recently"
        }
        
        for rule_name, count in gap_counts_by_rule.most_common():
            description = rule_descriptions.get(rule_name, "")
            lines.append(f"| {rule_name} | {count} | {description} |")
        
        lines.extend([
            "",
            "### Severity Distribution",
            ""
        ])
        
        for severity in [GapSeverity.CRITICAL, GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]:
            if severity in severity_counts:
                count = severity_counts[severity]
                emoji = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}[severity.value]
                lines.append(f"- **{emoji}**: {count} issues")
        
        return lines
    
    def _generate_service_details(
        self,
        services: List[ServiceMetrics],
        all_classifications: List[ClassificationResult],
        all_gaps: List[GapResult]
    ) -> List[str]:
        """Generate detailed service analysis."""
        lines = ["## Detailed Service Analysis"]
        
        # Group data by service
        classifications_by_service = defaultdict(list)
        for c in all_classifications:
            # Find service that contains this metric
            for service in services:
                if c.metric_name in service.metrics:
                    classifications_by_service[service.name].append(c)
                    break
        
        gaps_by_service = defaultdict(list)
        for g in all_gaps:
            gaps_by_service[g.service_name].append(g)
        
        for service in services:
            service_classifications = classifications_by_service[service.name]
            service_gaps = gaps_by_service[service.name]
            
            lines.extend(self._generate_service_detail_section(service, service_classifications, service_gaps))
            lines.append("")
        
        return lines
    
    def _generate_service_detail_section(
        self,
        service: ServiceMetrics,
        classifications: List[ClassificationResult],
        gaps: List[GapResult]
    ) -> List[str]:
        """Generate detailed section for one service."""
        lines = [f"### {service.name}"]
        
        if service.namespace:
            lines.append(f"**Namespace:** {service.namespace}")
        
        lines.extend([
            f"**Total Metrics:** {len(service.metrics)}",
            f"**SLI Candidates:** {len(classifications)}",
            f"**Identified Gaps:** {len(gaps)}",
            ""
        ])
        
        # SLI Classifications
        if classifications:
            lines.extend([
                "#### SLI Classifications",
                "",
                "| Metric | SLI Type | Confidence | Suggested PromQL |",
                "|--------|----------|------------|------------------|"
            ])
            
            for c in sorted(classifications, key=lambda x: x.confidence, reverse=True):
                sli_type = c.sli_type.value.replace('_', ' ').title()
                confidence = f"{c.confidence:.0%}"
                promql = c.suggested_promql or "N/A"
                # Escape pipe characters in PromQL for markdown table
                promql = promql.replace('|', '\\|')
                lines.append(f"| `{c.metric_name}` | {sli_type} | {confidence} | `{promql}` |")
            
            lines.append("")
        
        # Gaps
        if gaps:
            lines.extend([
                "#### Identified Issues",
                ""
            ])
            
            for gap in gaps:
                severity_emoji = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW"}[gap.severity.value]
                lines.extend([
                    f"**{severity_emoji} - {gap.rule_name}** ({gap.severity.value})",
                    f"- **Issue:** {gap.message}",
                    f"- **Recommendation:** {gap.recommendation}",
                    ""
                ])
        
        return lines
    
    def _generate_recommendations(self, gaps: List[GapResult]) -> List[str]:
        """Generate overall recommendations."""
        lines = ["## Recommendations"]
        
        if not gaps:
            lines.extend([
                "",
                "Your Prometheus setup looks great for SLO implementation! Consider:",
                "",
                "1. **Define SLO targets** based on the discovered SLI metrics",
                "2. **Set up alerting** using the suggested PromQL expressions",  
                "3. **Create dashboards** to visualize your SLIs",
                "4. **Implement error budgets** for your most critical services"
            ])
            return lines
        
        # Group recommendations by priority
        critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        high_gaps = [g for g in gaps if g.severity == GapSeverity.HIGH]
        
        lines.append("")
        
        if critical_gaps:
            lines.extend([
                "### Immediate Actions Required",
                "",
                "Address these critical gaps first:"
            ])
            
            for i, gap in enumerate(critical_gaps[:5], 1):  # Top 5 critical
                lines.extend([
                    f"{i}. **{gap.service_name}**: {gap.message}",
                    f"   - {gap.recommendation}",
                    ""
                ])
        
        if high_gaps:
            lines.extend([
                "### High Priority Improvements", 
                "",
                "These improvements will significantly enhance your SLO readiness:"
            ])
            
            for i, gap in enumerate(high_gaps[:5], 1):  # Top 5 high priority
                lines.extend([
                    f"{i}. **{gap.service_name}**: {gap.message}",
                    f"   - {gap.recommendation}",
                    ""
                ])
        
        lines.extend([
            "### General Best Practices",
            "",
            "1. **Start with the Golden Signals**: Focus on latency, error rate, throughput, and saturation",
            "2. **Use histogram metrics**: Prefer histogram metrics over averages for latency measurements", 
            "3. **Standardize naming**: Use consistent metric naming patterns across services",
            "4. **Monitor continuously**: Set up regular analysis to catch new gaps as services evolve"
        ])
        
        return lines
    
    def _generate_appendix(self) -> List[str]:
        """Generate appendix with additional information."""
        lines = [
            "## Appendix",
            "",
            "### SLI Types Explained",
            "",
            "- **Latency**: How long it takes to service a request",
            "- **Error Rate**: The fraction of requests that fail", 
            "- **Throughput**: How many requests are handled per second",
            "- **Saturation**: How 'full' your service is (resource utilization)",
            "- **Availability**: Whether your service is up and accessible",
            "",
            "### About This Tool",
            "",
            "This report was generated by `prom-slo-analyzer`, an open-source tool for analyzing Prometheus metrics",
            "and identifying gaps in SLO readiness.",
            "",
            "For more information and to contribute, visit: https://github.com/YusefAmen/prom-slo-analyzer",
            "",
            "---",
            "",
            "*Generated by prom-slo-analyzer*"
        ]
        
        return lines