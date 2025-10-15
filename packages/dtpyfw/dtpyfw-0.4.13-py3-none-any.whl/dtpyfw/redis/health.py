from typing import Tuple

from .connection import RedisInstance

__all__ = ("is_redis_connected",)


def is_redis_connected(redis: RedisInstance) -> Tuple[bool, Exception | None]:
    try:
        return redis.get_redis_client().ping(), None
    except Exception as e:
        return False, e
