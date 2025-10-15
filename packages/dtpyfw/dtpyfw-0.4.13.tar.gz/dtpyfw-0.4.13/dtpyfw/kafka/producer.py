from typing import Any

from kafka import KafkaProducer

from ..core.exception import exception_to_dict
from ..log import footprint
from .connection import KafkaInstance


class Producer:
    """High-level Kafka producer wrapper."""

    def __init__(self, kafka_instance: KafkaInstance) -> None:
        self._producer: KafkaProducer = kafka_instance.get_producer()

    def send(
        self, topic: str, value: Any, key: str | bytes | None = None, timeout: int = 10
    ) -> None:
        """Send a message to Kafka, waiting up to `timeout` seconds for
        confirmation."""
        controller = f"{__name__}.Producer.send"
        if not isinstance(topic, str) or not topic:
            raise ValueError("`topic` must be a non-empty string")

        encoded_key: bytes | None
        if isinstance(key, str):
            encoded_key = key.encode("utf-8")
        else:
            encoded_key = key

        try:
            future = self._producer.send(topic, key=encoded_key, value=value)
            future.get(timeout=timeout)
            footprint.leave(
                log_type="info",
                message=f"Message {key} has been sent to {topic}",
                controller=controller,
                subject="Message sent",
            )
        except Exception as e:
            footprint.leave(
                log_type="error",
                message=f"Failed to send message to topic {topic}",
                controller=controller,
                subject="Producer Error",
                payload={
                    "error": exception_to_dict(e),
                },
            )
