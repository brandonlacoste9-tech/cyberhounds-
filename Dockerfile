# 🐺 CYBERHOUND DOCKER IMAGE
# Production-ready container for compliance hunting

FROM python:3.11-slim as base

# Security: Run as non-root user
RUN groupadd -r cyberhound && useradd -r -g cyberhound cyberhound

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hound_core/ ./hound_core/
COPY web_dashboard/ ./web_dashboard/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Create data directory
RUN mkdir -p /app/hound_core/data/logs && \
    chown -R cyberhound:cyberhound /app

# Switch to non-root user
USER cyberhound

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/hound_core/data
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, 'hound_core'); from health_check import check_health; r = check_health(); sys.exit(0 if r['healthy'] else 1)"

# Default command
CMD ["python", "-m", "hound_core.cron_hunt"]

# Labels
LABEL maintainer="Cyberhound Team"
LABEL description="B2B Compliance Gap Hunting System"
LABEL version="2.1"

# Multi-stage build for smaller production image
FROM base as production

# Remove test files from production
RUN rm -rf tests/

# Final image
FROM production

# Expose port for web dashboard (optional)
EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["-m", "hound_core.cron_hunt"]
