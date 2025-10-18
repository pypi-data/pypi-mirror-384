"""
Geohash-based location caching for efficient geographic data caching.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union

import pygeohash as pgh

from redis_cache_toolkit.connection import get_redis_connection, RedisConfig
from redis_cache_toolkit.helpers import serialize_for_cache, deserialize_from_cache


logger = logging.getLogger(__name__)


class GeohashCacheManager:
    """
    Manager for geohash-based location caching.
    
    This class provides methods to cache location-based data using geohash encoding.
    Geohashing allows for efficient spatial indexing and querying of geographic data.
    
    Attributes:
        redis_config: Redis configuration
        default_precision: Default geohash precision (1-12, default: 5)
        default_timeout: Default cache timeout in seconds
        
    Examples:
        >>> manager = GeohashCacheManager(precision=5, timeout=1800)
        >>> 
        >>> # Cache city ID by coordinates
        >>> manager.set_location_data(41.0082, 28.9784, "city_id", 34)
        >>> 
        >>> # Retrieve city ID
        >>> city_id = manager.get_location_data(41.0082, 28.9784, "city_id")
    """
    
    def __init__(
        self,
        redis_config: Optional[RedisConfig] = None,
        precision: int = 5,
        timeout: int = 1800,
    ):
        """
        Initialize GeohashCacheManager.
        
        Args:
            redis_config: Redis configuration
            precision: Geohash precision (1-12). Higher = more precise but less area coverage
            timeout: Default cache timeout in seconds
        """
        self.redis_config = redis_config
        self.precision = precision
        self.timeout = timeout
        self._redis_conn = None
        self._redis_conn_raw = None
    
    @property
    def redis_conn(self):
        """Get Redis connection with decode_responses=True."""
        if self._redis_conn is None:
            self._redis_conn = get_redis_connection(self.redis_config, decode_responses=True)
        return self._redis_conn
    
    @property
    def redis_conn_raw(self):
        """Get Redis connection with decode_responses=False."""
        if self._redis_conn_raw is None:
            self._redis_conn_raw = get_redis_connection(self.redis_config, decode_responses=False)
        return self._redis_conn_raw
    
    def encode_location(self, lat: float, lon: float, precision: Optional[int] = None) -> str:
        """
        Encode latitude and longitude into geohash.
        
        Args:
            lat: Latitude
            lon: Longitude
            precision: Geohash precision (default: instance precision)
            
        Returns:
            Geohash string
            
        Examples:
            >>> manager = GeohashCacheManager()
            >>> geohash = manager.encode_location(41.0082, 28.9784)
            >>> print(geohash)  # 'sxk3z'
        """
        precision = precision or self.precision
        return pgh.encode(lat, lon, precision=precision)
    
    def decode_location(self, geohash: str) -> tuple:
        """
        Decode geohash into latitude and longitude.
        
        Args:
            geohash: Geohash string
            
        Returns:
            Tuple of (latitude, longitude)
            
        Examples:
            >>> manager = GeohashCacheManager()
            >>> lat, lon = manager.decode_location('sxk3z')
            >>> print(f"{lat}, {lon}")  # '41.01, 28.98'
        """
        return pgh.decode(geohash)
    
    def set_location_data(
        self,
        lat: float,
        lon: float,
        key_suffix: str,
        value: Any,
        timeout: Optional[int] = None,
        precision: Optional[int] = None,
    ) -> bool:
        """
        Cache data by geographic location.
        
        Args:
            lat: Latitude
            lon: Longitude
            key_suffix: Suffix for cache key (e.g., 'city_id', 'township_id')
            value: Value to cache
            timeout: Cache timeout in seconds (default: instance timeout)
            precision: Geohash precision (default: instance precision)
            
        Returns:
            True if successful
            
        Examples:
            >>> manager = GeohashCacheManager()
            >>> manager.set_location_data(41.0082, 28.9784, "city_id", 34)
            >>> manager.set_location_data(41.0082, 28.9784, "weather", {"temp": 20})
        """
        try:
            geohash = self.encode_location(lat, lon, precision)
            cache_key = f"geo:{geohash}:{key_suffix}"
            serialized = serialize_for_cache(value)
            timeout = timeout or self.timeout
            
            self.redis_conn_raw.set(cache_key, serialized, ex=timeout)
            logger.debug(f"Cached location data: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error caching location data: {e}")
            return False
    
    def get_location_data(
        self,
        lat: float,
        lon: float,
        key_suffix: str,
        precision: Optional[int] = None,
    ) -> Optional[Any]:
        """
        Retrieve cached data by geographic location.
        
        Args:
            lat: Latitude
            lon: Longitude
            key_suffix: Suffix for cache key
            precision: Geohash precision (default: instance precision)
            
        Returns:
            Cached value or None if not found
            
        Examples:
            >>> manager = GeohashCacheManager()
            >>> city_id = manager.get_location_data(41.0082, 28.9784, "city_id")
            >>> print(city_id)  # 34
        """
        try:
            geohash = self.encode_location(lat, lon, precision)
            cache_key = f"geo:{geohash}:{key_suffix}"
            
            cached_value = self.redis_conn_raw.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for location data: {cache_key}")
                return deserialize_from_cache(cached_value)
            
            logger.debug(f"Cache miss for location data: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving location data: {e}")
            return None
    
    def delete_location_data(
        self,
        lat: float,
        lon: float,
        key_suffix: str,
        precision: Optional[int] = None,
    ) -> bool:
        """
        Delete cached data by geographic location.
        
        Args:
            lat: Latitude
            lon: Longitude
            key_suffix: Suffix for cache key
            precision: Geohash precision (default: instance precision)
            
        Returns:
            True if successful
        """
        try:
            geohash = self.encode_location(lat, lon, precision)
            cache_key = f"geo:{geohash}:{key_suffix}"
            
            self.redis_conn.delete(cache_key)
            logger.debug(f"Deleted location data: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting location data: {e}")
            return False


def geohash_cached(
    key_suffix: str,
    precision: int = 5,
    timeout: int = 1800,
    lat_arg: str = "lat",
    lon_arg: str = "lon",
    redis_config: Optional[RedisConfig] = None,
) -> Callable:
    """
    Decorator for caching function results based on geographic coordinates.
    
    This decorator automatically caches function results using geohash encoding
    of the provided latitude and longitude arguments.
    
    Args:
        key_suffix: Suffix for cache key (e.g., 'city_id', 'township_id')
        precision: Geohash precision (1-12, default: 5)
        timeout: Cache timeout in seconds (default: 1800)
        lat_arg: Name of latitude argument (default: 'lat')
        lon_arg: Name of longitude argument (default: 'lon')
        redis_config: Redis configuration
        
    Returns:
        Decorated function
        
    Examples:
        >>> @geohash_cached("city_id", precision=5, timeout=1800)
        ... def get_city_from_coords(lat: float, lon: float) -> int:
        ...     # Expensive reverse geocoding operation
        ...     return reverse_geocode_city(lat, lon)
        >>> 
        >>> city_id = get_city_from_coords(41.0082, 28.9784)  # Cached
        >>> city_id = get_city_from_coords(41.0082, 28.9784)  # From cache
        
        >>> # With custom argument names
        >>> @geohash_cached("weather", lat_arg="latitude", lon_arg="longitude")
        ... def get_weather(latitude: float, longitude: float):
        ...     return fetch_weather_api(latitude, longitude)
        
    Notes:
        - Function must accept lat and lon as keyword arguments or positional args
        - Geohash precision determines the area size:
          * precision=5: ~4.9km x 4.9km
          * precision=6: ~1.2km x 0.6km
          * precision=7: ~153m x 153m
    """
    manager = GeohashCacheManager(redis_config, precision, timeout)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract lat and lon from arguments
            lat = kwargs.get(lat_arg)
            lon = kwargs.get(lon_arg)
            
            # Try to get from positional args if not in kwargs
            if lat is None or lon is None:
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                
                if lat_arg in param_names and lon_arg in param_names:
                    lat_idx = param_names.index(lat_arg)
                    lon_idx = param_names.index(lon_arg)
                    
                    if lat_idx < len(args):
                        lat = args[lat_idx]
                    if lon_idx < len(args):
                        lon = args[lon_idx]
            
            if lat is None or lon is None:
                logger.warning(
                    f"Could not extract lat/lon from {func.__name__} arguments. "
                    f"Looking for '{lat_arg}' and '{lon_arg}'"
                )
                return func(*args, **kwargs)
            
            # Try to get from cache
            cached_value = manager.get_location_data(lat, lon, key_suffix)
            if cached_value is not None:
                return cached_value
            
            # Cache miss - call original function
            result = func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                manager.set_location_data(lat, lon, key_suffix, result)
            
            return result
        
        return wrapper
    return decorator

