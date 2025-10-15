from typing import Any


class KafkaConfig:
    """Builder for Kafka settings, supporting a full URL or individual
    params."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}

    def set_kafka_url(self, url: str) -> "KafkaConfig":
        """Provide a full Kafka URL, e.g.
        kafka://user:pass@host1:9092,host2:9092."""
        self._config["kafka_url"] = url
        return self

    def set_bootstrap_servers(self, servers: list[str]) -> "KafkaConfig":
        self._config["bootstrap_servers"] = servers
        return self

    # ... other setters unchanged ...
    def set_security_protocol(self, protocol: str) -> "KafkaConfig":
        self._config["security_protocol"] = protocol
        return self

    def set_sasl_mechanism(self, mechanism: str) -> "KafkaConfig":
        self._config["sasl_mechanism"] = mechanism
        return self

    def set_sasl_plain_username(self, username: str) -> "KafkaConfig":
        self._config["sasl_plain_username"] = username
        return self

    def set_sasl_plain_password(self, password: str) -> "KafkaConfig":
        self._config["sasl_plain_password"] = password
        return self

    def set_client_id(self, client_id: str) -> "KafkaConfig":
        self._config["client_id"] = client_id
        return self

    def set_group_id(self, group_id: str) -> "KafkaConfig":
        self._config["group_id"] = group_id
        return self

    def set_auto_offset_reset(self, offset: str) -> "KafkaConfig":
        self._config["auto_offset_reset"] = offset
        return self

    def set_enable_auto_commit(self, flag: bool) -> "KafkaConfig":
        self._config["enable_auto_commit"] = flag
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
