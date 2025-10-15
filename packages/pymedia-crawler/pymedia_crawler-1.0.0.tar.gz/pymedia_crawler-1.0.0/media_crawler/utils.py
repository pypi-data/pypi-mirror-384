"""
Retry and utility functions for the crawler application.
"""
import time
import random
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps


logger = logging.getLogger(__name__)

T = TypeVar('T')


def exponential_backoff_sleep(attempt: int, base: int = 2) -> None:
    """
    Sleep with exponential backoff.
    
    Args:
        attempt: Current attempt number (1-indexed)
        base: Base for exponential calculation
    """
    sleep_time = (base ** attempt) + random.uniform(0, 1)
    logger.debug(f"Retry sleeping for {sleep_time:.1f}s (attempt {attempt})")
    time.sleep(sleep_time)


def retry(
    max_attempts: int = 3,
    backoff_base: int = 2,
    exceptions: tuple = (Exception,),
    on_failure: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        on_failure: Optional callback function to call on failure
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt}/{max_attempts}: {e}"
                    )
                    if attempt < max_attempts:
                        exponential_backoff_sleep(attempt, backoff_base)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts"
                        )
                        if on_failure:
                            on_failure(e)
                        return None
            return None
        return wrapper
    return decorator


def url_to_filename(url: str) -> str:
    """
    Convert URL to a safe filename.
    
    Args:
        url: URL string
        
    Returns:
        Safe filename string
    """
    return (url.replace('https://', '')
               .replace('http://', '')
               .replace('/', '_')
               .replace('?', '_')
               .replace('&', '_')
               .replace('=', '_')
               .replace(':', '_'))
