# QueueMind Backend — Python 3.12 slim
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Kafka support for prod mode
RUN pip install --no-cache-dir aiokafka==0.10.0

# Copy source
COPY . .

# Default: run the API server
# Override CMD to run a worker: CMD ["python", "worker_entrypoint.py", "--type", "cpu"]
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/metrics || exit 1

CMD ["python", "main.py"]
