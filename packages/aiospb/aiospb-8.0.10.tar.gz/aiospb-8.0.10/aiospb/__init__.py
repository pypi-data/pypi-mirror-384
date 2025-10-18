import asyncio
import logging
import random
from functools import wraps

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def exponential_retry(
    max_retries=3, base_delay=1, backoff_factor=2, jitter=True, exceptions=(Exception,)
):
    """
    Decorator for exponential backoff retry.

    :param max_retries: Max number of retry attempts (total calls = max_retries + 1)
    :param base_delay: Initial delay in seconds
    :param backoff_factor: Multiplier for each retry (e.g., 2 doubles the delay)
    :param jitter: Add random variation to avoid synchronized retries
    :param exceptions: Tuple of exceptions to catch and retry on
    """

    def decorator(coro):
        @wraps(coro)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await coro(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise last_exception
                    # Calculate delay: base * (factor ^ attempt) + jitter
                    delay = base_delay * (backoff_factor**attempt)
                    if jitter:
                        delay += random.uniform(0, base_delay)  # Simple jitter
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e.__class__.__name__} -> {e}. Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
            return None  # Fallback, though we raise above

        return wrapper

    return decorator
