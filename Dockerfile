FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir uv && \
    uv sync --no-dev --locked && \
    pip install --no-cache-dir .

ENV APP_ENV=production

# Create volume mount point for data persistence
VOLUME ["/app/data"]

CMD ["python3", "run.py"]
