import asyncio
import inspect
import time
from functools import wraps
from typing import Awaitable, Callable

from ..log import footprint
from .exception import exception_to_dict
from .jsonable_encoder import jsonable_encoder

__all__ = (
    "retry_async",
    "retry",
    "retry_wrapper",
)


async def retry_async(
    func: Awaitable,
    *args,
    sleep_time: int | float = 2,
    max_attempts: int | float = 3,
    backoff: int | float = 2,
    exceptions=(Exception,),
    log_tries: bool = False,
    **kwargs,
):
    """Retry an async ``func`` with exponential backoff."""
    controller = f"{__name__}.retry_async"
    delay = sleep_time
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            error_dict = exception_to_dict(e)
            error_dict["kwargs"] = jsonable_encoder(kwargs)
            error_dict["args"] = jsonable_encoder(args)
            if attempt == max_attempts:
                footprint.leave(
                    log_type="error",
                    message=f"We could not finish the current job in the function {func.__name__}.",
                    controller=controller,
                    subject=f"Error at {func.__name__}",
                    payload=error_dict,
                )
                raise e
            elif log_tries:
                footprint.leave(
                    log_type="warning",
                    message=f"An error happened while we retry to run {func.__name__} at the {attempt} attempt{'s' if attempt > 1 else ''}.",
                    controller=controller,
                    subject=f"Warning at retrying {func.__name__}",
                    payload=error_dict,
                )
            await asyncio.sleep(delay)
            delay *= backoff


def retry(
    func: Callable,
    *args,
    sleep_time: int | float = 2,
    max_attempts: int | float = 3,
    backoff: int | float = 2,
    exceptions=(Exception,),
    log_tries: bool = False,
    **kwargs,
):
    """Retry a synchronous callable using the same semantics as
    ``retry_async``."""
    controller = f"{__name__}.retry"
    if inspect.iscoroutinefunction(func):
        return retry_async(
            func,
            *args,
            sleep_time=sleep_time,
            max_attempts=max_attempts,
            backoff=backoff,
            exceptions=exceptions,
            **kwargs,
        )

    delay = sleep_time
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            error_dict = exception_to_dict(e)
            error_dict["kwargs"] = jsonable_encoder(kwargs)
            error_dict["args"] = jsonable_encoder(args)
            if attempt == max_attempts:
                footprint.leave(
                    log_type="error",
                    message=f"We could not finish the current job in the function {func.__name__}.",
                    controller=controller,
                    subject=f"Error at {func.__name__}",
                    payload=error_dict,
                )
                raise e
            elif log_tries:
                footprint.leave(
                    log_type="warning",
                    message=f"An error happened while we retry to run {func.__name__} at the {attempt} attempt{'s' if attempt > 1 else ''}.",
                    controller=controller,
                    subject=f"Warning at retrying {func.__name__}",
                    payload=error_dict,
                )
            time.sleep(delay)
            delay *= backoff


def retry_wrapper(
    max_attempts: int | float = 3,
    sleep_time: int | float = 2,
    backoff: int | float = 2,
    exceptions=(Exception,),
    log_tries: bool = False,
):
    """Decorator form of :func:`retry` supporting async and sync callables."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_async(
                func,
                *args,
                max_attempts=max_attempts,
                sleep_time=sleep_time,
                backoff=backoff,
                exceptions=exceptions,
                log_tries=log_tries,
                **kwargs,
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry(
                func,
                *args,
                max_attempts=max_attempts,
                sleep_time=sleep_time,
                backoff=backoff,
                exceptions=exceptions,
                log_tries=log_tries,
                **kwargs,
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
