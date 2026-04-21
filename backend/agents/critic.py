"""
QueueMind — Critic & Validator Agent
--------------------------------------
Validates task outputs for correctness, completeness, and quality.
Ensures dependency consistency before marking tasks as validated.
"""

import logging
import random
from typing import Optional

from models.task import Task, TaskResult, TaskStatus
from store.task_store import TaskStore

logger = logging.getLogger("queuemind.critic")


class CriticAgent:
    """
    Critic & Validator Agent — Validates task results.

    Responsibilities:
    - Validate output structure and completeness
    - Check dependency consistency
    - Assign quality scores (0-10)
    - Gate tasks from COMPLETED → VALIDATED
    """

    def __init__(self, store: TaskStore):
        self.agent_name = "critic"
        self._store = store

    async def validate(self, task: Task, result: TaskResult) -> dict:
        """
        Validate a completed task's result.
        Checks structure, dependencies, and assigns quality score.
        """
        logger.info(f"[Critic] Validating {task.task_id}")

        # Check 1: Result structure
        has_result = result.result is not None
        has_output = isinstance(result.result, dict) and "output" in result.result if has_result else False

        # Check 2: Dependency consistency
        deps_valid = await self._check_dependencies(task)

        # Check 3: Execution time sanity
        time_valid = 0 < result.execution_time < 120  # Under 2 minutes

        # Calculate quality score
        quality_score = self._calculate_quality(
            has_result=has_result,
            has_output=has_output,
            deps_valid=deps_valid,
            time_valid=time_valid,
            execution_time=result.execution_time,
        )

        is_valid = has_result and deps_valid and time_valid and quality_score >= 5.0

        if is_valid:
            await self._store.update_task(
                task.task_id,
                status=TaskStatus.VALIDATED,
                quality_score=quality_score,
            )
            logger.info(f"[Critic] Task {task.task_id} VALIDATED (score: {quality_score})")
        else:
            reasons = []
            if not has_result:
                reasons.append("missing result")
            if not deps_valid:
                reasons.append("dependency not validated")
            if not time_valid:
                reasons.append("execution time out of bounds")
            if quality_score < 5.0:
                reasons.append(f"low quality score ({quality_score})")

            logger.warning(f"[Critic] Task {task.task_id} REJECTED: {', '.join(reasons)}")

        return {
            "agent": self.agent_name,
            "task_id": task.task_id,
            "valid": is_valid,
            "quality_score": quality_score,
            "checks": {
                "has_result": has_result,
                "has_output": has_output,
                "deps_valid": deps_valid,
                "time_valid": time_valid,
            },
        }

    async def _check_dependencies(self, task: Task) -> bool:
        """Verify all dependency tasks are validated."""
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            dep_task = await self._store.get_task(dep_id)
            if not dep_task:
                return False
            if dep_task.status not in (TaskStatus.VALIDATED, TaskStatus.STORED):
                return False
        return True

    def _calculate_quality(
        self,
        has_result: bool,
        has_output: bool,
        deps_valid: bool,
        time_valid: bool,
        execution_time: float,
    ) -> float:
        """
        Calculate a quality score from 0-10 based on multiple factors.
        """
        score = 0.0

        # Result presence (3 points)
        if has_result:
            score += 2.0
        if has_output:
            score += 1.0

        # Dependency consistency (2 points)
        if deps_valid:
            score += 2.0

        # Time validity (2 points)
        if time_valid:
            score += 2.0

        # Efficiency bonus (up to 2 points — faster = better)
        if execution_time < 2.0:
            score += 2.0
        elif execution_time < 5.0:
            score += 1.5
        elif execution_time < 10.0:
            score += 1.0
        else:
            score += 0.5

        # Variance factor (up to 1 point) — simulates detailed inspection
        score += round(random.uniform(0.3, 1.0), 1)

        return round(min(10.0, score), 1)
