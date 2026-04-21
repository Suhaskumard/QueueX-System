"""
QueueMind — Load Balancer Agent
--------------------------------
Assigns Kafka partitions to workers using least-loaded-first strategy.
Monitors and tracks worker utilization in real-time.
"""

import logging
from typing import Optional

from models.task import Task, TaskStatus
from models.events import WorkerStatus
from store.task_store import TaskStore

logger = logging.getLogger("queuemind.loadbalancer")


class LoadBalancerAgent:
    """
    Load Balancer Agent — Assigns tasks to workers.

    Responsibilities:
    - Maintain worker registry
    - Track worker load percentages
    - Use least-loaded-first assignment
    - Support dynamic worker registration
    """

    def __init__(self, store: TaskStore):
        self.agent_name = "load_balancer"
        self._store = store

    async def register_workers(self, cpu_count: int, io_count: int) -> None:
        """Register CPU and IO workers."""
        for i in range(1, cpu_count + 1):
            worker = WorkerStatus(
                worker_id=f"worker_cpu_{i}",
                worker_type="cpu",
                status="idle",
            )
            await self._store.register_worker(worker)

        for i in range(1, io_count + 1):
            worker = WorkerStatus(
                worker_id=f"worker_io_{i}",
                worker_type="io",
                status="idle",
            )
            await self._store.register_worker(worker)

        logger.info(f"[LoadBalancer] Registered {cpu_count} CPU + {io_count} IO workers")

    async def assign_worker(self, task: Task) -> Optional[dict]:
        """
        Assign a task to the least-loaded appropriate worker.
        Returns assignment dict or None if no worker available.
        """
        # Determine required worker type
        worker_type = "io" if task.partition == "io" else "cpu"

        worker = await self._store.get_least_loaded_worker(worker_type)
        if not worker:
            logger.warning(f"[LoadBalancer] No available {worker_type} worker for {task.task_id}")
            return None

        # Update worker state
        await self._store.update_worker(
            worker.worker_id,
            status="busy",
            current_task=task.task_id,
            load_pct=min(100.0, worker.load_pct + 25.0),
        )

        # Update task assignment
        await self._store.update_task(
            task.task_id,
            status=TaskStatus.ASSIGNED,
            assigned_worker=worker.worker_id,
        )

        logger.info(f"[LoadBalancer] Assigned {task.task_id} → {worker.worker_id} (load: {worker.load_pct + 25:.0f}%)")

        return {
            "agent": self.agent_name,
            "task_id": task.task_id,
            "assigned_worker": worker.worker_id,
            "worker_load": f"{min(100, worker.load_pct + 25):.0f}%",
        }

    async def release_worker(self, worker_id: str, success: bool = True) -> None:
        """Release a worker after task completion or failure."""
        worker = await self._store.get_worker(worker_id)
        if not worker:
            return

        updates = {
            "status": "idle",
            "current_task": None,
            "load_pct": max(0.0, worker.load_pct - 25.0),
        }
        if success:
            updates["tasks_completed"] = worker.tasks_completed + 1
        else:
            updates["tasks_failed"] = worker.tasks_failed + 1

        await self._store.update_worker(worker_id, **updates)

    async def get_utilization_snapshot(self) -> list[dict]:
        """Get current utilization for all workers."""
        workers = await self._store.get_all_workers()
        return [
            {
                "worker_id": w.worker_id,
                "type": w.worker_type,
                "load": w.load_pct,
                "status": w.status,
                "tasks_completed": w.tasks_completed,
                "tasks_failed": w.tasks_failed,
                "current_task": w.current_task,
            }
            for w in workers
        ]
