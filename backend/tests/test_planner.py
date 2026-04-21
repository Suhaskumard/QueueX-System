"""
test_planner.py — Unit tests for PlannerAgent
Run: pytest backend/tests/test_planner.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import pytest
from agents.planner import PlannerAgent
from models.task import WorkloadRequest, TaskStatus, TaskType


@pytest.fixture
def planner():
    return PlannerAgent()


@pytest.fixture
def workload():
    return WorkloadRequest(name="Test Workload", total_chunks=2, priority=5)


def test_plan_creates_tasks(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    # 7 pipeline stages × 2 chunks + 1 final aggregation
    assert len(tasks) == 7 * 2 + 1


def test_all_tasks_have_correct_status(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    for task in tasks:
        assert task.status == TaskStatus.CREATED


def test_dependency_resolution(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    task_ids = {t.task_id for t in tasks}

    # All dependencies must reference valid task IDs
    for task in tasks:
        for dep in task.dependencies:
            assert dep in task_ids, f"Missing dependency: {dep}"


def test_aggregate_task_depends_on_all_reports(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    agg = next(t for t in tasks if "aggregate" in t.task_id)
    report_ids = {t.task_id for t in tasks if "generate_report" in t.task_id}
    assert set(agg.dependencies) == report_ids


def test_task_types_assigned(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    types = {t.task_type for t in tasks}
    # Should have both CPU and IO tasks
    assert TaskType.CPU in types
    assert TaskType.IO in types


def test_plan_output_format(planner, workload):
    tasks = asyncio.run(planner.plan(workload))
    output = planner.get_plan_output(tasks)
    assert "agent" in output
    assert output["agent"] == "planner"
    assert "tasks" in output
    assert len(output["tasks"]) == len(tasks)


def test_priority_propagated(planner):
    high_priority = WorkloadRequest(total_chunks=1, priority=9)
    tasks = asyncio.run(planner.plan(high_priority))
    for task in tasks:
        assert task.priority == 9
