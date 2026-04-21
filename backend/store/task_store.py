"""
QueueMind — Task State Store
-----------------------------
Thread-safe in-memory store for tasks, execution history,
failure logs, and worker performance metrics.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from collections import defaultdict

from models.task import Task, TaskStatus
from models.events import WorkerStatus, SystemSummary, MetricsSnapshot

logger = logging.getLogger("queuemind.store")


class TaskStore:
    """
    Central in-memory state store for all tasks and workers.
    Uses asyncio.Lock for safe concurrent access.
    """

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._workers: dict[str, WorkerStatus] = {}
        self._execution_history: list[dict[str, Any]] = []
        self._failure_logs: list[dict[str, Any]] = []
        self._metrics_history: list[MetricsSnapshot] = []
        self._total_retries: int = 0
        self._start_time: datetime = datetime.now(timezone.utc)
        self._lock = asyncio.Lock()

    # ── Task Operations ─────────────────────────────────────────────

    async def add_task(self, task: Task) -> None:
        async with self._lock:
            self._tasks[task.task_id] = task
            logger.debug(f"[Store] Added task {task.task_id}")

    async def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"[Store] Task {task_id} not found for update")
                return None
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.utcnow()
            return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def get_all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    async def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    async def are_dependencies_met(self, task: Task) -> bool:
        """Check if all dependency tasks are validated."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or dep_task.status not in (TaskStatus.VALIDATED, TaskStatus.STORED):
                return False
        return True

    # ── Worker Operations ────────────────────────────────────────────

    async def register_worker(self, worker: WorkerStatus) -> None:
        async with self._lock:
            self._workers[worker.worker_id] = worker
            logger.info(f"[Store] Registered worker {worker.worker_id}")

    async def update_worker(self, worker_id: str, **kwargs) -> Optional[WorkerStatus]:
        async with self._lock:
            worker = self._workers.get(worker_id)
            if not worker:
                return None
            for key, value in kwargs.items():
                if hasattr(worker, key):
                    setattr(worker, key, value)
            worker.last_heartbeat = datetime.utcnow()
            return worker

    async def get_worker(self, worker_id: str) -> Optional[WorkerStatus]:
        return self._workers.get(worker_id)

    async def get_all_workers(self) -> list[WorkerStatus]:
        return list(self._workers.values())

    async def get_least_loaded_worker(self, worker_type: str) -> Optional[WorkerStatus]:
        """Find the least loaded worker of a given type."""
        candidates = [
            w for w in self._workers.values()
            if w.worker_type == worker_type and w.status != "offline"
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda w: w.load_pct)

    # ── History & Logs ───────────────────────────────────────────────

    async def add_execution_record(self, record: dict) -> None:
        async with self._lock:
            self._execution_history.append(record)

    async def add_failure_log(self, log: dict) -> None:
        async with self._lock:
            self._failure_logs.append(log)

    async def increment_retries(self) -> None:
        async with self._lock:
            self._total_retries += 1

    async def add_metrics_snapshot(self, snapshot: MetricsSnapshot) -> None:
        async with self._lock:
            self._metrics_history.append(snapshot)
            # Keep last 300 snapshots (5 min at 1/sec)
            if len(self._metrics_history) > 300:
                self._metrics_history = self._metrics_history[-300:]

    # ── Aggregated Queries ───────────────────────────────────────────

    async def get_summary(self) -> SystemSummary:
        async with self._lock:
            total = len(self._tasks)
            completed = sum(1 for t in self._tasks.values() if t.status in (TaskStatus.COMPLETED, TaskStatus.VALIDATED, TaskStatus.STORED))
            failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
            validated = sum(1 for t in self._tasks.values() if t.status in (TaskStatus.VALIDATED, TaskStatus.STORED))

            exec_times = [t.execution_time for t in self._tasks.values() if t.execution_time is not None]
            avg_lat = sum(exec_times) / len(exec_times) if exec_times else 0

            elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds()
            throughput = (completed / elapsed * 60) if elapsed > 0 else 0

            # Determine system health
            failure_rate = (failed / total * 100) if total > 0 else 0
            if failure_rate > 30:
                health = "critical"
            elif failure_rate > 10:
                health = "degraded"
            else:
                health = "stable"

            return SystemSummary(
                tasks_total=total,
                completed=completed,
                failed=failed,
                validated=validated,
                retries=self._total_retries,
                avg_latency=f"{avg_lat:.1f}s",
                throughput=f"{throughput:.0f} tasks/min",
                system_health=health,
                uptime=f"{elapsed:.0f}s",
            )

    async def get_tasks_by_status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for task in self._tasks.values():
            counts[task.status.value] += 1
        return dict(counts)

    async def get_metrics_history(self) -> list[MetricsSnapshot]:
        return list(self._metrics_history)

    async def get_failure_logs(self) -> list[dict]:
        return list(self._failure_logs)

    async def get_recent_execution_history(self, limit: int = 50) -> list[dict]:
        return self._execution_history[-limit:]
