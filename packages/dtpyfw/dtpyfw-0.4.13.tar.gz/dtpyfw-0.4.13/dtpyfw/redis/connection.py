import urllib.parse
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

import redis
from redis.asyncio import Redis as AsyncRedis

from .config import RedisConfig

__all__ = ("RedisInstance",)


class RedisInstance:

    def __init__(self, redis_config: RedisConfig):
        self.config = redis_config
        self.redis_url = self._set_redis_url()

    def _set_redis_url(self) -> str:
        """Constructs the Redis connection URL."""
        redis_url = self.config.get("redis_url")
        if redis_url:
            return redis_url

        redis_ssl = self.config.get("redis_ssl", False)
        redis_host = self.config.get("redis_host")
        redis_port = self.config.get("redis_port")
        redis_db = self.config.get("redis_db")
        redis_username = self.config.get("redis_username", "")
        redis_password = self.config.get("redis_password", "")

        username = urllib.parse.quote(redis_username) if redis_username else ""
        password = urllib.parse.quote(redis_password) if redis_password else ""

        auth_part = (
            f"{username}:{password}@"
            if username and password
            else f"{password}@" if password else f"{username}@" if username else ""
        )
        protocol = "rediss" if redis_ssl else "redis"

        return f"{protocol}://{auth_part}{redis_host}:{redis_port}/{redis_db}"

    def get_redis_url(self) -> str:
        return self.redis_url

    def get_redis_client(self) -> redis.Redis:
        return redis.Redis.from_url(self.redis_url)

    async def get_async_redis_client(self) -> AsyncRedis:
        return AsyncRedis.from_url(self.redis_url)

    @contextmanager
    def get_redis(self) -> Generator[redis.Redis, None, None]:
        """Context manager for synchronous Redis client."""
        redis_client = self.get_redis_client()
        try:
            yield redis_client
        finally:
            redis_client.close()

    @asynccontextmanager
    async def get_async_redis(self) -> AsyncGenerator[AsyncRedis, None]:
        """Async context manager for Redis client."""
        async_redis_client = await self.get_async_redis_client()
        try:
            yield async_redis_client
        finally:
            await async_redis_client.aclose()
