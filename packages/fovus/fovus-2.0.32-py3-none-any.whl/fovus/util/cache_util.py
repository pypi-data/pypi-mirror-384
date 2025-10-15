import functools
import json
import os
import time
from typing import Any, Callable

from fovus.constants.cli_constants import PATH_TO_CACHE

# Default settings
DEFAULT_TTL = 600  # seconds
os.makedirs(PATH_TO_CACHE, exist_ok=True)


def _make_cache_key(args, kwargs):
    """
    Normalize args/kwargs into a JSON-safe cache key.

    Skips 'self' (first arg).
    """
    relevant_args = args[1:] if len(args) > 0 else args
    try:
        return json.dumps({"args": relevant_args, "kwargs": kwargs}, sort_keys=True, default=str)
    except TypeError:
        # fallback if something is not serializable
        return str({"args": relevant_args, "kwargs": kwargs})


def cache_result(cache_key: str, ttl: int = DEFAULT_TTL, persistent: bool = True):
    """
    Cache decorator for API methods.

    cache_key (str): Unique identifier for the cache (e.g., API name).
    ttl (int): Cache expiration time in seconds.
    persistent (bool): Whether to store cache on disk or keep in memory only.
    """

    def decorator(func: Callable):
        cache_file = os.path.join(PATH_TO_CACHE, f"{cache_key}.json")
        memory_cache: dict[str, tuple[Any, float]] = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal memory_cache

            key = _make_cache_key(args, kwargs)

            # --- In-memory cache ---
            if key in memory_cache:
                data, ts = memory_cache[key]
                if time.time() - ts < ttl:
                    return data

            # --- Persistent cache ---
            if persistent and os.path.exists(cache_file):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache = json.load(f)
                    if key in cache and time.time() - cache[key]["timestamp"] < ttl:
                        return cache[key]["data"]
                except (json.JSONDecodeError, OSError, KeyError):
                    # Ignore corrupted or unreadable cache
                    pass

            # --- Call API if not cached ---
            data = func(*args, **kwargs)

            # Save to memory cache
            memory_cache[key] = (data, time.time())

            # Save to file cache
            if persistent:
                cache = {}
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, encoding="utf-8") as f:
                            cache = json.load(f)
                    except (json.JSONDecodeError, OSError, KeyError):
                        pass
                cache[key] = {"data": data, "timestamp": time.time()}
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f)

            return data

        return wrapper

    return decorator
