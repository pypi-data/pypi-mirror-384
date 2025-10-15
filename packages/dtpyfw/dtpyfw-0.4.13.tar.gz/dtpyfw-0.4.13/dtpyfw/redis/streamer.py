import json
import os
import re
import socket
import time
import uuid
from dataclasses import dataclass
from collections import defaultdict
from typing import Callable, DefaultDict, Dict, List, Optional, Tuple

from redis.exceptions import ResponseError

from ..core.exception import exception_to_dict
from ..core.retry import retry_wrapper
from ..log import footprint
from .connection import RedisInstance

__all__ = (
    "RedisStreamer",
    "Message",
)


@dataclass
class Message:
    name: str
    body: Dict

    def get_json_encoded(self):
        return {"name": self.name, "body": json.dumps(self.body, default=str)}


class RedisStreamer:
    """
    Redis Streams consumer with:
      - Decoupled fan-out across microservices (one group per service).
      - Bounded at-most-once (per group) via a ZSET de-dup window.
      - Channel ownership & time-based cleanup (only the owner trims).

    Back-compat:
      ctor(consumer_name=...) -> 'consumer_name' is treated as the listener (group) name.
      A unique per-process consumer instance name is auto-generated.
    """

    # -------------------- ctor & state --------------------

    def __init__(
        self,
        redis_instance: RedisInstance,
        consumer_name: str,                    # legacy; used as listener (group) name
        dedup_window_ms: Optional[int] = None, # at-most-once window (default 7d)
        owner_ttl_ms: int = 60_000,            # ownership key TTL; if owner dies, others can take over
        owner_heartbeat_ms: int = 15_000,      # how often to refresh ownership TTL
        cleanup_interval_ms: int = 30_000,     # how often to attempt cleanup per owned channel
    ):
        self.listener_name: str = self._sanitize(consumer_name, maxlen=128)
        self.consumer_instance_name: str = self._gen_consumer_name()  # used as Redis consumername

        self._redis_instance = redis_instance
        self._redis_client = self._redis_instance.get_redis_client()

        # Channel retention (if set) enables trimming; ownership controls who trims
        self._channel_retention: Dict[str, Optional[int]] = {}

        # Local subscriptions for this process: (channel, listener_name, group_name, read_messages)
        self._subscriptions: List[Tuple[str, str, str, bool]] = []

        # Handlers per (channel, listener_name)
        self._handlers: DefaultDict[Tuple[str, str], List[Callable]] = defaultdict(list)

        # De-dup window (ms) for ZSET ledger (bounds memory + redelivery horizon)
        self._dedup_window_ms: int = dedup_window_ms if (dedup_window_ms and dedup_window_ms > 0) else 7 * 24 * 60 * 60 * 1000

        # Ownership & cleanup cadence
        self._owner_ttl_ms = max(5_000, owner_ttl_ms)
        self._owner_heartbeat_ms = max(1_000, owner_heartbeat_ms)
        self._cleanup_interval_ms = max(5_000, cleanup_interval_ms)

        # Internal timestamps for cadence control
        self._last_owner_hb_ms: Dict[str, int] = {}      # channel -> last heartbeat time
        self._last_cleanup_run_ms: Dict[str, int] = {}   # channel -> last cleanup time

    @staticmethod
    def _sanitize(s: str, maxlen: int) -> str:
        s = re.sub(r"[^a-zA-Z0-9._:-]+", "-", s or "")
        return s[:maxlen]

    def _gen_consumer_name(self) -> str:
        host = os.getenv("POD_NAME") or os.getenv("HOSTNAME") or socket.gethostname()
        pid = os.getpid()
        rnd = uuid.uuid4().hex[:8]
        name = ".".join([self.listener_name, self._sanitize(host, 64), str(pid), rnd])
        return self._sanitize(name, maxlen=200)

    def _server_now_ms(self) -> int:
        sec, usec = self._redis_client.time()
        return sec * 1000 + (usec // 1000)

    def _consumer_group_exists(self, channel_name: str, consumer_group: str) -> bool:
        try:
            groups = self._redis_client.xinfo_groups(channel_name)
            return any(group["name"].decode("utf-8") == consumer_group for group in groups)
        except Exception:
            return False

    @staticmethod
    def _group_name(channel: str, listener_name: str) -> str:
        return f"{channel}:{listener_name}:cg"

    @staticmethod
    def _processed_zset_key(channel: str, group: str) -> str:
        return f"stream:{channel}:group:{group}:processed"

    @staticmethod
    def _dlq_stream(channel: str) -> str:
        return f"{channel}:dlq"

    @staticmethod
    def _owner_key(channel: str) -> str:
        return f"stream:{channel}:owner"


    def register_channel(
        self,
        channel_name: str,
        retention_ms: Optional[int] = None,
    ):
        """
        Register channel metadata. If retention_ms is provided, this instance will try to
        become the channel OWNER and will clean up messages after retention_ms.
        Ownership is cooperative: the owner key has a TTL and is renewed periodically.
        When it expires (process down), another registrant can acquire ownership.
        """
        self._channel_retention[channel_name] = retention_ms
        if retention_ms and retention_ms > 0:
            self._try_acquire_ownership(channel_name)  # attempt immediately
        return self

    @retry_wrapper()
    def send_message(self, channel: str, message: Message):
        self._redis_client.xadd(channel, message.get_json_encoded())

    def _i_am_owner(self, channel: str) -> bool:
        try:
            v = self._redis_client.get(self._owner_key(channel))
            if not v:
                return False
            if isinstance(v, bytes):
                v = v.decode("utf-8", errors="ignore")
            return v == self.consumer_instance_name
        except Exception:
            return False

    def _try_acquire_ownership(self, channel: str) -> bool:
        """
        Attempt to acquire channel ownership using SET NX PX.
        """
        key = self._owner_key(channel)
        try:
            ok = self._redis_client.set(key, self.consumer_instance_name, nx=True, px=self._owner_ttl_ms)
            if ok:
                footprint.leave(
                    log_type="info",
                    subject="Channel ownership acquired",
                    controller=f"{__name__}.Consumer._try_acquire_ownership",
                    message=f"Now owner of channel '{channel}'",
                    payload={"channel": channel, "owner": self.consumer_instance_name, "ttl_ms": self._owner_ttl_ms},
                )
                # seed cadence
                now = self._server_now_ms()
                self._last_owner_hb_ms[channel] = now
                self._last_cleanup_run_ms.setdefault(channel, 0)
                return True
            return False
        except Exception as e:
            footprint.leave(
                log_type="error",
                subject="Channel ownership acquire error",
                controller=f"{__name__}.Consumer._try_acquire_ownership",
                message=f"Failed to acquire ownership for '{channel}'",
                payload={"channel": channel, "error": exception_to_dict(e)},
            )
            return False

    def _refresh_ownership(self, channel: str):
        """
        Refresh ownership TTL only if we are the owner.
        """
        key = self._owner_key(channel)
        try:
            if self._i_am_owner(channel):
                # Renew TTL
                self._redis_client.pexpire(key, self._owner_ttl_ms)
                self._last_owner_hb_ms[channel] = self._server_now_ms()
        except Exception as e:
            footprint.leave(
                log_type="error",
                subject="Channel ownership heartbeat error",
                controller=f"{__name__}.Consumer._refresh_ownership",
                message=f"Failed to refresh ownership for '{channel}'",
                payload={"channel": channel, "error": exception_to_dict(e)},
            )

    # -------------------- subscriptions & handlers --------------------

    def subscribe(
        self,
        channel_name: str,
        read_messages: bool = True,
        start_from_latest: bool = True,
    ):
        """
        Subscribe this process (identified by self.listener_name) to a channel.
        Creates/uses consumer group = f"{channel}:{self.listener_name}:cg".
        """
        controller = f"{__name__}.Consumer.subscribe"
        listener_name = self.listener_name
        group = self._group_name(channel_name, listener_name)

        if not self._consumer_group_exists(channel_name, group):
            try:
                start_id = "$" if start_from_latest else "0-0"
                self._redis_client.xgroup_create(channel_name, group, start_id, mkstream=True)
            except Exception as e:
                footprint.leave(
                    log_type="error",
                    subject="Error creating consumer group",
                    message=f"Error creating consumer group {group} for channel {channel_name}.",
                    controller=controller,
                    payload=exception_to_dict(e),
                )

        self._subscriptions.append((channel_name, listener_name, group, read_messages))
        return self

    def register_handler(self, channel_name: str, handler_func: Callable, listener_name: Optional[str] = None):
        listener = listener_name or self.listener_name
        self._handlers[(channel_name, listener)].append(handler_func)
        return self

    def _reserve_once(self, processed_key: str, message_id: str, now_ms: int) -> bool:
        try:
            added = self._redis_client.zadd(processed_key, {message_id: now_ms}, nx=True)
            return added == 1
        except Exception as e:
            footprint.leave(
                log_type="error",
                subject="Dedup error",
                controller=f"{__name__}.Consumer._reserve_once",
                message="ZADD NX failed; skipping message to avoid duplicate processing.",
                payload={"error": exception_to_dict(e), "message_id": message_id, "key": processed_key},
            )
            return False

    def _dead_letter(self, channel: str, reason: str, message_id: str, extra: Dict):
        """
        Log bad/failed messages instead of pushing to a DLQ stream.
        The caller is responsible for XACK to prevent re-delivery loops.
        """
        try:
            payload = {"reason": reason, "channel": channel, "message_id": message_id}
            if extra:
                payload.update(extra)
            footprint.leave(
                log_type="error",
                subject="Message failed",
                controller=f"{__name__}.Consumer._dead_letter",
                message=f"Message failure on channel '{channel}' (reason={reason})",
                payload=payload,
            )
        except Exception as e:
            # Last-resort logging if footprint itself throws
            footprint.leave(
                log_type="error",
                subject="Dead-letter logging error",
                controller=f"{__name__}.Consumer._dead_letter",
                message="Failed to log message failure",
                payload={"error": exception_to_dict(e), "channel": channel, "reason": reason, "message_id": message_id},
            )

    def _ack(self, channel: str, group: str, message_id: str):
        try:
            acked = self._redis_client.xack(channel, group, message_id)
            if acked == 0:
                footprint.leave(
                    log_type="info",
                    subject="Ack no-op",
                    controller=f"{__name__}.Consumer._ack",
                    message="XACK returned 0 (already acked or not pending).",
                    payload={"channel": channel, "group": group, "message_id": message_id},
                )
        except Exception as e:
            footprint.leave(
                log_type="error",
                subject="Ack error",
                controller=f"{__name__}.Consumer._ack",
                message="XACK failed.",
                payload={"error": exception_to_dict(e), "channel": channel, "group": group, "message_id": message_id},
            )

    @retry_wrapper()
    def _consume_one(self, channel: str, consumer_group: str, listener_name: str, block_time: float, count: int = 32):
        controller = f"{__name__}.Consumer._consume_one"
        try:
            msgs = self._redis_client.xreadgroup(
                groupname=consumer_group,
                consumername=self.consumer_instance_name,
                streams={channel: ">"},
                block=int(block_time * 1000),
                count=count,
            )
            if not msgs:
                return

            _, batch = msgs[0]
            processed_key = self._processed_zset_key(channel, consumer_group)

            for message_id, fields in batch:
                now_ms = self._server_now_ms()

                # At-most-once (within window): reserve the ID
                if not self._reserve_once(processed_key, message_id, now_ms):
                    self._ack(channel, consumer_group, message_id)
                    continue

                # Decode + schema guard
                try:
                    raw_name = fields.get(b"name")
                    raw_body = fields.get(b"body")
                    if raw_name is None or raw_body is None:
                        raise ValueError("Missing required fields 'name' or 'body'.")
                    name = raw_name.decode("utf-8") if isinstance(raw_name, bytes) else raw_name
                    body = json.loads(raw_body.decode("utf-8")) if isinstance(raw_body, bytes) else raw_body
                except Exception as e:
                    raw_dump = {
                        (k.decode() if isinstance(k, bytes) else k):
                        (v.decode() if isinstance(v, bytes) else v)
                        for k, v in (fields or {}).items()
                    }
                    self._dead_letter(
                        channel,
                        reason="decode/schema",
                        message_id=message_id,
                        extra={"listener": listener_name, "error": json.dumps(exception_to_dict(e)), "raw": json.dumps(raw_dump, default=str)},
                    )
                    self._ack(channel, consumer_group, message_id)
                    continue

                # Dispatch to handlers
                handler_failed = False
                for handler in self._handlers.get((channel, listener_name), []):
                    try:
                        handler(name=name, payload=body)
                    except Exception as e:
                        handler_failed = True
                        self._dead_letter(
                            channel,
                            reason="handler",
                            message_id=message_id,
                            extra={
                                "listener": listener_name,
                                "handler": handler.__name__,
                                "error": json.dumps(exception_to_dict(e)),
                                "name": name,
                                "payload": json.dumps(body, default=str),
                            },
                        )
                        self._ack(channel, consumer_group, message_id)
                        break

                if not handler_failed:
                    self._ack(channel, consumer_group, message_id)

        except Exception as e:
            if "NOGROUP" in str(e):
                try:
                    self.subscribe(channel_name=channel)
                except ResponseError as inner_e:
                    if "BUSYGROUP" not in str(inner_e):
                        footprint.leave(
                            log_type="error",
                            controller=controller,
                            subject="Creating missing consumer group Error",
                            message="Error creating missing consumer group",
                            payload={
                                "error": exception_to_dict(inner_e),
                                "group": consumer_group,
                                "listener": listener_name
                            },
                        )

            footprint.leave(
                log_type="error",
                message=f"Error consuming messages from channel {channel}",
                controller=controller,
                subject="Consuming Messages Error",
                payload={"error": exception_to_dict(e), "group": consumer_group, "listener": listener_name},
            )

    def consume_once(self, block_time: float = 5.0, count: int = 32):
        for channel, listener, group, read in self._subscriptions:
            if read:
                self._consume_one(channel, group, listener, block_time, count)

    def persist_consume(self, rest_time: float = 0.1, block_time: float = 5.0, count: int = 32):
        controller = f"{__name__}.Consumer.persist_consume"
        # One-time snapshot
        for channel, listener, group, read in self._subscriptions:
            footprint.leave(
                log_type="info",
                message="Subscription configuration",
                controller=controller,
                subject="Persist consuming listeners",
                payload={"channel": channel, "listener": listener, "group": group, "will_read_messages": bool(read)},
            )

        while True:
            self.consume_once(block_time=block_time, count=count)
            # Maintenance cadence
            self._ownership_heartbeat_and_cleanup()
            self.maintain_ledgers()
            if rest_time > 0:
                time.sleep(rest_time)

    def _ownership_heartbeat_and_cleanup(self):
        """
        For each channel with retention, ensure an owner exists:
          - Try to acquire if no owner.
          - If we are the owner, refresh TTL periodically and run cleanup on cadence.
        """
        now = self._server_now_ms()
        for channel, retention_ms in self._channel_retention.items():
            if not retention_ms or retention_ms <= 0:
                continue

            # Try to acquire if no owner
            if not self._i_am_owner(channel):
                # If key missing or owned by someone else whose TTL may expire soon, a SET NX will only work when vacant
                self._try_acquire_ownership(channel)
                # If still not owner, skip to next channel
                if not self._i_am_owner(channel):
                    continue

            # Refresh ownership TTL on cadence
            last_hb = self._last_owner_hb_ms.get(channel, 0)
            if now - last_hb >= self._owner_heartbeat_ms:
                self._refresh_ownership(channel)

            # Cleanup on cadence
            last_run = self._last_cleanup_run_ms.get(channel, 0)
            if now - last_run >= self._cleanup_interval_ms:
                self._run_time_based_cleanup(channel, retention_ms)
                self._last_cleanup_run_ms[channel] = now

    @retry_wrapper()
    def _run_time_based_cleanup(self, channel_name: str, retention_ms: int):
        """
        Trim entries older than retention using XTRIM MINID (approximate).
        WARNING: XTRIM MINID removes entries regardless of PEL; pick a retention
                 that exceeds worst-case consumer lag.
        """
        controller = f"{__name__}.Consumer._run_time_based_cleanup"
        if not self._i_am_owner(channel_name):
            return
        try:
            now_ms = self._server_now_ms()
            cutoff = now_ms - retention_ms
            removed = self._redis_client.xtrim(channel_name, minid=f"{cutoff}-0", approximate=True)
            if removed:
                footprint.leave(
                    log_type="info",
                    message=f"Trimmed {removed} entries older than {retention_ms}ms in {channel_name}.",
                    controller=controller,
                    subject="Time-based stream trimming",
                    payload={"channel": channel_name, "cutoff_ms": cutoff, "retention_ms": retention_ms},
                )
        except Exception as e:
            footprint.leave(
                log_type="error",
                message=f"Error cleaning up messages in channel {channel_name}",
                controller=controller,
                subject="Cleaning up messages Error",
                payload={"channel": channel_name, "error": exception_to_dict(e)},
            )

    # -------------------- maintenance: dedup ledgers --------------------

    @retry_wrapper()
    def maintain_ledgers(self):
        """
        Purge old de-dup reservations from ZSETs so memory stays bounded.
        One ZREMRANGEBYSCORE per subscription.
        """
        controller = f"{__name__}.Consumer.maintain_ledgers"
        now_ms = self._server_now_ms()
        cutoff = now_ms - self._dedup_window_ms

        for channel_name, _, consumer_group, _ in self._subscriptions:
            key = self._processed_zset_key(channel_name, consumer_group)
            try:
                removed = self._redis_client.zremrangebyscore(key, min="-inf", max=f"({cutoff}")
                if removed:
                    footprint.leave(
                        log_type="info",
                        message=f"Purged {removed} dedup entries older than {self._dedup_window_ms}ms",
                        controller=controller,
                        subject="Dedup ledger maintenance",
                        payload={"key": key, "cutoff_ms": cutoff, "removed": removed},
                    )
            except Exception as e:
                footprint.leave(
                    log_type="error",
                    message="Error purging dedup ledger",
                    controller=controller,
                    subject="Dedup maintenance error",
                    payload={"key": key, "error": exception_to_dict(e)},
                )
