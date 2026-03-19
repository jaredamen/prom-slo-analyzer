"""Rich terminal output for SLO analysis results."""

from typing import List, Dict
from collections import defaultdict, Counter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..discovery import ServiceMetrics
from ..classifiers.base import ClassificationResult, SLIType
from ..rules.base import GapResult, GapSeverity


class TerminalReporter:
    """Rich terminal reporter for SLO analysis results."""
    
    def __init__(self, console: Console = None):
        """Initialize terminal reporter.
        
        Args:
            console: Rich console instance (creates new one if not provided)
        """
        self.console = console or Console()
    
    def show_progress(self, message: str):
        """Show a progress spinner with message.
        
        Args:
            message: Progress message to display
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            progress.add_task(description=message, total=None)
    
    def report_discovery_summary(self, services: List[ServiceMetrics]):
        """Display service discovery summary.
        
        Args:
            services: List of discovered services
        """
        if not services:
            self.console.print("[yellow]No services discovered[/yellow]")
            return
        
        # Summary statistics
        total_services = len(services)
        total_metrics = sum(len(service.metrics) for service in services)
        
        # Create summary panel
        summary_text = f"""
        [bold blue]Discovery Summary[/bold blue]
        
        • Services discovered: [green]{total_services}[/green]
        • Total metrics: [green]{total_metrics}[/green]
        • Average metrics per service: [green]{total_metrics / total_services:.1f}[/green]
        """
        
        self.console.print(Panel(summary_text.strip(), title="Service Discovery"))
        
        # Services table
        table = Table(title="Discovered Services", box=box.ROUNDED)
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Namespace", style="blue")
        table.add_column("Metrics", justify="right", style="green")
        table.add_column("Sample Metrics", style="dim")
        
        for service in services:
            namespace = service.namespace or "[dim]unknown[/dim]"
            sample_metrics = ", ".join(service.metrics[:3])
            if len(service.metrics) > 3:
                sample_metrics += f", [dim]... and {len(service.metrics) - 3} more[/dim]"
            
            table.add_row(
                service.name,
                namespace,
                str(len(service.metrics)),
                sample_metrics
            )
        
        self.console.print(table)
        self.console.print()
    
    def report_classification_summary(self, all_classifications: List[ClassificationResult]):
        """Display classification summary across all services.
        
        Args:
            all_classifications: List of all metric classifications
        """
        if not all_classifications:
            self.console.print("[yellow]No metrics classified[/yellow]")
            return
        
        # Count classifications by type
        type_counts = Counter(c.sli_type for c in all_classifications)
        
        # Create summary table
        table = Table(title="SLI Classification Summary", box=box.ROUNDED)
        table.add_column("SLI Type", style="cyan")
        table.add_column("Metrics Found", justify="right", style="green")
        table.add_column("Description", style="dim")
        
        sli_descriptions = {
            SLIType.LATENCY: "Request/response time metrics",
            SLIType.ERROR_RATE: "Error ratio and failure metrics", 
            SLIType.THROUGHPUT: "Request rate and volume metrics",
            SLIType.SATURATION: "Resource utilization metrics",
            SLIType.AVAILABILITY: "Uptime and health check metrics",
            SLIType.QUEUE_DEPTH: "Queue length and backlog metrics",
            SLIType.CONNECTION_POOL: "Connection pool utilization metrics",
            SLIType.CACHE_HIT_RATIO: "Cache performance metrics"
        }
        
        for sli_type, count in type_counts.most_common():
            description = sli_descriptions.get(sli_type, "")
            table.add_row(
                sli_type.value.replace('_', ' ').title(),
                str(count),
                description
            )
        
        self.console.print(table)
        self.console.print()
    
    def report_service_analysis(self, service: ServiceMetrics, classifications: List[ClassificationResult], gaps: List[GapResult]):
        """Display detailed analysis for a single service.
        
        Args:
            service: Service being analyzed
            classifications: Classifications for this service
            gaps: Gap analysis results for this service
        """
        # Service header
        title = f"{service.name}"
        if service.namespace:
            title += f" ({service.namespace})"
        
        # Build service info
        info_lines = [
            f"[bold blue]Service Analysis[/bold blue]",
            f"• Total metrics: [green]{len(service.metrics)}[/green]",
            f"• SLI candidates: [green]{len(classifications)}[/green]",
            f"• Identified gaps: [{'red' if gaps else 'green'}]{len(gaps)}[/green]"
        ]
        
        if classifications:
            # Group by SLI type
            by_type = defaultdict(list)
            for c in classifications:
                by_type[c.sli_type].append(c)
            
            info_lines.append("")
            info_lines.append("[bold]Available SLI Types:[/bold]")
            for sli_type, type_classifications in by_type.items():
                emoji = self._get_sli_emoji(sli_type)
                info_lines.append(f"{emoji} {sli_type.value.replace('_', ' ').title()}: {len(type_classifications)} metrics")
        
        self.console.print(Panel("\n".join(info_lines), title=title))
        
        # Classification details
        if classifications:
            self._show_classifications_table(classifications)
        
        # Gap analysis
        if gaps:
            self._show_gaps_table(gaps)
        
        self.console.print()
    
    def report_overall_summary(self, services: List[ServiceMetrics], all_classifications: List[ClassificationResult], all_gaps: List[GapResult]):
        """Display overall analysis summary.
        
        Args:
            services: All analyzed services
            all_classifications: All classifications
            all_gaps: All detected gaps
        """
        # Calculate metrics
        services_with_slis = len([s for s in services if any(c.metric_name in s.metrics for c in all_classifications)])
        services_with_gaps = len(set(g.service_name for g in all_gaps))
        
        gap_severity_counts = Counter(g.severity for g in all_gaps)
        
        # Create summary
        summary_text = f"""
        [bold green]SLO Readiness Summary[/bold green]
        
        [bold]Services:[/bold]
        • Total analyzed: {len(services)}
        • With SLI candidates: [{'green' if services_with_slis == len(services) else 'yellow'}]{services_with_slis}[/]
        • With identified gaps: [{'red' if services_with_gaps > 0 else 'green'}]{services_with_gaps}[/]
        
        [bold]Metrics:[/bold]
        • Total SLI candidates: [green]{len(all_classifications)}[/green]
        • Total gaps identified: [{'red' if all_gaps else 'green'}]{len(all_gaps)}[/]
        """
        
        if gap_severity_counts:
            summary_text += "\n[bold]Gap Severity:[/bold]\n"
            severity_colors = {
                GapSeverity.CRITICAL: "red",
                GapSeverity.HIGH: "red",  
                GapSeverity.MEDIUM: "yellow",
                GapSeverity.LOW: "blue"
            }
            for severity, count in gap_severity_counts.items():
                color = severity_colors.get(severity, "white")
                summary_text += f"• {severity.value.title()}: [{color}]{count}[/{color}]\n"
        
        self.console.print(Panel(summary_text.strip(), title="Overall Results"))
    
    def _show_classifications_table(self, classifications: List[ClassificationResult]):
        """Show detailed classifications table."""
        table = Table(title="SLI Classifications", box=box.SIMPLE)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("SLI Type", style="blue")
        table.add_column("Confidence", justify="right", style="green")
        table.add_column("Suggested PromQL", style="dim", max_width=50)
        
        # Sort by confidence descending
        sorted_classifications = sorted(classifications, key=lambda x: x.confidence, reverse=True)
        
        for classification in sorted_classifications:
            confidence_str = f"{classification.confidence:.0%}"
            sli_type_display = classification.sli_type.value.replace('_', ' ').title()
            
            # Truncate PromQL if too long
            promql = classification.suggested_promql or "N/A"
            if len(promql) > 50:
                promql = promql[:47] + "..."
            
            table.add_row(
                classification.metric_name,
                sli_type_display,
                confidence_str,
                promql
            )
        
        self.console.print(table)
    
    def _show_gaps_table(self, gaps: List[GapResult]):
        """Show gaps analysis table."""
        table = Table(title="Identified Gaps", box=box.SIMPLE)
        table.add_column("Rule", style="cyan")
        table.add_column("Severity", justify="center")
        table.add_column("Issue", style="yellow", max_width=40)
        table.add_column("Recommendation", style="dim", max_width=50)
        
        # Sort by severity (critical first)
        severity_order = {GapSeverity.CRITICAL: 0, GapSeverity.HIGH: 1, GapSeverity.MEDIUM: 2, GapSeverity.LOW: 3}
        sorted_gaps = sorted(gaps, key=lambda x: severity_order[x.severity])
        
        for gap in sorted_gaps:
            severity_style = {
                GapSeverity.CRITICAL: "red",
                GapSeverity.HIGH: "red",
                GapSeverity.MEDIUM: "yellow", 
                GapSeverity.LOW: "blue"
            }[gap.severity]
            
            severity_display = f"[{severity_style}]{gap.severity.value.upper()}[/{severity_style}]"
            
            # Truncate long text
            message = gap.message
            if len(message) > 40:
                message = message[:37] + "..."
                
            recommendation = gap.recommendation
            if len(recommendation) > 50:
                recommendation = recommendation[:47] + "..."
            
            table.add_row(
                gap.rule_name,
                severity_display,
                message,
                recommendation
            )
        
        self.console.print(table)
    
    def _get_sli_emoji(self, sli_type: SLIType) -> str:
        """Get emoji for SLI type."""
        emoji_map = {
            SLIType.LATENCY: "LATENCY",
            SLIType.ERROR_RATE: "ERROR", 
            SLIType.THROUGHPUT: "THROUGHPUT",
            SLIType.SATURATION: "SATURATION",
            SLIType.AVAILABILITY: "AVAILABILITY",
            SLIType.QUEUE_DEPTH: "QUEUE_DEPTH",
            SLIType.CONNECTION_POOL: "CONNECTION_POOL",
            SLIType.CACHE_HIT_RATIO: "CACHE_HIT_RATIO"
        }
        return emoji_map.get(sli_type, "METRICS")