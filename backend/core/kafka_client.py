import asyncio
import json
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

class ForensicEventBus:
    """Event bus with support for Kafka and in-memory async queues for offline forensic workstations."""
    def __init__(self):
        self._in_memory_queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self.is_kafka = False

    def _get_queue(self, topic: str) -> asyncio.Queue:
        if topic not in self._in_memory_queues:
            self._in_memory_queues[topic] = asyncio.Queue()
        return self._in_memory_queues[topic]

    async def publish(self, topic: str, message: dict):
        """Publish an event to the trace topic."""
        logger.info(f"[EventBus] Publishing to '{topic}': {message.get('event_type', 'event')}")
        q = self._get_queue(topic)
        await q.put(message)

        # Notify direct subscribers if registered
        for callback in self._subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(message))
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error executing event subscriber for '{topic}': {e}")

    async def consume(self, topic: str) -> dict:
        """Consume the next event from the queue."""
        q = self._get_queue(topic)
        return await q.get()

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

event_bus = ForensicEventBus()
