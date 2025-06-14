FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV APP_ENV=production

# Create volume mount point for data persistence
VOLUME ["/app/data"]

CMD ["python3", "run.py"]