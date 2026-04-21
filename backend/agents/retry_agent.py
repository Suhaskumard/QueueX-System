"""
QueueMind — Retry & Failure Agent
-----------------------------------
Detects and classifies task failures, implements exponential backoff
retry strategy, and routes permanently failed tasks to dead letter.
"""

import asyncio
import logging
import random
from datetime import datetime

from config import settings
from models.task import Task, TaskResult, TaskStatus
from store.task_store import TaskStore

logger = logging.getLogger("queuemind.retry")


# Failure patterns that indicate transient vs permanent failures
TRANSIENT_PATTERNS = [
    "ConnectionTimeout",
    "RateLimitExceeded",
    "IOError: temporary",
    "ServiceUnavailable",
]

PERMANENT_PATTERNS = [
    "MemoryError",
    "ParseError",
    "ValidationError",
    "SchemaError",
]


class RetryAgent:
    """
    Retry & Failure Agent — Handles task failures intelligently.

    Responsibilities:
    - Detect and classify failures (transient vs permanent)
    - Apply exponential backoff for retries
    - Enforce max retry limits
    - Route permanently failed tasks to dead letter
    """

    def __init__(self, store: TaskStore):
        self.agent_name = "retry"
        self._store = store

    def classify_failure(self, error: str) -> str:
        """Classify a failure as transient or permanent."""
        for pattern in TRANSIENT_PATTERNS:
            if pattern.lower() in error.lower():
                return "transient"
        for pattern in PERMANENT_PATTERNS:
            if pattern.lower() in error.lower():
                return "permanent"
        # Default to transient (optimistic)
        return "transient"

    def calculate_delay(self, retry_count: int) -> float:
        """
        Calculate retry delay using exponential backoff with jitter.
        delay = min(base * 2^retry + jitter, max_delay)
        """
        base_delay = settings.RETRY_BASE_DELAY * (2 ** retry_count)
        jitter = random.uniform(0, 1.0)
        delay = min(base_delay + jitter, settings.RETRY_MAX_DELAY)
        return round(delay, 1)

    async def handle_failure(self, task: Task, result: TaskResult) -> dict:
        """
        Process a failed task. Decides whether to retry or permanently fail.

        Returns a dict with the retry decision and metadata.
        """
        error = result.error or "Unknown error"
        failure_type = self.classify_failure(error)
        current_retry = task.retry_count

        logger.info(f"[Retry] Handling failure for {task.task_id}: {failure_type} (retry {current_retry})")

        # Store failure log
        await self._store.add_failure_log({
            "task_id": task.task_id,
            "error": error,
            "failure_type": failure_type,
            "retry_count": current_retry,
            "worker_id": result.worker_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Permanent failure or max retries exceeded
        if failure_type == "permanent" or current_retry >= settings.MAX_RETRIES:
            await self._store.update_task(
                task.task_id,
                status=TaskStatus.FAILED,
                failure_type=failure_type,
                error_message=error,
            )

            reason = "permanent failure" if failure_type == "permanent" else f"max retries ({settings.MAX_RETRIES}) exceeded"
            logger.warning(f"[Retry] Task {task.task_id} PERMANENTLY FAILED: {reason}")

            return {
                "agent": self.agent_name,
                "task_id": task.task_id,
                "failure_type": failure_type,
                "retry_count": current_retry,
                "action": "dead_letter",
                "reason": reason,
            }

        # Transient failure — schedule retry
        delay = self.calculate_delay(current_retry)
        new_retry_count = current_retry + 1

        await self._store.update_task(
            task.task_id,
            retry_count=new_retry_count,
            status=TaskStatus.CREATED,
            failure_type=failure_type,
            error_message=error,
            assigned_worker=None,
        )

        await self._store.increment_retries()

        logger.info(f"[Retry] Task {task.task_id} scheduled for retry #{new_retry_count} in {delay}s")

        return {
            "agent": self.agent_name,
            "task_id": task.task_id,
            "failure_type": failure_type,
            "retry_count": new_retry_count,
            "next_retry_delay": f"{delay}s",
            "action": "retry",
        }

    async def get_retry_delay(self, task: Task) -> float:
        """Get the delay before next retry for a task."""
        return self.calculate_delay(task.retry_count)
