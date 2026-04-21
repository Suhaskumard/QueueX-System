"""
QueueMind Task Models
---------------------
Pydantic models for tasks, results, and workload requests.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TaskStatus(str, Enum):
    CREATED = "created"
    PARTITIONED = "partitioned"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"
    STORED = "stored"


class TaskType(str, Enum):
    CPU = "cpu"
    IO = "io"
    IO_CPU = "io_cpu"


class Task(BaseModel):
    task_id: str
    description: str
    task_type: TaskType = TaskType.CPU
    priority: int = Field(default=1, ge=1, le=10)
    dependencies: list[str] = Field(default_factory=list)
    partition: str = "cpu"
    status: TaskStatus = TaskStatus.CREATED
    assigned_worker: Optional[str] = None
    result: Optional[Any] = None
    quality_score: Optional[float] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    failure_type: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    kafka_topic: Optional[str] = None
    kafka_partition: Optional[int] = None
    kafka_offset: Optional[int] = None

    def update_status(self, new_status: TaskStatus):
        self.status = new_status
        self.updated_at = datetime.utcnow()


class TaskResult(BaseModel):
    task_id: str
    worker_id: str
    status: str
    execution_time: float
    result: Any = None
    error: Optional[str] = None


class WorkloadRequest(BaseModel):
    """Incoming workload request from the API."""
    name: str = "Log Processing Pipeline"
    description: str = "Process system logs: extract IPs, deduplicate, classify, check blacklists, geolocate, detect patterns, generate reports"
    total_chunks: int = Field(default=5, ge=1, le=50)
    priority: int = Field(default=5, ge=1, le=10)
