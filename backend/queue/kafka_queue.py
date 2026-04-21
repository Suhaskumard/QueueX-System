"""
QueueMind — Kafka Queue Implementation
----------------------------------------
Production-mode queue using aiokafka.
Only used when MODE=prod (requires a running Kafka broker).
Dev mode uses InMemoryQueue from memory_queue.py instead.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from queue.base import MessageQueue

logger = logging.getLogger("queuemind.kafka")

try:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from aiokafka.errors import KafkaConnectionError
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    logger.warning("[KafkaQueue] aiokafka not installed. Run: pip install aiokafka")


class KafkaQueue(MessageQueue):
    """
    Production Kafka queue using aiokafka.

    Implements the same interface as InMemoryQueue so the rest of the
    system needs zero changes when switching MODE=prod.

    Topics created automatically on first produce/consume call.
    Consumer groups are respected for load-balanced consumption.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        if not AIOKAFKA_AVAILABLE:
            raise ImportError("aiokafka is required for Kafka mode. pip install aiokafka")

        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumers: dict[str, AIOKafkaConsumer] = {}
        self._running = False

    # ── Lifecycle ───────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the Kafka producer."""
        logger.info(f"[KafkaQueue] Connecting to {self.bootstrap_servers}")
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            enable_idempotence=True,
            compression_type="lz4",
        )
        await self._producer.start()
        self._running = True
        logger.info("[KafkaQueue] Producer ready")

    async def stop(self) -> None:
        """Gracefully stop producer and all consumers."""
        self._running = False
        if self._producer:
            await self._producer.stop()
        for consumer in self._consumers.values():
            await consumer.stop()
        logger.info("[KafkaQueue] Stopped")

    async def create_topic(self, topic: str, partitions: int = 4) -> None:
        """
        Topics are created automatically by Kafka when first produced to
        (if auto.create.topics.enable=true on the broker, which is default).
        This method is a no-op in Kafka mode — here for interface compatibility.
        """
        logger.debug(f"[KafkaQueue] Topic '{topic}' will be auto-created on first use")

    # ── Produce ─────────────────────────────────────────────────────

    async def produce(
        self,
        topic: str,
        message: dict,
        partition: Optional[int] = None,
        key: Optional[str] = None,
    ) -> None:
        """Publish a message to a Kafka topic."""
        if not self._producer:
            raise RuntimeError("KafkaQueue not started. Call start() first.")

        await self._producer.send_and_wait(
            topic,
            value=message,
            key=key,
            partition=partition,
        )
        logger.debug(f"[KafkaQueue] Produced → {topic} (partition={partition})")

    # ── Consume ─────────────────────────────────────────────────────

    async def consume(
        self,
        topic: str,
        group_id: str = "queuemind-workers",
        timeout_ms: int = 1000,
    ) -> AsyncGenerator[dict, None]:
        """
        Async generator that yields messages from a Kafka topic.
        Each call with the same group_id shares the consumer group offset,
        enabling load-balanced consumption across multiple workers.
        """
        consumer_key = f"{topic}:{group_id}"

        if consumer_key not in self._consumers:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                max_poll_records=10,
            )
            await consumer.start()
            self._consumers[consumer_key] = consumer
            logger.info(f"[KafkaQueue] Consumer ready: {consumer_key}")

        consumer = self._consumers[consumer_key]

        while self._running:
            try:
                records = await asyncio.wait_for(
                    consumer.getmany(timeout_ms=timeout_ms),
                    timeout=timeout_ms / 1000 + 1,
                )
                for tp, messages in records.items():
                    for msg in messages:
                        yield msg.value
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[KafkaQueue] Consumer error: {e}")
                await asyncio.sleep(1)

    # ── Utils ────────────────────────────────────────────────────────

    async def get_topic_offsets(self, topic: str) -> dict:
        """Return current end offsets for all partitions of a topic."""
        if not self._producer:
            return {}
        from aiokafka import TopicPartition
        partitions = self._producer.partitions_for(topic)
        if not partitions:
            return {}
        tps = {TopicPartition(topic, p) for p in partitions}
        offsets = await self._producer.end_offsets(tps)
        return {tp.partition: offset for tp, offset in offsets.items()}
