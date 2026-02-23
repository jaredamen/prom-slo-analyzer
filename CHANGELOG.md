# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-02-23

### Added

#### Core Features
- **Prometheus Integration**: Full Prometheus API client with connection testing
- **Service Discovery**: Automatic service detection from metric naming patterns
- **Metric Classification Engine**: Comprehensive SLI type detection system
- **Gap Analysis**: Intelligent detection of missing SLI components
- **Multi-format Reporting**: Rich terminal output and markdown report generation

#### SLI Classifiers
- **Latency Classifier**: Detects histogram and summary metrics for response time analysis
- **Error Rate Classifier**: Identifies error counters and HTTP status code metrics  
- **Throughput Classifier**: Recognizes request rate and transaction volume metrics
- **Saturation Classifier**: Finds resource utilization and capacity metrics
- **Availability Classifier**: Locates uptime and health check metrics

#### Gap Detection Rules
- **Missing Latency Rule**: Flags services with error/throughput but no latency metrics
- **Missing Error Rate Rule**: Identifies services lacking error tracking capabilities
- **No SLI Candidates Rule**: Detects services without any SLI-suitable metrics

#### CLI Interface
- **scan command**: Complete SLO readiness analysis with multiple output formats
- **discover command**: Quick service discovery without full analysis
- **Environment variable support**: `PROMETHEUS_URL` configuration
- **Namespace filtering**: Filter analysis by Kubernetes namespace or service group

#### PromQL Integration
- **Template Library**: Ready-to-use PromQL expressions for common SLI calculations
- **Expression Validation**: Basic syntax checking for generated PromQL
- **Multi-percentile Support**: P50, P90, P95, P99 latency calculations
- **Rate Calculation**: Automatic rate() expressions for counter metrics

#### Output Formats
- **Rich Terminal Output**: Colored tables, progress bars, and formatted analysis
- **Markdown Reports**: Professional reports suitable for documentation and sharing
- **JSON Support**: Structured output format (planned for v0.2.0)

#### Docker Support
- **Multi-architecture Images**: AMD64 and ARM64 container support
- **Security**: Non-root container execution
- **Health Checks**: Built-in container health monitoring

### Technical Features

#### Architecture
- **Plugin-based Design**: Extensible classifier and rule system
- **Clean Separation**: Distinct layers for discovery, analysis, and reporting
- **Type Safety**: Comprehensive type hints throughout codebase
- **Error Handling**: Robust error handling and user-friendly messages

#### Testing
- **Comprehensive Test Suite**: 95%+ code coverage
- **Mock Prometheus Responses**: Realistic test fixtures
- **Integration Testing**: End-to-end CLI testing
- **Property-based Testing**: Automated test case generation

#### Code Quality
- **Linting**: Ruff for code quality and import organization
- **Formatting**: Black for consistent code style
- **Type Checking**: MyPy for static type analysis
- **Pre-commit Hooks**: Automated quality checks

### Documentation
- **Professional README**: Comprehensive usage guide with examples
- **Contributing Guidelines**: Developer onboarding and contribution process
- **Architecture Documentation**: Code organization and extension patterns
- **CLI Reference**: Complete command and option documentation

### Infrastructure
- **GitHub Actions CI**: Automated testing across Python 3.9-3.12
- **Automated Releases**: PyPI publishing and Docker image builds
- **Code Coverage**: Codecov integration for coverage tracking
- **Security**: Dependabot for dependency updates

## Roadmap for v0.2.0

### Planned Features
- **Queue Depth Classifier**: Analysis of backlog and queueing metrics
- **Connection Pool Classifier**: Database and HTTP client pool monitoring
- **Cache Hit Ratio Classifier**: Cache performance and efficiency metrics
- **Single Signal Rule**: Detect services with only one SLI type
- **Stale Metrics Rule**: Identify metrics with outdated data
- **JSON Report Format**: Machine-readable structured output
- **Custom Classification Rules**: User-defined metric patterns
- **Burn Rate Templates**: Multi-window alerting expressions

### Technical Improvements
- **Performance Optimization**: Batch metric queries and parallel processing
- **Enhanced Error Handling**: Better diagnostics for connection issues
- **Configuration Files**: YAML/JSON configuration support
- **Prometheus Label Analysis**: Deep inspection of metric labels
- **Historical Analysis**: Trend analysis over time periods

[Unreleased]: https://github.com/YusefAmen/prom-slo-analyzer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YusefAmen/prom-slo-analyzer/releases/tag/v0.1.0