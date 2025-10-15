import hashlib
import json
import zlib
from functools import wraps
from typing import Any, Callable, Dict, List, Set

from redis import Redis

from ..core.exception import exception_to_dict
from ..core.jsonable_encoder import jsonable_encoder
from ..log import footprint
from .connection import RedisInstance

__all__ = (
    "cache_data",
    "cache_function",
    "cache_wrapper",
)


def cache_data(
    response: Dict,
    cache_key: str,
    redis_instance: Redis,
    expire: int | None = None
):
    controller = f"{__name__}.cache_data"
    try:
        compressed_main_value = zlib.compress(
            json.dumps(jsonable_encoder(response)).encode("utf-8")
        )
        redis_instance.delete(cache_key)
        if expire:
            redis_instance.setex(
                name=cache_key, value=compressed_main_value, time=expire
            )
        else:
            redis_instance.set(name=cache_key, value=compressed_main_value)

    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="We faced an error while we want to cache data.",
            controller=controller,
            subject="Error on caching data",
            payload={
                "expire": expire,
                "cache_key": cache_key,
                "error": exception_to_dict(exception),
            },
        )

    return response


def _cache_key_generator(
    namespace: str,
    args: tuple,
    kwargs: Dict[str, Any],
    skip_cache_keys: Set[str],
):
    kwargs_key = {k: v for k, v in kwargs.items() if k not in skip_cache_keys}
    cache_key = ""
    if namespace:
        cache_key += f"{namespace}:"
    if args:
        args_hash = hashlib.sha256(
            json.dumps(args, default=str).encode("utf-8")
        ).hexdigest()
        cache_key += f"{args_hash}:"
    if kwargs_key:
        kwargs_hash = hashlib.sha256(
            json.dumps(kwargs_key, default=str).encode("utf-8")
        ).hexdigest()
        cache_key += f"{kwargs_hash}:"

    return cache_key.rstrip(":")


def _should_cache(cache_only_for: List[Dict[str, Any]] | None, kwargs: Dict[str, Any]) -> bool:
    if cache_only_for is None:
        return True
    for cond in cache_only_for:
        col = cond.get("kwarg")
        if cond.get("operator") == "in" and kwargs.get(col) in cond.get("value"):
            return True
    return False


def _decode_cached_value(cache_compressed: bytes, controller: str):
    try:
        return json.loads(zlib.decompress(cache_compressed).decode("utf-8"))
    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="Error during decompressing or loading cached data.",
            controller=controller,
            subject="Error on reading cache",
            payload={"error": exception_to_dict(exception)},
        )
        return None


def _encode_result(result: Any) -> bytes:
    return zlib.compress(json.dumps(jsonable_encoder(result)).encode("utf-8"))


def _redis_get_sync(redis_client, key: str, controller: str):
    try:
        return redis_client.get(key)
    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="Error while trying to retrieve data from cache.",
            controller=controller,
            subject="Error on get cached data",
            payload={"redis_key": key, "error": exception_to_dict(exception)},
        )
        return None


async def _redis_get_async(redis_client, key: str, controller: str):
    try:
        return await asyncio.to_thread(redis_client.get, key)
    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="Error while trying to retrieve data from cache.",
            controller=controller,
            subject="Error on get cached data",
            payload={"redis_key": key, "error": exception_to_dict(exception)},
        )
        return None


def _redis_write_sync(redis_client, key: str, value: bytes, expire: int | None, controller: str):
    try:
        redis_client.delete(key)
        if expire:
            redis_client.setex(name=key, time=expire, value=value)
        else:
            redis_client.set(name=key, value=value)
    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="Error occurred while caching the result.",
            controller=controller,
            subject="Error on writing cache",
            payload={"redis_key": key, "error": exception_to_dict(exception)},
        )


async def _redis_write_async(redis_client, key: str, value: bytes, expire: int | None, controller: str):
    try:
        await asyncio.to_thread(redis_client.delete, key)
        if expire:
            # redis-py setex signature: setex(name, time, value)
            await asyncio.to_thread(redis_client.setex, key, expire, value)
        else:
            await asyncio.to_thread(redis_client.set, key, value)
    except Exception as exception:
        footprint.leave(
            log_type="error",
            message="Error occurred while caching the result.",
            controller=controller,
            subject="Error on writing cache",
            payload={"redis_key": key, "error": exception_to_dict(exception)},
        )


def cache_function(
    func: Callable,
    redis: "RedisInstance",
    namespace: str,
    expire: int | None = None,
    cache_only_for: List[Dict[str, Any]] = None,
    skip_cache_keys: Set[str] = None,
    *args,
    **kwargs,
):
    """
    Sync cache wrapper; uses sync Redis I/O.
    """
    controller = f"{__name__}.cache_function"
    if skip_cache_keys is None:
        skip_cache_keys = set()

    if not _should_cache(cache_only_for, kwargs):
        return func(*args, **kwargs)

    cache_key = _cache_key_generator(namespace, args, kwargs, skip_cache_keys)

    with redis.get_redis_client() as redis_instance:
        cache_compressed = _redis_get_sync(redis_instance, cache_key, controller)
        if cache_compressed:
            cached = _decode_cached_value(cache_compressed, controller)
            if cached is not None:
                return cached

        # Miss → compute
        result = func(*args, **kwargs)

        # Write
        _redis_write_sync(
            redis_instance,
            cache_key,
            _encode_result(result),
            expire,
            controller,
        )
        return result


async def acache_function(
    func: Callable,
    redis: "RedisInstance",
    namespace: str,
    expire: int | None = None,
    cache_only_for: List[Dict[str, Any]] = None,
    skip_cache_keys: Set[str] = None,
    *args,
    **kwargs,
):
    """
    Async cache wrapper; Redis remains sync but I/O is offloaded via asyncio.to_thread.
    """
    controller = f"{__name__}.acache_function"
    if skip_cache_keys is None:
        skip_cache_keys = set()

    if not _should_cache(cache_only_for, kwargs):
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    cache_key = _cache_key_generator(namespace, args, kwargs, skip_cache_keys)

    with redis.get_redis_client() as redis_instance:
        cache_compressed = await _redis_get_async(redis_instance, cache_key, controller)
        if cache_compressed:
            cached = _decode_cached_value(cache_compressed, controller)
            if cached is not None:
                return cached

        # Miss → compute
        if inspect.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        # Write
        await _redis_write_async(
            redis_instance,
            cache_key,
            _encode_result(result),
            expire,
            controller,
        )
        return result


def cache_wrapper(
    redis: "RedisInstance",
    namespace: str,
    expire: int | None = None,
    cache_only_for: List[Dict[str, Any]] = None,
    skip_cache_keys: Set[str] = None,
):
    """
    Unified decorator selecting sync/async path with shared helpers.
    """
    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def awrapper(*args, **kwargs):
                return await acache_function(
                    func=func,
                    redis=redis,
                    namespace=namespace,
                    expire=expire,
                    cache_only_for=cache_only_for,
                    skip_cache_keys=skip_cache_keys,
                    *args,
                    **kwargs,
                )
            return awrapper
        else:
            @wraps(func)
            def swrapper(*args, **kwargs):
                return cache_function(
                    func=func,
                    redis=redis,
                    namespace=namespace,
                    expire=expire,
                    cache_only_for=cache_only_for,
                    skip_cache_keys=skip_cache_keys,
                    *args,
                    **kwargs,
                )
            return swrapper
    return decorator
