# Prometheus SLO Analyzer

**Instantly assess your Prometheus metrics for SLO readiness — discover which services have the right signals for SLIs, identify gaps, and get actionable recommendations.**

[![CI Status](https://github.com/jaredamen/prom-slo-analyzer/workflows/CI/badge.svg)](https://github.com/jaredamen/prom-slo-analyzer/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start

```bash
# Install
pip install prom-slo-analyzer

# Analyze your Prometheus instance
prom-slo-analyzer scan --prometheus-url http://localhost:9090

# Generate markdown report
prom-slo-analyzer scan --prometheus-url http://localhost:9090 --format markdown --output slo-report.md
```

## What It Does

`prom-slo-analyzer` connects to your Prometheus instance, analyzes your metrics, and tells you:

- **Which services are ready for SLOs** — services with complete latency, error rate, and throughput metrics
- **What's missing** — services tracking requests but missing crucial signals like latency or error rates  
- **Specific recommendations** — exactly which metrics to add and how to instrument them
- **Ready-to-use PromQL** — working expressions for your SLI calculations

## Example Output

```
Service Discovery
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Service       ┃ Namespace  ┃ Metrics      ┃ Sample Metrics                       ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_gateway   │ production │ 8            │ requests_total, duration_bucket, ... │
│ user_service  │ production │ 12           │ http_requests_total, db_conn_pool... │
│ payment_svc   │ production │ 6            │ transactions_total, queue_depth, ... │
└───────────────┴────────────┴──────────────┴──────────────────────────────────────┘

api_gateway (production)
Total metrics: 8 • SLI candidates: 5 • Identified gaps: 0

SLI Classifications
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                                   ┃ SLI Type    ┃ Confidence ┃ Suggested PromQL                               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_gateway_request_duration_bucket      │ Latency     │ 90%        │ histogram_quantile(0.95, rate(...[5m]))       │
│ api_gateway_requests_total               │ Throughput  │ 92%        │ rate(api_gateway_requests_total[5m])           │
│ api_gateway_errors_total                 │ Error Rate  │ 91%        │ rate(...errors_total[5m]) / rate(...[5m])     │
└──────────────────────────────────────────┴─────────────┴────────────┴────────────────────────────────────────────────┘

payment_svc (production) 
🟡 MEDIUM: Missing Latency Metrics
Service tracks request throughput but lacks latency metrics
→ Add histogram metrics like 'payment_svc_duration_seconds' for latency SLOs

Overall Results
SLO Readiness Summary

Services:
• Total analyzed: 3
• With SLI candidates: 3  
• With identified gaps: 1

Metrics:
• Total SLI candidates: 12
• Total gaps identified: 1
```

## Installation

### From PyPI

```bash
pip install prom-slo-analyzer
```

### From Source

```bash
git clone https://github.com/YusefAmen/prom-slo-analyzer.git
cd prom-slo-analyzer
pip install -e .
```

### With Docker

```bash
docker run --rm ghcr.io/yusefamen/prom-slo-analyzer:latest \
  --prometheus-url http://host.docker.internal:9090
```

## CLI Reference

### `prom-slo-analyzer scan`

Analyze Prometheus metrics for SLO readiness.

**Options:**
- `--prometheus-url, -u` — Prometheus server URL (or set `PROMETHEUS_URL` env var)
- `--namespace, -n` — Filter services by namespace  
- `--format, -f` — Output format: `terminal` (default), `markdown`
- `--output, -o` — Output file (required for non-terminal formats)

**Examples:**

```bash
# Basic analysis
prom-slo-analyzer scan --prometheus-url http://prometheus:9090

# Filter by namespace
prom-slo-analyzer scan -u http://prometheus:9090 --namespace production

# Generate markdown report
prom-slo-analyzer scan -u http://prometheus:9090 -f markdown -o report.md

# Use environment variable
export PROMETHEUS_URL=http://prometheus:9090
prom-slo-analyzer scan --namespace staging
```

### `prom-slo-analyzer discover`

Quickly discover services without full analysis.

**Options:**
- `--prometheus-url, -u` — Prometheus server URL
- `--namespace, -n` — Filter by namespace

## Architecture

Clean pipeline design built for extensibility:

```
prom-slo-analyzer/
├── client.py          # Prometheus API client
├── discovery.py       # Service discovery & metric grouping  
├── classifiers/       # Metric classification engine
│   ├── latency.py     # Histogram/summary detection
│   ├── error_rate.py  # Error ratio detection  
│   ├── throughput.py  # Request rate detection
│   ├── saturation.py  # Resource utilization
│   └── availability.py # Up/health detection
├── rules/             # Gap detection rules
├── promql/            # PromQL templates & validation
└── report/            # Output formatting
```

### Supported SLI Types

- **Latency** — Request/response time (histograms, summaries)
- **Error Rate** — Failed request ratios, HTTP 5xx rates
- **Throughput** — Request rates, transaction volumes  
- **Saturation** — Resource utilization, capacity metrics
- **Availability** — Uptime, health checks, service status

*Coming Soon:* Queue depth, connection pools, cache hit ratios

## Understanding SLOs

**Service Level Objectives (SLOs)** define reliability targets for your services. They're built on **Service Level Indicators (SLIs)** — the metrics that matter to your users.

The **Golden Signals** (latency, error rate, throughput, saturation) form the foundation of effective SLOs:

- **Latency SLI**: "95% of requests complete within 200ms"
- **Error Rate SLI**: "99.9% of requests succeed" 
- **Throughput SLI**: "Handle 1000 requests/second"
- **Availability SLI**: "Service responds to requests 99.95% of the time"

`prom-slo-analyzer` identifies which of your services have the right metrics to support these SLIs and where you need to add instrumentation.

## Roadmap

### Upcoming Features

- **Queue Depth Analysis** — Detect backlog and queueing metrics
- **Connection Pool Monitoring** — Database and HTTP client pool utilization  
- **Cache Performance** — Hit/miss ratios and cache efficiency
- **Burn Rate Alerting** — Multi-window burn rate expressions
- **Composite SLIs** — Combined latency + error rate expressions
- **Custom Classification Rules** — Define your own metric patterns
- **Grafana Integration** — Auto-generate SLI dashboards
- **Kubernetes Discovery** — Service discovery via K8s API

### Community Contributions Welcome!

We're building this in the open. Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

**Quick start for contributors:**

```bash
git clone https://github.com/YusefAmen/prom-slo-analyzer.git
cd prom-slo-analyzer
pip install -e ".[dev]"
pre-commit install
pytest
```

## Like This Tool?

If `prom-slo-analyzer` helps improve your SLO game, consider:

- **Starring the repo** — helps others discover the tool
- **[Buy me a coffee](https://buymeacoffee.com/YusefAmen)** — fuel more open source work
- **[GitHub Sponsors](https://github.com/sponsors/YusefAmen)** — ongoing support for development

## Need More Than Analysis?

Check out **[Reflex](https://yusefamen.github.io/reflex-landing/)** — AI-powered SLO generation for Kubernetes and Prometheus. Reflex goes beyond analysis to automatically create SLOs, alerting rules, and dashboards based on your actual traffic patterns.

## Author

Built by **Jared (Yusef) Amen** — SRE consultant and builder of reliability tooling.

**Available for consulting:** [LinkedIn](https://linkedin.com/in/yusefamen) • **Open source work:** [GitHub](https://github.com/YusefAmen)

I help teams implement SLOs, improve observability, and build reliable systems. From startups to enterprises — let's make your services more reliable.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and migration guides.

---

*Prometheus SLO Analyzer — Making SLO adoption simple, one metric at a time.*
