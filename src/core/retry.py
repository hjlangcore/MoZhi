import time
import functools
from typing import Callable, Any, Optional, List, Type
from loguru import logger
from src.core.exceptions import LLMConnectionError, LLMResponseError


class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_exceptions = retry_on_exceptions or [LLMConnectionError, LLMResponseError]


def exponential_backoff(attempt: int, initial_delay: float, max_delay: float, base: float) -> float:
    delay = min(initial_delay * (base ** attempt), max_delay)
    jitter = delay * 0.1 * (1 - 2 * (attempt % 2))
    return max(0, delay + jitter)


def with_retry(config: Optional[RetryConfig] = None):
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(config.retry_on_exceptions) as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = exponential_backoff(
                            attempt,
                            config.initial_delay,
                            config.max_delay,
                            config.exponential_base
                        )
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper
    return decorator


class RetryHandler:
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        wrapped_func = with_retry(self.config)(func)
        return wrapped_func(*args, **kwargs)

    def execute_async(self, func: Callable, *args, **kwargs):
        import asyncio

        async def async_wrapper():
            for attempt in range(self.config.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except tuple(self.config.retry_on_exceptions) as e:
                    if attempt < self.config.max_attempts - 1:
                        delay = exponential_backoff(
                            attempt,
                            self.config.initial_delay,
                            self.config.max_delay,
                            self.config.exponential_base
                        )
                        logger.warning(f"Async attempt {attempt + 1} failed: {e}. Retrying...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All async attempts failed for {func.__name__}")
                        raise

        return async_wrapper()
