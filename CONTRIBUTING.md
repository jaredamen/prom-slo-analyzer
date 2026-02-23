# Contributing to Prometheus SLO Analyzer

Thank you for your interest in contributing to `prom-slo-analyzer`! This guide will help you get started.

## Quick Start

```bash
# Fork and clone the repository
git clone https://github.com/YusefAmen/prom-slo-analyzer.git
cd prom-slo-analyzer

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Check code quality
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## Development Environment

### Prerequisites

- Python 3.9 or higher
- Git
- A Prometheus instance for testing (optional but recommended)

### Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a virtual environment** and activate it
4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-queue-depth-classifier`
- `fix/prometheus-connection-timeout`
- `docs/update-installation-guide`

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting and import sorting
- **MyPy** for type checking

Before submitting, ensure your code passes all checks:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

### Testing

#### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names that explain what's being tested
- Follow the existing test patterns in the codebase
- Mock external dependencies (Prometheus API calls)

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/prom_slo_analyzer

# Run specific test file
pytest tests/test_client.py

# Run tests matching pattern
pytest -k "test_classify"
```

#### Test Categories

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions (mark with `@pytest.mark.integration`)

## Contributing Guidelines

### Adding New Classifiers

To add a new metric classifier (e.g., for queue depth):

1. **Create the classifier file**: `src/prom_slo_analyzer/classifiers/your_classifier.py`
2. **Follow the pattern**: Look at `latency.py` as a reference
3. **Extend the base class**: Inherit from `BaseClassifier`
4. **Implement required methods**: `sli_type` property and `classify` method
5. **Add to `__init__.py`**: Export your classifier
6. **Write comprehensive tests**: Add test file in `tests/test_classifiers/`
7. **Update documentation**: Add to README roadmap → implemented features

### Adding New Gap Detection Rules

To add a new gap detection rule:

1. **Create the rule file**: `src/prom_slo_analyzer/rules/your_rule.py`
2. **Follow the pattern**: Look at `missing_latency.py` as a reference
3. **Extend the base class**: Inherit from `BaseRule`
4. **Implement required methods**: `rule_name` property and `check` method
5. **Add to `__init__.py`**: Export your rule
6. **Write tests**: Add test file in `tests/test_rules/`

### Code Architecture

The project follows a clean pipeline architecture:

```
Input (Prometheus) → Discovery → Classification → Gap Detection → Reporting
```

- **Client**: Handles Prometheus API communication
- **Discovery**: Groups metrics by service
- **Classifiers**: Determine SLI suitability  
- **Rules**: Detect gaps in SLO readiness
- **Reports**: Format output for users

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: `pytest`
2. **Code quality checks pass**: `ruff check && black --check && mypy`
3. **Update documentation** if needed
4. **Add entry to CHANGELOG.md** under "Unreleased" section

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] New tests added for new functionality
- [ ] All existing tests pass
- [ ] Manual testing performed (describe what you tested)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by maintainers
3. **Manual testing** for significant changes
4. **Approval** and merge

## Issue Guidelines

### Bug Reports

Use the bug report template and include:

- **Environment**: OS, Python version, package version
- **Prometheus setup**: Version, configuration details
- **Steps to reproduce**: Clear, minimal example
- **Expected vs actual behavior**
- **Error messages**: Full stack traces
- **Sample metrics**: If relevant to the issue

### Feature Requests

Use the feature request template and include:

- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought about
- **Use case**: Real-world scenario where this helps

## Development Tips

### Testing Against Real Prometheus

For integration testing:

```bash
# Start Prometheus with Docker
docker run -p 9090:9090 prom/prometheus

# Test against it
prom-slo-analyzer scan --prometheus-url http://localhost:9090
```

### Adding Sample Data

Create realistic test fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def sample_metrics():
    return [
        "your_service_requests_total",
        "your_service_duration_seconds_bucket",
        # ... more realistic metric names
    ]
```

### Debugging

Use the `--debug` flag for detailed output:

```bash
prom-slo-analyzer scan --prometheus-url http://localhost:9090 --debug
```

## Release Process

Releases are automated via GitHub Actions when a release is published:

1. **Update version** in `pyproject.toml` and `src/prom_slo_analyzer/__init__.py`
2. **Update CHANGELOG.md** with release notes
3. **Create release** on GitHub with version tag (e.g., `v0.2.0`)
4. **Automated pipeline** builds and publishes to PyPI

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join our Discord (link in README)
- **Email**: Reach out to maintainers directly for sensitive topics

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Please be respectful and inclusive.

## Recognition

Contributors are recognized in:
- GitHub contributors page
- CHANGELOG.md for significant contributions
- README.md hall of fame (coming soon)

---

Thank you for contributing to making SLO adoption easier for everyone! 🎉