"""
QueueMind — FastAPI Orchestrator
==================================
Main entry point for the distributed task queue system.
Manages the full task lifecycle: Plan → Schedule → Execute → Validate → Monitor.
"""

import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.task import Task, TaskStatus, WorkloadRequest
from queue.memory_queue import InMemoryQueue
from store.task_store import TaskStore
from websocket.manager import ConnectionManager
from agents.planner import PlannerAgent
from agents.scheduler import SchedulerAgent
from agents.load_balancer import LoadBalancerAgent
from agents.worker_agent import WorkerExecutionAgent
from agents.retry_agent import RetryAgent
from agents.critic import CriticAgent
from agents.monitor import MonitorAgent

# ── Logging Setup ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-25s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("queuemind.main")

# ── Global Instances ────────────────────────────────────────────────

queue = InMemoryQueue()
store = TaskStore()
ws_manager = ConnectionManager()

planner = PlannerAgent()
scheduler = SchedulerAgent(queue, store)
load_balancer = LoadBalancerAgent(store)
worker_agent = WorkerExecutionAgent()
retry_agent = RetryAgent(store)
critic = CriticAgent(store)
monitor = MonitorAgent(store, ws_manager)

# Active background tasks
_background_tasks: set[asyncio.Task] = set()
_metrics_task: asyncio.Task | None = None
_processing_lock = asyncio.Lock()


# ── Task Processing Pipeline ───────────────────────────────────────

async def process_single_task(task: Task) -> None:
    """Process a single task through the full pipeline."""
    try:
        # 1. Load Balancer — assign worker
        assignment = await load_balancer.assign_worker(task)
        if not assignment:
            await monitor.emit("worker_unavailable", task.task_id, level="warn",
                             details={"reason": "no available worker"})
            # Re-queue after delay
            await asyncio.sleep(1)
            assignment = await load_balancer.assign_worker(task)
            if not assignment:
                await monitor.emit("task_deferred", task.task_id, level="warn")
                return

        worker_id = assignment["assigned_worker"]

        await monitor.emit("task_assigned", task.task_id, worker_id,
                          details={"load": assignment["worker_load"]})
        await monitor.emit_task_update(task.task_id, "assigned")

        # 2. Worker — execute task
        await store.update_task(task.task_id, status=TaskStatus.RUNNING)
        await monitor.emit("task_started", task.task_id, worker_id)
        await monitor.emit_task_update(task.task_id, "running")

        result = await worker_agent.execute(task, worker_id)

        # 3. Handle result
        if result.status == "failed":
            # Release worker
            await load_balancer.release_worker(worker_id, success=False)

            await store.update_task(task.task_id,
                                   status=TaskStatus.FAILED,
                                   execution_time=result.execution_time,
                                   error_message=result.error)

            await monitor.emit("task_failed", task.task_id, worker_id,
                             details={"error": result.error},
                             level="error")
            await monitor.emit_task_update(task.task_id, "failed")

            # 4. Retry Agent — handle failure
            retry_result = await retry_agent.handle_failure(task, result)

            await monitor.emit("retry_decision", task.task_id,
                             details=retry_result, level="warn")

            # Broadcast retry event
            await ws_manager.broadcast("retry_event", retry_result)

            if retry_result["action"] == "retry":
                # Wait for retry delay
                delay_str = retry_result["next_retry_delay"]
                delay = float(delay_str.replace("s", ""))
                await asyncio.sleep(delay)

                # Re-fetch task (it's been updated by retry agent)
                updated_task = await store.get_task(task.task_id)
                if updated_task:
                    # Re-process
                    bg_task = asyncio.create_task(process_single_task(updated_task))
                    _background_tasks.add(bg_task)
                    bg_task.add_done_callback(_background_tasks.discard)
        else:
            # Success
            await load_balancer.release_worker(worker_id, success=True)

            await store.update_task(task.task_id,
                                   status=TaskStatus.COMPLETED,
                                   execution_time=result.execution_time,
                                   result=result.result)

            await store.add_execution_record({
                "task_id": task.task_id,
                "worker_id": worker_id,
                "execution_time": result.execution_time,
                "status": "completed",
            })

            await monitor.emit("task_completed", task.task_id, worker_id,
                             details={"time": f"{result.execution_time}s"},
                             level="success")
            await monitor.emit_task_update(task.task_id, "completed")

            # 5. Critic — validate result
            validation = await critic.validate(task, result)

            await monitor.emit("task_validated" if validation["valid"] else "validation_failed",
                             task.task_id,
                             details={"score": validation["quality_score"]},
                             level="success" if validation["valid"] else "warn")
            await monitor.emit_task_update(task.task_id, task.status.value)

            # 6. Try to schedule dependent tasks
            await scheduler.retry_pending()

            # Check if the scheduler released new tasks
            # Process any newly queued tasks
            await _check_and_process_queued_tasks()

    except Exception as e:
        logger.error(f"[Pipeline] Error processing {task.task_id}: {e}", exc_info=True)
        await monitor.emit("pipeline_error", task.task_id,
                         details={"error": str(e)}, level="error")


async def _check_and_process_queued_tasks() -> None:
    """Check for newly queued tasks and process them."""
    queued_tasks = await store.get_tasks_by_status(TaskStatus.QUEUED)
    for task in queued_tasks:
        # Only process if not already being processed
        bg_task = asyncio.create_task(process_single_task(task))
        _background_tasks.add(bg_task)
        bg_task.add_done_callback(_background_tasks.discard)


