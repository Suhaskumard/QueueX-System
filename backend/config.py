"""
QueueMind Configuration
-----------------------
Central configuration for the distributed task queue system.
Supports dev (in-memory) and prod (Kafka) modes.
"""

import os


class Settings:
    # System mode: "dev" (in-memory queue) or "prod" (Kafka)
    MODE: str = os.getenv("QUEUEMIND_MODE", "dev")

    # Kafka settings (prod mode only)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # Worker configuration
    NUM_CPU_WORKERS: int = int(os.getenv("NUM_CPU_WORKERS", "2"))
    NUM_IO_WORKERS: int = int(os.getenv("NUM_IO_WORKERS", "2"))

    # Failure simulation
    WORKER_FAILURE_RATE: float = float(os.getenv("WORKER_FAILURE_RATE", "0.15"))

    # Retry configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "2.0"))
    RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", "60.0"))

    # Kafka topics
    TOPIC_QUEUE_CPU: str = "task_queue_cpu"
    TOPIC_QUEUE_IO: str = "task_queue_io"
    TOPIC_RESULTS: str = "task_results"
    TOPIC_FAILURES: str = "task_failures"
    TOPIC_MONITORING: str = "monitoring_events"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Demo workload
    DEMO_TASK_COUNT: int = 20

    # Worker execution time ranges (seconds) for simulation
    CPU_EXEC_TIME_RANGE: tuple = (2.0, 6.0)
    IO_EXEC_TIME_RANGE: tuple = (1.0, 4.0)


settings = Settings()
