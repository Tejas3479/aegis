import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar, ParamSpec, Awaitable

T = TypeVar("T")
P = ParamSpec("P")

logger = logging.getLogger("aegis_enterprise.resilience")

class CircuitBreaker:
    """
    Enterprise circuit breaker to prevent cascading failures in external AI/DB services.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def __call__(self, func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF-OPEN state.")
                else:
                    logger.warning(f"Circuit breaker for {func.__name__} is OPEN. Blocking request.")
                    raise Exception(f"Circuit Breaker for {func.__name__} is currently OPEN due to previous failures.")

            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                    logger.info(f"Circuit breaker for {func.__name__} recovered to CLOSED state.")
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.critical(f"Circuit breaker for {func.__name__} tripped to OPEN state after {self.failures} failures.")
                raise e
        return wrapper

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    """
    Decorator for exponential backoff retries on transient failures.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            x = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f"Function {func.__name__} failed after {retries} retries.")
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x)
                    logger.warning(f"Retrying {func.__name__} in {sleep}s... (Attempt {x+1}/{retries})")
                    await asyncio.sleep(sleep)
                    x += 1
        return wrapper
    return decorator
