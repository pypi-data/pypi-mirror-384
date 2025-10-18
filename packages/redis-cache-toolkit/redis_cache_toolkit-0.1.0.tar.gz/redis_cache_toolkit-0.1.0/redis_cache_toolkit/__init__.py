"""
Redis Cache Toolkit
===================

Advanced Redis caching decorators with support for:
- Pydantic models
- Geohash-based location caching
- Multiple Redis configurations (standalone, sentinel, cluster)
- Type-safe cache keys
- Automatic serialization/deserialization

Example usage:
    >>> from redis_cache_toolkit import cached, cached_model, geohash_cached
    >>> 
    >>> @cached(timeout=60)
    ... def expensive_function(user_id: int):
    ...     return fetch_user_data(user_id)
    >>> 
    >>> @cached_model(UserModel, timeout=300)
    ... def get_user_profile(user_id: int):
    ...     return {"id": user_id, "name": "John"}
"""

__version__ = "0.1.0"
__author__ = "Redis Cache Toolkit Contributors"

from redis_cache_toolkit.decorators import (
    cached,
    cached_model,
    capture_exception_decorator,
    dont_unpack_list,
    default_positive_int,
)
from redis_cache_toolkit.geohash import geohash_cached, GeohashCacheManager
from redis_cache_toolkit.connection import get_redis_connection, RedisConnectionType

__all__ = [
    # Main decorators
    "cached",
    "cached_model",
    "geohash_cached",
    # Utility decorators
    "capture_exception_decorator",
    "dont_unpack_list",
    "default_positive_int",
    # Managers
    "GeohashCacheManager",
    # Connection
    "get_redis_connection",
    "RedisConnectionType",
]

