"""
QueueMind Event Models
----------------------
Models for monitoring events, system summaries, and worker status.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MonitoringEvent(BaseModel):
    event: str
    task_id: Optional[str] = None
    worker: Optional[str] = None
    time: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: str = "monitor"
    level: str = "info"  # info, warn, error, success


class SystemSummary(BaseModel):
    tasks_total: int = 0
    completed: int = 0
    failed: int = 0
    validated: int = 0
    retries: int = 0
    avg_latency: str = "0s"
    throughput: str = "0 tasks/min"
    system_health: str = "stable"  # stable, degraded, critical
    uptime: str = "0s"
    queue_depth: int = 0


class WorkerStatus(BaseModel):
    worker_id: str
    worker_type: str  # "cpu" or "io"
    load_pct: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    status: str = "idle"  # idle, busy, offline
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)


class MetricsSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    throughput: float = 0.0  # tasks per minute
    avg_latency: float = 0.0  # seconds
    failure_rate: float = 0.0  # percentage
    queue_depth: int = 0
    active_workers: int = 0
    tasks_by_status: dict[str, int] = Field(default_factory=dict)