async def run_workload(workload: WorkloadRequest) -> dict:
    """Execute a complete workload through the pipeline."""
    logger.info(f"╔══════════════════════════════════════════════════╗")
    logger.info(f"║  QueueMind — Processing: {workload.name:<24}║")
    logger.info(f"╚══════════════════════════════════════════════════╝")

    await monitor.emit("workload_received",
                      details={"name": workload.name, "chunks": workload.total_chunks})

    # 1. Plan
    await monitor.emit("planning_started", details={"workload": workload.name})
    tasks = await planner.plan(workload)

    # Store all tasks
    for task in tasks:
        await store.add_task(task)

    plan_output = planner.get_plan_output(tasks)
    await monitor.emit("planning_complete",
                      details={"task_count": len(tasks)},
                      level="success")

    # Broadcast all tasks to dashboard
    for task in tasks:
        await monitor.emit_task_update(task.task_id, "created")

    # 2. Schedule (only tasks with no dependencies go first)
    await monitor.emit("scheduling_started")
    schedule_results = await scheduler.schedule(tasks)
    await monitor.emit("scheduling_complete",
                      details={
                          "queued": len(schedule_results),
                          "pending": scheduler.pending_count,
                      },
                      level="success")

    # 3. Process queued tasks
    queued_tasks = await store.get_tasks_by_status(TaskStatus.QUEUED)
    for task in queued_tasks:
        bg_task = asyncio.create_task(process_single_task(task))
        _background_tasks.add(bg_task)
        bg_task.add_done_callback(_background_tasks.discard)

    return plan_output


# ── Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _metrics_task

    logger.info("=" * 60)
    logger.info("  QueueMind — Distributed Task Queue System")
    logger.info(f"  Mode: {settings.MODE.upper()}")
    logger.info(f"  Workers: {settings.NUM_CPU_WORKERS} CPU + {settings.NUM_IO_WORKERS} IO")
    logger.info(f"  Failure Rate: {settings.WORKER_FAILURE_RATE * 100:.0f}%")
    logger.info("=" * 60)

    # Start queue
    await queue.start()
    await queue.create_topic(settings.TOPIC_QUEUE_CPU)
    await queue.create_topic(settings.TOPIC_QUEUE_IO)
    await queue.create_topic(settings.TOPIC_RESULTS)
    await queue.create_topic(settings.TOPIC_FAILURES)
    await queue.create_topic(settings.TOPIC_MONITORING)

    # Register workers
    await load_balancer.register_workers(settings.NUM_CPU_WORKERS, settings.NUM_IO_WORKERS)

    # Start metrics loop
    _metrics_task = asyncio.create_task(monitor.start_metrics_loop(1.0))

    logger.info("✓ QueueMind is ready")

    yield

    # Shutdown
    logger.info("Shutting down QueueMind...")
    await monitor.stop()
    if _metrics_task:
        _metrics_task.cancel()
    for bg_task in _background_tasks:
        bg_task.cancel()
    await queue.stop()
    logger.info("QueueMind shut down cleanly")


# ── FastAPI App ─────────────────────────────────────────────────────

app = FastAPI(
    title="QueueMind",
    description="Production-Grade Distributed Task Queue System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ──────────────────────────────────────────────────

@app.post("/api/workloads")
async def submit_workload(workload: WorkloadRequest):
    """Submit a new workload for processing."""
    result = await run_workload(workload)
    return {"status": "accepted", "plan": result}


@app.post("/api/demo")
async def run_demo():
    """Trigger a pre-built demo workload."""
    workload = WorkloadRequest(
        name="Log Processing Pipeline",
        description="Process 1GB system logs: extract IPs, deduplicate, classify, check blacklists, geolocate, detect patterns, generate reports",
        total_chunks=3,
        priority=5,
    )
    result = await run_workload(workload)
    return {"status": "demo_started", "plan": result}


@app.get("/api/tasks")
async def list_tasks(status: str = None):
    """List all tasks, optionally filtered by status."""
    if status:
        try:
            task_status = TaskStatus(status)
            tasks = await store.get_tasks_by_status(task_status)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    else:
        tasks = await store.get_all_tasks()

    return {
        "count": len(tasks),
        "tasks": [t.model_dump() for t in tasks],
    }


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get detailed info for a specific task."""
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task {task_id} not found")
    return task.model_dump()


@app.get("/api/workers")
async def list_workers():
    """Get all worker statuses."""
    workers = await store.get_all_workers()
    return {
        "count": len(workers),
        "workers": [w.model_dump() for w in workers],
    }


@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics."""
    summary = await store.get_summary()
    status_counts = await store.get_tasks_by_status_counts()
    history = await store.get_metrics_history()

    return {
        "summary": summary.model_dump(),
        "status_counts": status_counts,
        "metrics_history": [m.model_dump() for m in history[-60:]],
    }


@app.get("/api/summary")
async def get_summary():
    """Get final system summary."""
    return (await store.get_summary()).model_dump()


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    """Get recent monitoring events."""
    return {"logs": monitor.get_recent_events(limit)}


@app.get("/api/failures")
async def get_failures():
    """Get failure logs."""
    logs = await store.get_failure_logs()
    return {"count": len(logs), "failures": logs}


# ── WebSocket Endpoint ──────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # Send initial state
    tasks = await store.get_all_tasks()
    workers = await store.get_all_workers()
    summary = await store.get_summary()

    await ws_manager.send_personal(websocket, "initial_state", {
        "tasks": [t.model_dump(mode="json") for t in tasks],
        "workers": [w.model_dump(mode="json") for w in workers],
        "summary": summary.model_dump(),
    })

    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            # Client can send commands if needed
            logger.debug(f"[WS] Received: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ── Entry Point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
