"""
test_worker.py — Unit tests for WorkerExecutionAgent
Run: pytest backend/tests/test_worker.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import pytest
from agents.worker_agent import WorkerExecutionAgent
from models.task import Task, TaskType, TaskStatus
from config import settings


@pytest.fixture
def worker():
    return WorkerExecutionAgent()


@pytest.fixture
def cpu_task():
    return Task(
        task_id="task_deduplicate_chunk_1",
        description="Deduplicate extracted entries (chunk 1)",
        task_type=TaskType.CPU,
        priority=5,
        partition="cpu",
    )


@pytest.fixture
def io_task():
    return Task(
        task_id="task_extract_ips_chunk_1",
        description="Extract IP addresses from log chunk (chunk 1)",
        task_type=TaskType.IO,
        priority=5,
        partition="io",
    )


def test_cpu_task_returns_result(worker, cpu_task):
    # Disable failures for deterministic tests
    settings.WORKER_FAILURE_RATE = 0.0
    result = asyncio.run(worker.execute(cpu_task, "worker_cpu_1"))
    assert result.task_id == cpu_task.task_id
    assert result.worker_id == "worker_cpu_1"
    assert result.status in ("completed", "failed")


def test_io_task_returns_result(worker, io_task):
    settings.WORKER_FAILURE_RATE = 0.0
    result = asyncio.run(worker.execute(io_task, "worker_io_1"))
    assert result.task_id == io_task.task_id
    assert result.status in ("completed", "failed")


def test_execution_time_recorded(worker, cpu_task):
    settings.WORKER_FAILURE_RATE = 0.0
    result = asyncio.run(worker.execute(cpu_task, "worker_cpu_1"))
    assert result.execution_time is not None
    assert result.execution_time > 0


def test_failure_simulation(worker, cpu_task):
    settings.WORKER_FAILURE_RATE = 1.0  # Force 100% failure
    result = asyncio.run(worker.execute(cpu_task, "worker_cpu_1"))
    assert result.status == "failed"
    assert result.error is not None
    # Restore
    settings.WORKER_FAILURE_RATE = 0.15


def test_success_has_result_payload(worker, cpu_task):
    settings.WORKER_FAILURE_RATE = 0.0
    result = asyncio.run(worker.execute(cpu_task, "worker_cpu_1"))
    if result.status == "completed":
        assert result.result is not None
