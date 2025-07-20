FROM python:3.12-slim

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install uv and dependencies in one optimized layer
RUN pip install --no-cache-dir uv && \
    UV_NO_SYNC=true uv sync --no-dev --locked --offline || \
    UV_HTTP_TIMEOUT=60 uv sync --no-dev --locked && \
    rm -rf ~/.cache/uv

# Copy application code
COPY app/ ./app/
COPY run.py ./
COPY scripts/ ./scripts/

ENV APP_ENV=production

# Install OpenSSL for certificate generation
RUN apt-get update && \
    apt-get install -y openssl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create volume mount points for data and certificates
VOLUME ["/app/data", "/app/certs"]

CMD ["uv", "run", "python3", "run.py"]
