"""
Async message bus (in-process or ZeroMQ PUB/SUB).

Topic routing:
  "concept_target"       L1 → L2
  "physical_realization" L2 → L3
  "integration_feedback" L3 → L1
  "retarget_request"     L3 → L2
  "icvp_vote"            L1 ↔ L1

Usage (in-process mode)::

    bus = MessageBus()
    bus.subscribe("concept_target", my_handler)
    await bus.publish("concept_target", concept_target_msg)
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

Handler = Callable[[Any], Awaitable[None]]


class MessageBus:
    """
    Simple in-process pub/sub bus backed by asyncio queues.

    For ZeroMQ mode (multi-process), swap publish/subscribe with zmq.asyncio
    sockets; the interface is identical.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register an async handler for a topic."""
        self._subscribers[topic].append(handler)
        logger.debug("Subscribed %s to topic '%s'", handler.__qualname__, topic)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic] = [
            h for h in self._subscribers[topic] if h is not handler
        ]

    async def publish(self, topic: str, message: Any) -> None:
        """
        Deliver message to all subscribers.

        Handlers are called concurrently; individual failures are logged
        but do not prevent delivery to other subscribers.
        """
        handlers = list(self._subscribers.get(topic, []))
        if not handlers:
            logger.debug("No subscribers for topic '%s'", topic)
            return

        results = await asyncio.gather(
            *[h(message) for h in handlers],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Handler %s raised on topic '%s': %s",
                    handlers[i].__qualname__,
                    topic,
                    result,
                    exc_info=result,
                )

    # ------------------------------------------------------------------
    # Convenience: record / replay
    # ------------------------------------------------------------------

    def record(self, topic: str, store: list) -> None:
        """Subscribe a simple list accumulator — useful for tests & replay."""
        async def _record(msg: Any) -> None:
            store.append(msg)
        self.subscribe(topic, _record)


# Module-level singleton (overridable in tests)
_default_bus: MessageBus | None = None


def get_bus() -> MessageBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus


def reset_bus() -> None:
    """Reset the singleton — useful between tests."""
    global _default_bus
    _default_bus = None
