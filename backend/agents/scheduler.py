"""
QueueMind — Scheduler Agent
-----------------------------
Routes planned tasks to appropriate Kafka topics and partitions.
Respects dependency ordering — tasks with unmet deps are held.
"""

import asyncio
import logging
from typing import Optional

from config import settings
from models.task import Task, TaskStatus, TaskType
from queue.base import MessageQueue
from store.task_store import TaskStore

logger = logging.getLogger("queuemind.scheduler")


class SchedulerAgent:
    """
    Scheduler Agent — Routes tasks to message queue topics.

    Responsibilities:
    - Map task_type → Kafka topic
    - Assign partitions (round-robin)
    - Respect dependency ordering
    - Track offsets
    """

    def __init__(self, queue: MessageQueue, store: TaskStore):
        self.agent_name = "scheduler"
        self._queue = queue
        self._store = store
        self._partition_counter: dict[str, int] = {}
        self._pending_tasks: list[Task] = []

    def _get_topic(self, task: Task) -> str:
        """Map task type to Kafka topic."""
        if task.task_type == TaskType.IO:
            return settings.TOPIC_QUEUE_IO
        return settings.TOPIC_QUEUE_CPU

    def _next_partition(self, topic: str) -> int:
        """Round-robin partition assignment."""
        if topic not in self._partition_counter:
            self._partition_counter[topic] = 0
        partition = self._partition_counter[topic]
        self._partition_counter[topic] = (partition + 1) % 4
        return partition

    async def schedule(self, tasks: list[Task]) -> list[dict]:
        """
        Schedule a list of tasks. Tasks with unmet dependencies
        are held in pending and retried later.
        """
        results = []
        self._pending_tasks.extend(tasks)

        scheduled = True
        while scheduled:
            scheduled = False
            still_pending = []

            for task in self._pending_tasks:
                deps_met = await self._store.are_dependencies_met(task)
                if deps_met:
                    result = await self._schedule_single(task)
                    results.append(result)
                    scheduled = True
                else:
                    still_pending.append(task)

            self._pending_tasks = still_pending

        if self._pending_tasks:
            logger.info(f"[Scheduler] {len(self._pending_tasks)} tasks waiting for dependencies")

        return results

    async def retry_pending(self) -> list[dict]:
        """Re-attempt scheduling of pending tasks (called periodically)."""
        if not self._pending_tasks:
            return []
        return await self.schedule([])  # Will process existing pending list

    async def _schedule_single(self, task: Task) -> dict:
        """Schedule a single task to its queue."""
        topic = self._get_topic(task)
        partition = self._next_partition(topic)

        # Update task state
        task.kafka_topic = topic
        task.kafka_partition = partition
        task.update_status(TaskStatus.QUEUED)

        # Produce to queue
        message = {
            "task_id": task.task_id,
            "description": task.description,
            "task_type": task.task_type.value,
            "priority": task.priority,
            "dependencies": task.dependencies,
        }
        offset = await self._queue.produce(topic, message, partition)
        task.kafka_offset = offset

        # Save to store
        await self._store.update_task(
            task.task_id,
            status=TaskStatus.QUEUED,
            kafka_topic=topic,
            kafka_partition=partition,
            kafka_offset=offset,
        )

        logger.info(f"[Scheduler] Queued {task.task_id} → {topic}[{partition}] offset={offset}")

        return {
            "agent": self.agent_name,
            "task_id": task.task_id,
            "kafka_topic": topic,
            "partition": partition,
            "offset": offset,
        }

    @property
    def pending_count(self) -> int:
        return len(self._pending_tasks)
