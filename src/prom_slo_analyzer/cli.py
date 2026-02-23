"""Command line interface for prom-slo-analyzer."""

import os
import sys
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .client import PrometheusClient
from .discovery import ServiceDiscovery
from .classifiers import (
    LatencyClassifier, ErrorRateClassifier, ThroughputClassifier, 
    SaturationClassifier, AvailabilityClassifier
)
from .rules import MissingLatencyRule, MissingErrorRateRule, NoSLICandidatesRule
from .report import TerminalReporter, MarkdownReporter

app = typer.Typer(
    name="prom-slo-analyzer",
    help="Analyze Prometheus metrics for SLO readiness",
    add_completion=False,
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def scan(
    prometheus_url: Optional[str] = typer.Option(
        None, 
        "--prometheus-url", 
        "-u",
        help="Prometheus server URL (or set PROMETHEUS_URL env var)",
        envvar="PROMETHEUS_URL"
    ),
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace", 
        "-n",
        help="Filter services by namespace"
    ),
    format: str = typer.Option(
        "terminal",
        "--format",
        "-f", 
        help="Output format: terminal, markdown"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (only for non-terminal formats)"
    )
):
    """Scan Prometheus instance and analyze SLO readiness."""
    
    # Validate prometheus URL
    if not prometheus_url:
        console.print("[red]Error: Prometheus URL is required. Use --prometheus-url or set PROMETHEUS_URL environment variable.[/red]")
        raise typer.Exit(1)
    
    # Validate format
    if format not in ["terminal", "markdown"]:
        console.print(f"[red]Error: Unsupported format '{format}'. Use: terminal, markdown[/red]")
        raise typer.Exit(1)
    
    # Validate output file for non-terminal formats
    if format != "terminal" and not output:
        console.print(f"[red]Error: Output file required for {format} format. Use --output[/red]")
        raise typer.Exit(1)
    
    try:
        # Initialize components
        client = PrometheusClient(prometheus_url)
        discovery = ServiceDiscovery(client)
        terminal_reporter = TerminalReporter(console)
        
        # Check connectivity
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Connecting to Prometheus...", total=None)
            
            if not client.check_connectivity():
                console.print(f"[red]Error: Cannot connect to Prometheus at {prometheus_url}[/red]")
                raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Connected to Prometheus at {prometheus_url}")
        
        # Discover services
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Discovering services...", total=None)
            services = discovery.discover_services(namespace_filter=namespace)
        
        if not services:
            console.print("[yellow]No services found matching the criteria[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"[green]✓[/green] Discovered {len(services)} services")
        
        # Initialize classifiers
        classifiers = [
            LatencyClassifier(),
            ErrorRateClassifier(), 
            ThroughputClassifier(),
            SaturationClassifier(),
            AvailabilityClassifier()
        ]
        
        # Initialize gap detection rules
        rules = [
            MissingLatencyRule(),
            MissingErrorRateRule(),
            NoSLICandidatesRule()
        ]
        
        # Analyze each service
        all_classifications = []
        all_gaps = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Analyzing services...", total=len(services))
            
            for service in services:
                # Classify metrics
                service_classifications = []
                for classifier in classifiers:
                    classifications = classifier.batch_classify(service.metrics)
                    service_classifications.extend(classifications)
                    all_classifications.extend(classifications)
                
                # Detect gaps
                service_gaps = []
                for rule in rules:
                    gaps = rule.check(service, service_classifications)
                    service_gaps.extend(gaps)
                    all_gaps.extend(gaps)
                
                progress.advance(task)
        
        console.print(f"[green]✓[/green] Analysis complete")
        console.print()
        
        # Generate reports
        if format == "terminal":
            # Show discovery summary
            terminal_reporter.report_discovery_summary(services)
            
            # Show classification summary
            terminal_reporter.report_classification_summary(all_classifications)
            
            # Show each service analysis
            for service in services:
                service_classifications = [c for c in all_classifications if c.metric_name in service.metrics]
                service_gaps = [g for g in all_gaps if g.service_name == service.name]
                terminal_reporter.report_service_analysis(service, service_classifications, service_gaps)
            
            # Show overall summary
            terminal_reporter.report_overall_summary(services, all_classifications, all_gaps)
            
        elif format == "markdown":
            markdown_reporter = MarkdownReporter()
            report_content = markdown_reporter.generate_report(
                services, all_classifications, all_gaps, prometheus_url
            )
            markdown_reporter.save_report(report_content, output)
            console.print(f"[green]✓[/green] Markdown report saved to {output}")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        if "--debug" in sys.argv:
            raise
        raise typer.Exit(1)


@app.command()
def discover(
    prometheus_url: Optional[str] = typer.Option(
        None,
        "--prometheus-url", 
        "-u",
        help="Prometheus server URL (or set PROMETHEUS_URL env var)",
        envvar="PROMETHEUS_URL"
    ),
    namespace: Optional[str] = typer.Option(
        None,
        "--namespace",
        "-n", 
        help="Filter services by namespace"
    )
):
    """Discover services from Prometheus without full analysis."""
    
    if not prometheus_url:
        console.print("[red]Error: Prometheus URL is required. Use --prometheus-url or set PROMETHEUS_URL environment variable.[/red]")
        raise typer.Exit(1)
    
    try:
        client = PrometheusClient(prometheus_url)
        discovery = ServiceDiscovery(client)
        terminal_reporter = TerminalReporter(console)
        
        # Check connectivity
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Connecting to Prometheus...", total=None)
            
            if not client.check_connectivity():
                console.print(f"[red]Error: Cannot connect to Prometheus at {prometheus_url}[/red]")
                raise typer.Exit(1)
        
        console.print(f"[green]✓[/green] Connected to Prometheus at {prometheus_url}")
        
        # Discover services
        with Progress(
            SpinnerColumn(), 
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Discovering services...", total=None)
            services = discovery.discover_services(namespace_filter=namespace)
        
        # Report discovery results
        terminal_reporter.report_discovery_summary(services)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Discovery cancelled[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Error during discovery: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version and exit")
):
    """
    Prometheus SLO Analyzer
    
    Analyze your Prometheus metrics for SLO readiness. Discover which services 
    have the right metrics for SLIs, identify gaps, and get recommendations
    for improving your observability setup.
    """
    if version:
        from . import __version__
        console.print(f"prom-slo-analyzer version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()