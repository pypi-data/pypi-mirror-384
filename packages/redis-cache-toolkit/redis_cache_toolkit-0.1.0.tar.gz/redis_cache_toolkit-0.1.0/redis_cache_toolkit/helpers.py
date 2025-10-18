"""
Helper utilities for cache key generation and object handling.
"""
from typing import Any, Dict, Tuple


CUSTOMER_IDENTIFIER_ATTR = "id"


def check_is_identifiable_object(item: Any) -> bool:
    """
    Check if an object has an identifier attribute.
    
    Args:
        item: Object to check
        
    Returns:
        True if object has identifier attribute
    """
    return hasattr(item, CUSTOMER_IDENTIFIER_ATTR)


def parse_identifiable_object(item: Any) -> Any:
    """
    Extract identifier from an object.
    
    Args:
        item: Object with identifier attribute
        
    Returns:
        The identifier value
    """
    return getattr(item, CUSTOMER_IDENTIFIER_ATTR)


def make_cache_key(
    args: Tuple,
    kwargs: Dict,
    typed: bool = False,
    kwd_mark: Tuple = (object(),),
    fasttypes: set = None,
) -> int:
    """
    Make a cache key from optionally typed positional and keyword arguments.
    
    This function is inspired by functools._make_key but enhanced for Redis caching.
    The key is constructed in a flat manner for better performance.
    
    Args:
        args: Positional arguments tuple
        kwargs: Keyword arguments dictionary
        typed: If True, arguments of different types will be cached separately
        kwd_mark: Marker tuple for separating args and kwargs
        fasttypes: Set of types known to cache their hash value
        
    Returns:
        Hash value that can be used as cache key
        
    Examples:
        >>> make_cache_key((1, 2), {"x": 3}, typed=False)
        123456789
        
        >>> make_cache_key(("hello",), {}, typed=True)
        987654321
    """
    if fasttypes is None:
        fasttypes = {int, str, float, bool}
    
    # Build the key tuple
    key = args
    
    if kwargs:
        key += kwd_mark
        for item in kwargs.items():
            # Handle objects with identifiers (e.g., Django models, Pydantic models)
            if check_is_identifiable_object(item[1]):
                key += (item[0], parse_identifiable_object(item[1]))
            else:
                key += item
    
    # Add type information if requested
    if typed:
        key += tuple(type(v) for v in args)
        if kwargs:
            key += tuple(type(v) for v in kwargs.values())
    
    # Optimization: if single argument of fast type, return it directly
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    
    return hash(key)


def serialize_for_cache(value: Any) -> bytes:
    """
    Serialize a Python object for Redis storage using pickle.
    
    Args:
        value: Object to serialize
        
    Returns:
        Serialized bytes
    """
    import pickle
    return pickle.dumps(value)


def deserialize_from_cache(data: bytes) -> Any:
    """
    Deserialize a Python object from Redis storage.
    
    Args:
        data: Serialized bytes
        
    Returns:
        Deserialized Python object
    """
    import pickle
    return pickle.loads(data)

