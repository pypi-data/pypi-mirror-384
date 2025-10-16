import asyncio
import random
import logging
import uuid
from typing import Callable, Any, Tuple, Optional


# --- Logger Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("RetryFunction")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for tracing."""
    return str(uuid.uuid4())


def log_info(message: str, extra: Optional[dict] = None):
    logger.info(f"{message} | {extra or {}}")


def log_warning(message: str, extra: Optional[dict] = None):
    logger.warning(f"{message} | {extra or {}}")


def log_error(message: str, extra: Optional[dict] = None):
    logger.error(f"{message} | {extra or {}}")


def log_exceptions(func):
    """Decorator to log exceptions in async functions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_error(f"Unhandled exception in {func.__name__}: {e}")
            raise
    return wrapper


@log_exceptions
async def execute_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: int = 1,
    timeout: Optional[int] = None,
    **kwargs,
) -> Tuple[Optional[Any], Optional[Exception]]:
    """
    Execute an async function with retries, exponential backoff, and jitter.

    Args:
        func: Async function to execute.
        *args: Positional arguments for the function.
        max_retries: Number of retry attempts.
        base_delay: Initial delay before retrying.
        timeout: Optional timeout (seconds).
        **kwargs: Keyword arguments for the function.

    Returns:
        Tuple(result, None) if successful.
        Tuple(None, Exception) if failed after all retries.
    """
    correlation_id = generate_correlation_id()
    log_info("Retry Function initiated.", {"correlation_id": correlation_id})

    for attempt in range(max_retries):
        try:
            # Execute with or without timeout
            if timeout:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = await func(*args, **kwargs)

            if attempt > 0:
                log_info(
                    f"Success on retry attempt {attempt + 1}/{max_retries}",
                    {"attempts": attempt + 1, "retries": max_retries, "correlation_id": correlation_id}
                )
            return result, None

        except asyncio.TimeoutError as e:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            log_warning(
                f"Timeout on attempt {attempt + 1}/{max_retries}. Retrying in {delay:.1f}s",
                {"attempts": attempt + 1, "retries": max_retries, "delay": delay, "correlation_id": correlation_id}
            )
            if attempt == max_retries - 1:
                log_error("Final timeout after all retries.", {"correlation_id": correlation_id})
                return None, e
            await asyncio.sleep(delay)

        except Exception as e:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            log_error(
                f"Error on attempt {attempt + 1}/{max_retries}: {e}",
                {"attempts": attempt + 1, "retries": max_retries, "delay": delay, "correlation_id": correlation_id}
            )
            if attempt == max_retries - 1:
                log_error("Max retries reached. Aborting.", {"correlation_id": correlation_id})
                return None, e
            await asyncio.sleep(delay)

    return None, Exception("Failed after maximum retries.")
