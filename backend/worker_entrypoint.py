"""
QueueMind — Standalone Worker Entrypoint
-----------------------------------------
Used in Docker/production mode to run workers as isolated containers.
In dev mode, workers are spawned as asyncio tasks inside main.py.

Usage:
    python worker_entrypoint.py --type cpu --id worker_cpu_1
    python worker_entrypoint.py --type io  --id worker_io_1
"""

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from queue.kafka_queue import KafkaQueue
from agents.worker_agent import WorkerExecutionAgent
from models.task import Task
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger("queuemind.worker_entrypoint")


async def run_worker(worker_type: str, worker_id: str):
    """Pull tasks from Kafka and execute them in a loop."""
    logger.info(f"[Worker:{worker_id}] Starting ({worker_type.upper()} type)")

    queue = KafkaQueue(settings.KAFKA_BOOTSTRAP_SERVERS)
    await queue.start()

    agent = WorkerExecutionAgent()

    topic = settings.TOPIC_QUEUE_CPU if worker_type == "cpu" else settings.TOPIC_QUEUE_IO
    group_id = f"workers-{worker_type}"

    logger.info(f"[Worker:{worker_id}] Consuming from '{topic}' (group={group_id})")

    async for message in queue.consume(topic, group_id=group_id):
        try:
            task = Task(**message)
            logger.info(f"[Worker:{worker_id}] Received task: {task.task_id}")

            result = await agent.execute(task, worker_id)

            # Publish result back to results topic
            result_topic = settings.TOPIC_RESULTS if result.status == "completed" else settings.TOPIC_FAILURES
            await queue.produce(result_topic, result.model_dump())

            logger.info(f"[Worker:{worker_id}] Task {task.task_id} → {result.status}")

        except Exception as e:
            logger.error(f"[Worker:{worker_id}] Error processing message: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="QueueMind Worker")
    parser.add_argument("--type", choices=["cpu", "io"], default="cpu", help="Worker type")
    parser.add_argument("--id",   type=str,              default=None,  help="Worker ID override")
    args = parser.parse_args()

    worker_id = args.id or f"worker_{args.type}_docker"

    try:
        asyncio.run(run_worker(args.type, worker_id))
    except KeyboardInterrupt:
        logger.info(f"[Worker:{worker_id}] Stopped")


if __name__ == "__main__":
    main()
