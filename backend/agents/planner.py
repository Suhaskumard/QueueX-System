"""
QueueMind — Planner Agent
--------------------------
Decomposes incoming workloads into subtasks with intelligent chunking,
dependency mapping, and task type classification.
"""

import logging
from typing import Any

from models.task import Task, TaskStatus, TaskType, WorkloadRequest

logger = logging.getLogger("queuemind.planner")


# ── Log Processing Pipeline Task Templates ────────────────────────────

PIPELINE_STAGES = [
    {
        "stage": "extract_ips",
        "description": "Extract IP addresses from log chunk",
        "task_type": TaskType.IO,
        "partition": "io",
        "depends_on": [],
    },
    {
        "stage": "deduplicate",
        "description": "Deduplicate extracted entries",
        "task_type": TaskType.CPU,
        "partition": "cpu",
        "depends_on": ["extract_ips"],
    },
    {
        "stage": "classify",
        "description": "Classify IPs as internal/external",
        "task_type": TaskType.CPU,
        "partition": "cpu",
        "depends_on": ["deduplicate"],
    },
    {
        "stage": "blacklist_check",
        "description": "Check against blacklist API",
        "task_type": TaskType.IO,
        "partition": "io",
        "depends_on": ["classify"],
    },
    {
        "stage": "geolocation",
        "description": "Geolocation lookup for external IPs",
        "task_type": TaskType.IO,
        "partition": "io",
        "depends_on": ["classify"],
    },
    {
        "stage": "pattern_detect",
        "description": "Detect suspicious access patterns",
        "task_type": TaskType.CPU,
        "partition": "cpu",
        "depends_on": ["blacklist_check", "geolocation"],
    },
    {
        "stage": "generate_report",
        "description": "Generate CSV + PDF report",
        "task_type": TaskType.IO_CPU,
        "partition": "cpu",
        "depends_on": ["pattern_detect"],
    },
]


class PlannerAgent:
    """
    Planner Agent — Breaks workloads into executable subtasks.

    Responsibilities:
    - Decompose workload into chunks
    - Apply pipeline stages per chunk
    - Define dependencies and metadata
    - Classify task types (CPU/IO)
    """

    def __init__(self):
        self.agent_name = "planner"

    async def plan(self, workload: WorkloadRequest) -> list[Task]:
        """
        Decompose a workload request into a list of Task objects.
        Each chunk goes through the full pipeline.
        """
        logger.info(f"[Planner] Planning workload: {workload.name} ({workload.total_chunks} chunks)")

        tasks: list[Task] = []

        for chunk_idx in range(1, workload.total_chunks + 1):
            chunk_tasks = self._create_chunk_tasks(chunk_idx, workload)
            tasks.extend(chunk_tasks)

        # Add a final aggregation task that depends on all report tasks
        report_task_ids = [t.task_id for t in tasks if "generate_report" in t.task_id]
        aggregation = Task(
            task_id=f"task_aggregate_final",
            description="Aggregate all chunk reports into final output",
            task_type=TaskType.CPU,
            priority=workload.priority,
            dependencies=report_task_ids,
            partition="cpu",
            status=TaskStatus.CREATED,
        )
        tasks.append(aggregation)

        logger.info(f"[Planner] Created {len(tasks)} tasks across {workload.total_chunks} chunks")

        return tasks

    def _create_chunk_tasks(self, chunk_idx: int, workload: WorkloadRequest) -> list[Task]:
        """Create pipeline tasks for a single chunk."""
        chunk_tasks: list[Task] = []

        for stage in PIPELINE_STAGES:
            task_id = f"task_{stage['stage']}_chunk_{chunk_idx}"

            # Resolve dependencies — they reference tasks in the same chunk
            dependencies = []
            for dep_stage in stage["depends_on"]:
                dep_id = f"task_{dep_stage}_chunk_{chunk_idx}"
                dependencies.append(dep_id)

            task = Task(
                task_id=task_id,
                description=f"{stage['description']} (chunk {chunk_idx})",
                task_type=stage["task_type"],
                priority=workload.priority,
                dependencies=dependencies,
                partition=stage["partition"],
                status=TaskStatus.CREATED,
            )
            chunk_tasks.append(task)

        return chunk_tasks

    def get_plan_output(self, tasks: list[Task]) -> dict:
        """Format planner output per the spec."""
        return {
            "agent": self.agent_name,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "task_type": t.task_type.value,
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                    "partition": t.partition,
                }
                for t in tasks
            ],
        }
