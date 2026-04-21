"""
QueueMind — Monitor Agent
---------------------------
Aggregates events from all agents, computes real-time metrics,
and feeds the WebSocket manager for dashboard updates.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from models.events import MonitoringEvent, MetricsSnapshot
from store.task_store import TaskStore
from websocket.manager import ConnectionManager

logger = logging.getLogger("queuemind.monitor")


class MonitorAgent:
    """
    Monitoring & Dashboard Agent — Real-time system observability.

    Responsibilities:
    - Emit real-time system events
    - Compute metrics (throughput, latency, failure rate)
    - Feed WebSocket manager for dashboard
    - Maintain event log buffer
    """

    def __init__(self, store: TaskStore, ws_manager: ConnectionManager):
        self.agent_name = "monitor"
        self._store = store
        self._ws = ws_manager
        self._event_log: list[MonitoringEvent] = []
        self._start_time = time.time()
        self._running = False

    async def emit(self, event: str, task_id: Optional[str] = None,
                   worker: Optional[str] = None, details: Optional[dict] = None,
                   level: str = "info") -> None:
        """Emit a monitoring event and broadcast to dashboard."""
        elapsed = round(time.time() - self._start_time, 1)

        evt = MonitoringEvent(
            event=event,
            task_id=task_id,
            worker=worker,
            time=f"{elapsed}s",
            details=details,
            level=level,
        )

        self._event_log.append(evt)
        # Keep last 500 events
        if len(self._event_log) > 500:
            self._event_log = self._event_log[-500:]

        # Broadcast to dashboard
        await self._ws.broadcast("log_entry", {
            "event": evt.event,
            "task_id": evt.task_id,
            "worker": evt.worker,
            "time": evt.time,
            "level": evt.level,
            "details": evt.details,
            "timestamp": evt.timestamp.isoformat(),
        })

    async def emit_task_update(self, task_id: str, status: str, **kwargs) -> None:
        """Emit a task status update to dashboard."""
        from models.task import Task
        task = await self._store.get_task(task_id)
        if task:
            await self._ws.broadcast("task_update", {
                "task_id": task.task_id,
                "description": task.description,
                "task_type": task.task_type.value,
                "priority": task.priority,
                "status": task.status.value,
                "assigned_worker": task.assigned_worker,
                "execution_time": task.execution_time,
                "quality_score": task.quality_score,
                "retry_count": task.retry_count,
                **kwargs,
            })

    async def emit_worker_update(self) -> None:
        """Broadcast current worker state to dashboard."""
        workers = await self._store.get_all_workers()
        worker_data = [
            {
                "worker_id": w.worker_id,
                "worker_type": w.worker_type,
                "load_pct": w.load_pct,
                "tasks_completed": w.tasks_completed,
                "tasks_failed": w.tasks_failed,
                "current_task": w.current_task,
                "status": w.status,
            }
            for w in workers
        ]
        await self._ws.broadcast("worker_update", worker_data)

    async def emit_metrics(self) -> None:
        """Compute and broadcast current system metrics."""
        summary = await self._store.get_summary()
        status_counts = await self._store.get_tasks_by_status_counts()

        elapsed = time.time() - self._start_time
        total_tasks = summary.tasks_total
        completed = summary.completed

        # Calculate rates
        throughput = (completed / elapsed * 60) if elapsed > 0 else 0
        failure_rate = (summary.failed / total_tasks * 100) if total_tasks > 0 else 0

        # Get execution times for avg latency
        all_tasks = await self._store.get_all_tasks()
        exec_times = [t.execution_time for t in all_tasks if t.execution_time]
        avg_latency = sum(exec_times) / len(exec_times) if exec_times else 0

        snapshot = MetricsSnapshot(
            throughput=round(throughput, 1),
            avg_latency=round(avg_latency, 2),
            failure_rate=round(failure_rate, 1),
            queue_depth=0,
            active_workers=sum(1 for w in await self._store.get_all_workers() if w.status == "busy"),
            tasks_by_status=status_counts,
        )

        await self._store.add_metrics_snapshot(snapshot)

        await self._ws.broadcast("metric_update", {
            "throughput": snapshot.throughput,
            "avg_latency": snapshot.avg_latency,
            "failure_rate": snapshot.failure_rate,
            "queue_depth": snapshot.queue_depth,
            "active_workers": snapshot.active_workers,
            "tasks_by_status": snapshot.tasks_by_status,
            "tasks_total": total_tasks,
            "completed": completed,
            "failed": summary.failed,
            "retries": summary.retries,
            "system_health": summary.system_health,
            "uptime": f"{elapsed:.0f}s",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def emit_summary(self) -> None:
        """Broadcast final system summary."""
        summary = await self._store.get_summary()
        await self._ws.broadcast("system_summary", summary.model_dump())

    async def start_metrics_loop(self, interval: float = 1.0) -> None:
        """Start periodic metrics emission."""
        self._running = True
        logger.info("[Monitor] Starting metrics loop")
        while self._running:
            try:
                await self.emit_metrics()
                await self.emit_worker_update()
            except Exception as e:
                logger.error(f"[Monitor] Metrics loop error: {e}")
            await asyncio.sleep(interval)

    async def stop(self) -> None:
        self._running = False

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Get recent events for API."""
        return [
            {
                "event": e.event,
                "task_id": e.task_id,
                "worker": e.worker,
                "time": e.time,
                "level": e.level,
                "details": e.details,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self._event_log[-limit:]
        ]
