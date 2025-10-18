"""
Core caching decorators for Redis.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union

from redis_cache_toolkit.connection import get_redis_connection, RedisConfig
from redis_cache_toolkit.helpers import (
    make_cache_key,
    serialize_for_cache,
    deserialize_from_cache,
)


logger = logging.getLogger(__name__)

T = TypeVar('T')


def cached(
    timeout: int = 60,
    typed: bool = False,
    key_prefix: Optional[str] = None,
    redis_config: Optional[RedisConfig] = None,
) -> Callable:
    """
    Cache function results in Redis with automatic serialization.
    
    This decorator caches the return value of a function in Redis using pickle
    serialization. The cache key is automatically generated from function name
    and arguments.
    
    Args:
        timeout: Cache timeout in seconds (default: 60)
        typed: If True, arguments of different types are cached separately
        key_prefix: Custom prefix for cache keys (default: function name)
        redis_config: Redis configuration (default: standalone localhost)
        
    Returns:
        Decorated function
        
    Examples:
        >>> @cached(timeout=300)
        ... def get_user(user_id: int):
        ...     return db.query(User).get(user_id)
        
        >>> @cached(timeout=3600, typed=True, key_prefix="api")
        ... def fetch_api_data(endpoint: str):
        ...     return requests.get(endpoint).json()
        
    Notes:
        - Uses pickle for serialization, so cached objects must be picklable
        - Cache key includes function name and all arguments
        - Thread-safe within a single Redis instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get Redis connection
            redis_conn = get_redis_connection(redis_config, decode_responses=False)
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            arg_key = make_cache_key(args, kwargs, typed=typed)
            cache_key = f"cache:{prefix}:{arg_key}"
            
            # Try to get from cache
            try:
                cached_value = redis_conn.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return deserialize_from_cache(cached_value)
            except Exception as e:
                logger.warning(f"Cache read error for key {cache_key}: {e}")
            
            # Cache miss - call original function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            try:
                serialized = serialize_for_cache(result)
                redis_conn.set(cache_key, serialized, ex=timeout)
                logger.debug(f"Cached result for key: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache write error for key {cache_key}: {e}")
            
            return result
        
        return wrapper
    return decorator


def cached_model(
    model_class: Type[T],
    timeout: int = 60,
    typed: bool = False,
    key_prefix: Optional[str] = None,
    redis_config: Optional[RedisConfig] = None,
    return_none_on_error: bool = True,
) -> Callable:
    """
    Cache function results and validate with Pydantic model.
    
    This decorator caches function results and automatically validates/deserializes
    them using a Pydantic model. Useful for type-safe API response caching.
    
    Args:
        model_class: Pydantic model class for validation
        timeout: Cache timeout in seconds (default: 60)
        typed: If True, arguments of different types are cached separately
        key_prefix: Custom prefix for cache keys
        redis_config: Redis configuration
        return_none_on_error: Return None on validation error (default: True)
        
    Returns:
        Decorated function that returns model instances
        
    Examples:
        >>> from pydantic import BaseModel
        >>> 
        >>> class User(BaseModel):
        ...     id: int
        ...     name: str
        ...     email: str
        >>> 
        >>> @cached_model(User, timeout=300)
        ... def get_user_profile(user_id: int):
        ...     return {"id": user_id, "name": "John", "email": "john@example.com"}
        >>> 
        >>> user = get_user_profile(123)  # Returns User instance
        >>> assert isinstance(user, User)
        
    Notes:
        - Requires pydantic package: pip install redis-cache-toolkit[pydantic]
        - Function should return dict or object compatible with model
        - Validation errors are logged and can return None or raise
    """
    try:
        from pydantic import ValidationError
    except ImportError:
        raise ImportError(
            "pydantic is required for cached_model. "
            "Install it with: pip install redis-cache-toolkit[pydantic]"
        )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            # Get Redis connection
            redis_conn = get_redis_connection(redis_config, decode_responses=False)
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            arg_key = make_cache_key(args, kwargs, typed=typed)
            cache_key = f"cache:model:{prefix}:{arg_key}"
            
            # Try to get from cache
            try:
                cached_value = redis_conn.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    data = deserialize_from_cache(cached_value)
                    # Validate with Pydantic model
                    try:
                        return model_class(**data) if isinstance(data, dict) else data
                    except ValidationError as e:
                        logger.error(f"Validation error for cached data: {e}")
                        if return_none_on_error:
                            return None
                        raise
            except Exception as e:
                logger.warning(f"Cache read error for key {cache_key}: {e}")
            
            # Cache miss - call original function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            
            if result is None:
                return None
            
            # Validate result with Pydantic model
            try:
                model_instance = model_class(**result) if isinstance(result, dict) else result
            except ValidationError as e:
                logger.error(f"Validation error for function result: {e}")
                if return_none_on_error:
                    return None
                raise
            
            # Store in cache (store the dict representation)
            try:
                cache_data = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else model_instance.dict()
                serialized = serialize_for_cache(cache_data)
                redis_conn.set(cache_key, serialized, ex=timeout)
                logger.debug(f"Cached model result for key: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache write error for key {cache_key}: {e}")
            
            return model_instance
        
        return wrapper
    return decorator


def capture_exception_decorator(
    fallback_value: Any = None,
    log_errors: bool = True,
    capture_to_sentry: bool = False,
) -> Callable:
    """
    Decorator to catch exceptions and return fallback value.
    
    Useful for non-critical cached functions where you want graceful degradation.
    
    Args:
        fallback_value: Value to return on exception (default: None)
        log_errors: Whether to log errors (default: True)
        capture_to_sentry: Send errors to Sentry if available (default: False)
        
    Returns:
        Decorated function
        
    Examples:
        >>> @capture_exception_decorator(fallback_value={})
        ... @cached(timeout=60)
        ... def get_config():
        ...     return fetch_config_from_api()
        
        >>> config = get_config()  # Returns {} if any error occurs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {exc}")
                
                if capture_to_sentry:
                    try:
                        from sentry_sdk import capture_exception
                        capture_exception(exc)
                    except ImportError:
                        pass
                
                return fallback_value
        
        return wrapper
    return decorator


def dont_unpack_list(func: Callable) -> Callable:
    """
    Decorator to get first item of list or tuple result.
    
    Useful when you want to cache a list but only need the first item.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that returns first element if result is list/tuple
        
    Examples:
        >>> @dont_unpack_list
        ... @cached(timeout=60)
        ... def get_latest_item():
        ...     return [1, 2, 3]
        >>> 
        >>> result = get_latest_item()  # Returns 1, not [1, 2, 3]
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        if isinstance(result, (list, tuple)) and len(result) > 0:
            return result[0]
        return result
    
    return wrapper


def default_positive_int(func: Callable) -> Callable:
    """
    Decorator that returns 1 if cache is not found instead of None.
    
    Ensures that the function always returns a positive integer, useful
    for counter or ID caching.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that returns 1 if result is falsy
        
    Examples:
        >>> @default_positive_int
        ... @cached(timeout=60)
        ... def get_counter():
        ...     return redis_conn.get('counter')
        >>> 
        >>> count = get_counter()  # Returns 1 if cache miss
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        result = func(*args, **kwargs)
        return result if result else 1
    
    return wrapper

