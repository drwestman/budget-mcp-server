FROM python:3.12-slim

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install uv and dependencies in one optimized layer
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --locked && \
    rm -rf ~/.cache/uv

# Copy application code
COPY app/ ./app/
COPY run.py ./

ENV APP_ENV=production

# Create volume mount point for data persistence
VOLUME ["/app/data"]

CMD ["uv", "run", "python3", "run.py"]
