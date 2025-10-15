from contextlib import contextmanager

from kafka import KafkaConsumer, KafkaProducer

from ..core.exception import exception_to_dict
from ..log import footprint
from .config import KafkaConfig


class KafkaInstance:
    """Creates KafkaProducer/Consumer, respecting a single URL or individual
    settings."""

    def __init__(self, config: KafkaConfig) -> None:
        self._config = config
        self._base: dict = self._build_base_config()

    def _build_base_config(self) -> dict:
        # If a full URL is provided, use it directly
        kafka_url = self._config.get("kafka_url")
        if kafka_url:
            return {"bootstrap_servers": [kafka_url]}

        # Otherwise build from individual params
        servers = self._config.get("bootstrap_servers")
        if not servers:
            raise ValueError("Either kafka_url or bootstrap_servers must be configured")
        base = {"bootstrap_servers": servers}

        for key in (
            "security_protocol",
            "sasl_mechanism",
            "sasl_plain_username",
            "sasl_plain_password",
            "client_id",
        ):
            value = self._config.get(key)
            if value:
                base[key] = value

        return base

    def get_producer(self, **kwargs) -> KafkaProducer:
        """Return a KafkaProducer that JSON-encodes messages."""
        controller = f"{__name__}.KafkaInstance.get_producer"
        try:
            return KafkaProducer(
                **self._base,
                value_serializer=lambda v: __import__("json").dumps(v).encode(),
                **kwargs,
            )
        except Exception as e:
            footprint.leave(
                log_type="error",
                message="Error creating KafkaProducer",
                controller=controller,
                subject="Kafka Producer",
                payload={
                    "error": exception_to_dict(e),
                },
            )
            raise

    def get_consumer(self, topics: list[str], **kwargs) -> KafkaConsumer:
        """Return a KafkaConsumer subscribed to given topics."""
        controller = f"{__name__}.KafkaInstance.get_consumer"
        try:
            consumer_config = {
                **self._base,
                "group_id": self._config.get("group_id"),
                "auto_offset_reset": self._config.get("auto_offset_reset", "latest"),
                "enable_auto_commit": self._config.get("enable_auto_commit", True),
                **kwargs,
            }
            consumer = KafkaConsumer(**consumer_config)
            consumer.subscribe(topics)
            return consumer
        except Exception as e:
            footprint.leave(
                log_type="error",
                message="Error creating KafkaConsumer",
                controller=controller,
                subject="Kafka Consumer",
                payload={
                    "error": exception_to_dict(e),
                },
            )
            raise

    @contextmanager
    def producer_context(self, **kwargs):
        prod = self.get_producer(**kwargs)
        try:
            yield prod
        finally:
            prod.flush()
            prod.close()

    @contextmanager
    def consumer_context(self, topics: list[str], **kwargs):
        cons = self.get_consumer(topics, **kwargs)
        try:
            yield cons
        finally:
            cons.close()
