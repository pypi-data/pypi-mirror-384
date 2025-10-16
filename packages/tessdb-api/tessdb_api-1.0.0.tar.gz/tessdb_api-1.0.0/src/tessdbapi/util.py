from typing import Any
import asyncio
import functools

# Typying Alias for all helper function in here
# The Session class is generated dynamically in SQL Alchemy
# and depends on the database URL

type Session = Any

def async_lru_cache(*lru_cache_args, **lru_cache_kwargs):
    """asyncio counterpart for lru_cache"""
    def decorator(async_function):
        @functools.lru_cache(*lru_cache_args, **lru_cache_kwargs)
        def cached_async_function(*args, **kwargs):
            coroutine = async_function(*args, **kwargs)
            return asyncio.ensure_future(coroutine)

        @functools.wraps(async_function)
        async def wrapper(*args, **kwargs):
            return await cached_async_function(*args, **kwargs)

        return wrapper

    return decorator
