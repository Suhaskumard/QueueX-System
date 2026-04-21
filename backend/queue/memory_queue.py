"""
QueueMind — In-Memory Message Queue
------------------------------------
Async in-memory queue that simulates Kafka semantics for dev mode.
Supports topics, partitions, consumer groups, and offsets.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Optional
from collections import defaultdict

from .base import MessageQueue

logger = logging.getLogger("queuemind.queue")


class InMemoryQueue(MessageQueue):
    """
    In-memory message queue simulating Kafka behavior.
    Uses asyncio.Queue per topic-partition for async message passing.
    """

    def __init__(self, default_partitions: int = 4):
        self._default_partitions = default_partitions
        # topic -> partition_id -> asyncio.Queue
        self._queues: dict[str, dict[int, asyncio.Queue]] = {}
        # topic -> partition_id -> current offset
        self._offsets: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        # topic -> total messages produced
        self._total_produced: dict[str, int] = defaultdict(int)
        # topic -> number of partitions
        self._topic_partitions: dict[str, int] = {}
        # consumer group -> topic -> next partition to consume (round-robin)
        self._consumer_rr: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._running = True
        logger.info("[InMemoryQueue] Started")

    async def stop(self) -> None:
        self._running = False
        logger.info("[InMemoryQueue] Stopped")

    async def create_topic(self, topic: str, num_partitions: int = 4) -> None:
        async with self._lock:
            if topic not in self._queues:
                self._queues[topic] = {}
                self._topic_partitions[topic] = num_partitions
                for p in range(num_partitions):
                    self._queues[topic][p] = asyncio.Queue()
                logger.info(f"[InMemoryQueue] Created topic '{topic}' with {num_partitions} partitions")

    async def produce(self, topic: str, message: dict, partition: Optional[int] = None) -> int:
        if topic not in self._queues:
            await self.create_topic(topic, self._default_partitions)

        num_partitions = self._topic_partitions[topic]

        if partition is None:
            # Round-robin partition assignment
            partition = self._total_produced[topic] % num_partitions

        partition = partition % num_partitions
        offset = self._offsets[topic][partition]
        self._offsets[topic][partition] += 1
        self._total_produced[topic] += 1

        envelope = {
            "offset": offset,
            "partition": partition,
            "topic": topic,
            "value": message,
        }

        await self._queues[topic][partition].put(envelope)
        logger.debug(f"[InMemoryQueue] Produced to {topic}[{partition}] offset={offset}")
        return offset

    async def consume(self, topic: str, group_id: str = "default") -> AsyncGenerator[dict, None]:
        if topic not in self._queues:
            await self.create_topic(topic, self._default_partitions)

        while self._running:
            # Round-robin across partitions
            num_partitions = self._topic_partitions[topic]
            consumed = False

            for _ in range(num_partitions):
                p = self._consumer_rr[group_id][topic] % num_partitions
                self._consumer_rr[group_id][topic] = (p + 1)

                queue = self._queues[topic][p]
                try:
                    envelope = queue.get_nowait()
                    consumed = True
                    yield envelope["value"]
                except asyncio.QueueEmpty:
                    continue

            if not consumed:
                # No messages available, wait briefly
                await asyncio.sleep(0.1)

    async def get_queue_depth(self, topic: str) -> int:
        if topic not in self._queues:
            return 0
        total = 0
        for p_queue in self._queues[topic].values():
            total += p_queue.qsize()
        return total

    async def get_all_depths(self) -> dict[str, int]:
        """Return queue depth for all topics."""
        depths = {}
        for topic in self._queues:
            depths[topic] = await self.get_queue_depth(topic)
        return depths
