FROM python:3.12-slim

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install uv and dependencies in one optimized layer
RUN pip install --no-cache-dir uv && \
    ( uv sync --no-dev --locked --offline || \
      UV_HTTP_TIMEOUT=60 uv sync --no-dev --locked ) && \
    rm -rf ~/.cache/uv

# Copy application code
COPY app/ ./app/
COPY run.py ./
COPY run_stdio.py ./
COPY scripts/ ./scripts/

ENV APP_ENV=production

# Install OpenSSL and update CA certificates
RUN apt-get update && \
    apt-get install -y openssl ca-certificates && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -d /app -s /bin/bash appuser && \
    mkdir -p /app/data /app/certs && chown -R appuser:appuser /app

# Create volume mount points for data and certificates
VOLUME ["/app/data", "/app/certs"]

USER appuser
CMD ["uvx", "--from", ".", "budget-mcp-server"]
