# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN groupadd --gid 1000 analyzer && \
    useradd --uid 1000 --gid analyzer --shell /bin/bash --create-home analyzer

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package and its dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Switch to non-root user
USER analyzer

# Set the default command to run the CLI
ENTRYPOINT ["prom-slo-analyzer"]
CMD ["scan", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD prom-slo-analyzer --version || exit 1

# Labels for metadata
LABEL org.opencontainers.image.title="Prometheus SLO Analyzer"
LABEL org.opencontainers.image.description="Analyze Prometheus metrics for SLO readiness"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="Jared (Yusef) Amen <yusef@example.com>"
LABEL org.opencontainers.image.url="https://github.com/YusefAmen/prom-slo-analyzer"
LABEL org.opencontainers.image.source="https://github.com/YusefAmen/prom-slo-analyzer"
LABEL org.opencontainers.image.licenses="MIT"