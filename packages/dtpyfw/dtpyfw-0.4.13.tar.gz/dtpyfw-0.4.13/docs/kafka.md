# Kafka Sub-Package

**DealerTower Python Framework** — High‑level Kafka messaging utilities for standardized event production and consumption across microservices.

## Overview

The `kafka` sub-package provides:

* **Connection Management** with a fluent `KafkaConfig` builder and `KafkaInstance` factory.
* **Producer Class** (`Producer`) for sending JSON‑encoded messages and waiting for acknowledgment.
* **Consumer Class** (`Consumer`) for polling messages, registering per‑topic handlers, and manual offset commits.

This centralizes Kafka setup and workflows, reducing boilerplate and ensuring consistent patterns.

## Installation

Install the `kafka` extra to include necessary dependencies:

```bash
pip install dtpyfw[kafka]
```

## Configuration

### KafkaConfig

Fluent interface to set up Kafka connection parameters, including full URL or individual settings:

| Method                                      | Description                                                   |
| ------------------------------------------- | ------------------------------------------------------------- |
| `set_kafka_url(url: str)`                   | Full Kafka URL (overrides other servers), e.g. `kafka://...`. |
| `set_bootstrap_servers(servers: List[str])` | List of host\:port pairs, e.g. `['h1:9092','h2:9092']`.       |
| `set_security_protocol(proto: str)`         | SASL/SSL protocol, e.g. `SASL_PLAINTEXT` or `SSL`.            |
| `set_sasl_mechanism(mech: str)`             | SASL mechanism, e.g. `PLAIN`, `SCRAM-SHA-256`.                |
| `set_sasl_plain_username(user: str)`        | Username for SASL PLAIN authentication.                       |
| `set_sasl_plain_password(pwd: str)`         | Password for SASL PLAIN authentication.                       |
| `set_client_id(client_id: str)`             | Logical identifier for Kafka clients.                         |
| `set_group_id(group_id: str)`               | Consumer group identifier (for `Consumer`).                   |
| `set_auto_offset_reset(offset: str)`        | Where to start if no offset: `earliest` or `latest`.          |
| `set_enable_auto_commit(flag: bool)`        | Enable (`True`) or disable (`False`) auto offset commits.     |
| `get(key: str, default=None)`               | Retrieve a config value.                                      |

```python
from dtpyfw.kafka.config import KafkaConfig

config = (
    KafkaConfig()
    .set_kafka_url("kafka://user:pass@host1:9092,host2:9092")
    .set_auto_offset_reset("earliest")
    .set_enable_auto_commit(False)
)
```

## Connection Management

### KafkaInstance

Creates `KafkaProducer` and `KafkaConsumer` clients using the `KafkaConfig`:

```python
from dtpyfw.kafka.connection import KafkaInstance

kafka_instance = KafkaInstance(config)
```

**Context Managers:**

* `producer_context(**kwargs)` — yields a `KafkaProducer`, flushes and closes on exit.
* `consumer_context(topics: List[str], **kwargs)` — yields a `KafkaConsumer`, subscribes and closes on exit.

**Direct Clients:**

* `get_producer(**kwargs)` — raw `KafkaProducer` with JSON serialization.
* `get_consumer(topics: List[str], **kwargs)` — raw `KafkaConsumer` subscribed to topics.
Message values are JSON encoded when produced using these helpers.

```python
# Producing
with kafka_instance.producer_context() as producer:
    producer.send("events", {"type": "user.signup", "id": 42})

# Consuming
with kafka_instance.consumer_context(["events"], auto_offset_reset="earliest", enable_auto_commit=False) as consumer:
    for msg in consumer:
        print(msg.topic, msg.value)
```

## Producer

### `Producer`

High‑level wrapper for sending messages:

```python
from dtpyfw.kafka.producer import Producer

producer = Producer(kafka_instance)

# Send a message and wait for acknowledgment
producer.send(
    topic="events",
    value={"action": "order.created", "order_id": 1001},
    key=b"order-1001",
    timeout=10
)
```

**Key Methods:**

* `send(topic: str, value: Any, key: Optional[Any]=None, timeout: int=10)` — blocks until Kafka acknowledges or raises.

## Consumer

### `Consumer`

High‑level wrapper for polling and handling messages:

```python
from dtpyfw.kafka.consumer import Consumer

consumer = Consumer(
    kafka_instance,
    topics=["events"],
    auto_offset_reset="earliest",
    enable_auto_commit=False
)

# Register handler for topic
def handle_events(topic, partition, offset, key, value):
    print(f"Received {value} on {topic}")

consumer.register_handler("events", handle_events)

# Poll once (or loop for continuous)
consumer.consume(timeout_ms=1000)

# Manual offset commit (if auto_commit=False)
consumer.commit()
```

**Key Methods:**

* `register_handler(topic: str, handler: Callable)` — attach processing function.
* `consume(timeout_ms: int=1000)` — poll and dispatch to handlers, commits if configured.
* `commit()` — manually commit offsets when auto commit is disabled.

---

*This documentation covers the `kafka` sub‑package of the DealerTower Python Framework. Ensure the `kafka` extra is installed to use these features.*

