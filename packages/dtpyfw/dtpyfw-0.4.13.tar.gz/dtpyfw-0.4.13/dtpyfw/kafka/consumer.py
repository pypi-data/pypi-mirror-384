from typing import Any, Callable, Dict, List

from kafka import KafkaConsumer

from ..core.exception import exception_to_dict
from ..log import footprint
from .connection import KafkaInstance


class Consumer:
    """High-level Kafka consumer with per-topic handlers."""

    def __init__(
        self, kafka_instance: KafkaInstance, topics: List[str], **consumer_kwargs: Any
    ) -> None:
        # Create and subscribe consumer
        self._consumer: KafkaConsumer = kafka_instance.get_consumer(
            topics, **consumer_kwargs
        )
        self._handlers: Dict[str, List[Callable[..., None]]] = {}

    def register_handler(self, topic: str, handler: Callable[..., None]) -> "Consumer":
        """Attach a handler function for messages on a specific topic."""
        self._handlers.setdefault(topic, []).append(handler)
        return self

    def commit(self) -> None:
        """Public method to commit the current offsets to Kafka.

        Call this after successfully processing messages when auto-
        commit is disabled.
        """
        controller = f"{__name__}.Consumer.commit"
        try:
            self._consumer.commit()
        except Exception as e:
            footprint.leave(
                log_type="error",
                message="Error during commit()",
                controller=controller,
                subject="Commit Error",
                payload={
                    "error": exception_to_dict(e),
                },
            )
            raise

    def consume(self, timeout_ms: int = 1000) -> None:
        """Poll for messages and dispatch to handlers.

        If auto_commit is disabled, commits after handling.
        """
        controller = f"{__name__}.Consumer.consume"
        try:
            records = self._consumer.poll(timeout_ms=timeout_ms)
            for tp_records in records.values():
                for msg in tp_records:
                    for handler in self._handlers.get(msg.topic, []):
                        try:
                            handler(
                                topic=msg.topic,
                                partition=msg.partition,
                                offset=msg.offset,
                                key=msg.key,
                                value=msg.value,
                            )
                        except Exception as e:
                            footprint.leave(
                                log_type="error",
                                message=f"Handler {handler.__name__} failed for topic {msg.topic}",
                                controller=controller,
                                subject="Handler failed",
                                payload={
                                    "error": exception_to_dict(e),
                                },
                            )

            # Commit manually if needed
            if not self._consumer.config.get("enable_auto_commit", True):
                self._consumer.commit()
        except Exception as e:
            footprint.leave(
                log_type="error",
                message="Error during consume()",
                controller=controller,
                subject="Consumer Error",
                payload={
                    "error": exception_to_dict(e),
                },
            )
