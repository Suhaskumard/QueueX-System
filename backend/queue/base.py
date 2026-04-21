"""
QueueMind — Abstract Message Queue Interface
---------------------------------------------
Defines the contract that both InMemoryQueue and KafkaQueue must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional


class MessageQueue(ABC):
    """Abstract base class for the message queue system."""

    @abstractmethod
    async def start(self) -> None:
        """Initialize connections and start the queue system."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the queue system."""
        ...

    @abstractmethod
    async def produce(self, topic: str, message: dict, partition: Optional[int] = None) -> int:
        """
        Publish a message to a topic.
        Returns the offset of the published message.
        """
        ...

    @abstractmethod
    async def consume(self, topic: str, group_id: str = "default") -> AsyncGenerator[dict, None]:
        """
        Consume messages from a topic as an async generator.
        Messages are yielded one at a time.
        """
        ...

    @abstractmethod
    async def get_queue_depth(self, topic: str) -> int:
        """Return the number of pending messages in a topic."""
        ...

    @abstractmethod
    async def create_topic(self, topic: str, num_partitions: int = 4) -> None:
        """Create a topic with the specified number of partitions."""
        ...
