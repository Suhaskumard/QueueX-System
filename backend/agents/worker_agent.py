"""
QueueMind — Worker Execution Agent
------------------------------------
Simulates task execution with realistic timing and configurable failure rates.
CPU workers handle compute-heavy tasks, IO workers handle API/file operations.
"""

import asyncio
import random
import logging
import hashlib
import time
from typing import Any

from config import settings
from models.task import Task, TaskResult, TaskStatus

logger = logging.getLogger("queuemind.worker")


# ── Simulated Work Functions ────────────────────────────────────────

async def _simulate_cpu_work(task: Task) -> dict:
    """Simulate CPU-intensive work (hashing, sorting, matrix ops)."""
    duration = random.uniform(*settings.CPU_EXEC_TIME_RANGE)
    await asyncio.sleep(duration)

    # Simulate actual computation
    data = f"{task.task_id}:{task.description}:{time.time()}"
    result_hash = hashlib.sha256(data.encode()).hexdigest()[:16]

    results = {
        "extract_ips": {"ips_found": random.randint(50, 500), "hash": result_hash},
        "deduplicate": {"unique_entries": random.randint(30, 300), "duplicates_removed": random.randint(10, 100)},
        "classify": {"internal": random.randint(20, 150), "external": random.randint(10, 200)},
        "pattern_detect": {"suspicious_patterns": random.randint(0, 15), "risk_score": round(random.uniform(0.1, 9.5), 1)},
        "generate_report": {"report_id": result_hash, "pages": random.randint(5, 30), "format": "PDF+CSV"},
        "aggregate": {"chunks_merged": True, "final_report_id": result_hash},
    }

    # Find matching result based on task description
    for key, value in results.items():
        if key in task.task_id:
            return {"output": value, "compute_hash": result_hash, "duration": round(duration, 2)}

    return {"output": "computed_result", "compute_hash": result_hash, "duration": round(duration, 2)}


async def _simulate_io_work(task: Task) -> dict:
    """Simulate IO-bound work (API calls, file reading)."""
    duration = random.uniform(*settings.IO_EXEC_TIME_RANGE)
    await asyncio.sleep(duration)

    results = {
        "extract_ips": {"ips_extracted": random.randint(100, 1000), "log_lines_read": random.randint(5000, 50000)},
        "blacklist_check": {"checked": random.randint(50, 200), "blacklisted": random.randint(0, 10), "api_calls": random.randint(3, 15)},
        "geolocation": {"geolocated": random.randint(30, 150), "countries": random.randint(5, 30), "api_latency_ms": random.randint(50, 300)},
        "generate_report": {"files_written": 2, "csv_rows": random.randint(100, 5000), "pdf_pages": random.randint(5, 20)},
    }

    for key, value in results.items():
        if key in task.task_id:
            return {"output": value, "io_ops": random.randint(5, 50), "duration": round(duration, 2)}

    return {"output": "io_result", "io_ops": random.randint(5, 50), "duration": round(duration, 2)}


class WorkerExecutionAgent:
    """
    Worker Execution Agent — Processes tasks in isolation.

    Responsibilities:
    - Execute CPU and IO tasks
    - Simulate realistic work with configurable timing
    - Inject failures at configured rate
    - Report results and errors
    """

    def __init__(self):
        self.agent_name = "worker"

    async def execute(self, task: Task, worker_id: str) -> TaskResult:
        """
        Execute a task and return a TaskResult.
        May fail based on WORKER_FAILURE_RATE.
        """
        start_time = time.time()

        logger.info(f"[Worker:{worker_id}] Executing {task.task_id} ({task.task_type.value})")

        try:
            # Check for simulated failure
            if random.random() < settings.WORKER_FAILURE_RATE:
                # Simulate failure
                failure_delay = random.uniform(0.5, 2.0)
                await asyncio.sleep(failure_delay)

                failure_types = [
                    "ConnectionTimeout: upstream service unreachable",
                    "MemoryError: worker heap exhausted",
                    "IOError: temporary disk write failure",
                    "RateLimitExceeded: API throttled",
                    "ParseError: malformed log entry encountered",
                ]
                error = random.choice(failure_types)
                elapsed = time.time() - start_time

                logger.warning(f"[Worker:{worker_id}] Task {task.task_id} FAILED: {error}")

                return TaskResult(
                    task_id=task.task_id,
                    worker_id=worker_id,
                    status="failed",
                    execution_time=round(elapsed, 2),
                    error=error,
                )

            # Execute based on task type
            if task.task_type.value == "io":
                result = await _simulate_io_work(task)
            else:
                result = await _simulate_cpu_work(task)

            elapsed = time.time() - start_time

            logger.info(f"[Worker:{worker_id}] Task {task.task_id} COMPLETED in {elapsed:.2f}s")

            return TaskResult(
                task_id=task.task_id,
                worker_id=worker_id,
                status="completed",
                execution_time=round(elapsed, 2),
                result=result,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[Worker:{worker_id}] Task {task.task_id} EXCEPTION: {e}")
            return TaskResult(
                task_id=task.task_id,
                worker_id=worker_id,
                status="failed",
                execution_time=round(elapsed, 2),
                error=str(e),
            )
