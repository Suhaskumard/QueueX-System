"""
test_store.py — Unit tests for TaskStore
Run: pytest backend/tests/test_store.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import pytest
from store.task_store import TaskStore
from models.task import Task, TaskStatus, TaskType


@pytest.fixture
def store():
    return TaskStore()


@pytest.fixture
def sample_task():
    return Task(
        task_id="task_test_001",
        description="Test task",
        task_type=TaskType.CPU,
        priority=5,
        partition="cpu",
    )


def test_add_and_get_task(store, sample_task):
    asyncio.run(store.add_task(sample_task))
    result = asyncio.run(store.get_task("task_test_001"))
    assert result is not None
    assert result.task_id == "task_test_001"


def test_get_nonexistent_task_returns_none(store):
    result = asyncio.run(store.get_task("does_not_exist"))
    assert result is None


def test_update_task_status(store, sample_task):
    asyncio.run(store.add_task(sample_task))
    asyncio.run(store.update_task("task_test_001", status=TaskStatus.RUNNING))
    task = asyncio.run(store.get_task("task_test_001"))
    assert task.status == TaskStatus.RUNNING


def test_get_all_tasks(store, sample_task):
    asyncio.run(store.add_task(sample_task))
    all_tasks = asyncio.run(store.get_all_tasks())
    assert len(all_tasks) >= 1


def test_get_tasks_by_status(store, sample_task):
    asyncio.run(store.add_task(sample_task))
    asyncio.run(store.update_task("task_test_001", status=TaskStatus.QUEUED))
    queued = asyncio.run(store.get_tasks_by_status(TaskStatus.QUEUED))
    assert any(t.task_id == "task_test_001" for t in queued)


def test_summary_counts(store, sample_task):
    asyncio.run(store.add_task(sample_task))
    asyncio.run(store.update_task("task_test_001", status=TaskStatus.COMPLETED))
    summary = asyncio.run(store.get_summary())
    assert summary.tasks_total >= 1
    assert summary.completed >= 1
