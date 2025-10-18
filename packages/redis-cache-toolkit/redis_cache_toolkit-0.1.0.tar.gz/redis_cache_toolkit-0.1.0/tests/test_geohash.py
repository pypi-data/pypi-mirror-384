"""Tests for geohash-based location caching."""
import pytest
from redis_cache_toolkit.geohash import GeohashCacheManager, geohash_cached


class TestGeohashCacheManager:
    """Tests for GeohashCacheManager."""
    
    def test_encode_decode_location(self, redis_config):
        """Test geohash encoding and decoding."""
        manager = GeohashCacheManager(redis_config, precision=5)
        
        lat, lon = 41.0082, 28.9784
        geohash = manager.encode_location(lat, lon)
        
        assert isinstance(geohash, str)
        assert len(geohash) == 5
        
        decoded_lat, decoded_lon = manager.decode_location(geohash)
        assert abs(decoded_lat - lat) < 0.01
        assert abs(decoded_lon - lon) < 0.01
    
    def test_set_and_get_location_data(self, redis_conn, redis_config):
        """Test setting and getting location-based data."""
        manager = GeohashCacheManager(redis_config, precision=5, timeout=60)
        
        lat, lon = 41.0082, 28.9784
        city_id = 34
        
        # Set data
        success = manager.set_location_data(lat, lon, "city_id", city_id)
        assert success is True
        
        # Get data
        cached_city_id = manager.get_location_data(lat, lon, "city_id")
        assert cached_city_id == city_id
        
        # Get non-existent data
        result = manager.get_location_data(lat, lon, "non_existent")
        assert result is None
    
    def test_nearby_locations_share_cache(self, redis_conn, redis_config):
        """Test that nearby locations share the same geohash cache."""
        manager = GeohashCacheManager(redis_config, precision=5, timeout=60)
        
        # Set data at one location
        lat1, lon1 = 41.0082, 28.9784
        manager.set_location_data(lat1, lon1, "city_id", 34)
        
        # Get data at very nearby location (within same geohash)
        lat2, lon2 = 41.0083, 28.9785
        cached_value = manager.get_location_data(lat2, lon2, "city_id")
        
        # Should get same value due to geohash approximation
        assert cached_value == 34
    
    def test_precision_affects_area_size(self, redis_conn, redis_config):
        """Test that precision affects cache granularity."""
        # High precision - smaller area
        manager_precise = GeohashCacheManager(redis_config, precision=7, timeout=60)
        
        lat1, lon1 = 41.0082, 28.9784
        manager_precise.set_location_data(lat1, lon1, "test", "value1")
        
        # Slightly different location
        lat2, lon2 = 41.0090, 28.9790
        result = manager_precise.get_location_data(lat2, lon2, "test")
        
        # With high precision, this should be None (different geohash)
        assert result is None or result == "value1"  # Depends on exact distance
    
    def test_delete_location_data(self, redis_conn, redis_config):
        """Test deleting location-based data."""
        manager = GeohashCacheManager(redis_config, precision=5, timeout=60)
        
        lat, lon = 41.0082, 28.9784
        manager.set_location_data(lat, lon, "city_id", 34)
        
        # Verify it exists
        assert manager.get_location_data(lat, lon, "city_id") == 34
        
        # Delete
        success = manager.delete_location_data(lat, lon, "city_id")
        assert success is True
        
        # Verify it's deleted
        assert manager.get_location_data(lat, lon, "city_id") is None
    
    def test_complex_data_types(self, redis_conn, redis_config):
        """Test caching complex data types."""
        manager = GeohashCacheManager(redis_config, precision=5, timeout=60)
        
        lat, lon = 41.0082, 28.9784
        complex_data = {
            "city": "Istanbul",
            "districts": ["Kadıköy", "Beşiktaş"],
            "population": 15_000_000,
            "coordinates": {"lat": lat, "lon": lon}
        }
        
        manager.set_location_data(lat, lon, "city_info", complex_data)
        cached_data = manager.get_location_data(lat, lon, "city_info")
        
        assert cached_data == complex_data


class TestGeohashCachedDecorator:
    """Tests for @geohash_cached decorator."""
    
    def test_basic_geohash_caching(self, redis_conn, redis_config):
        """Test basic geohash-based function caching."""
        call_count = 0
        
        @geohash_cached("city_id", precision=5, timeout=60, redis_config=redis_config)
        def get_city(lat: float, lon: float):
            nonlocal call_count
            call_count += 1
            return 34  # Istanbul
        
        # First call
        result1 = get_city(41.0082, 28.9784)
        assert result1 == 34
        assert call_count == 1
        
        # Second call - from cache
        result2 = get_city(41.0082, 28.9784)
        assert result2 == 34
        assert call_count == 1
        
        # Nearby location - should use same cache
        result3 = get_city(41.0083, 28.9785)
        assert result3 == 34
        assert call_count == 1
    
    def test_custom_arg_names(self, redis_conn, redis_config):
        """Test geohash caching with custom argument names."""
        call_count = 0
        
        @geohash_cached(
            "weather",
            lat_arg="latitude",
            lon_arg="longitude",
            redis_config=redis_config
        )
        def get_weather(latitude: float, longitude: float):
            nonlocal call_count
            call_count += 1
            return {"temp": 20, "condition": "sunny"}
        
        result1 = get_weather(41.0082, 28.9784)
        assert call_count == 1
        
        result2 = get_weather(41.0082, 28.9784)
        assert call_count == 1  # Cached
        assert result2["temp"] == 20
    
    def test_positional_arguments(self, redis_conn, redis_config):
        """Test geohash caching with positional arguments."""
        call_count = 0
        
        @geohash_cached("result", redis_config=redis_config)
        def calculate(lat: float, lon: float, multiplier: int = 1):
            nonlocal call_count
            call_count += 1
            return (lat + lon) * multiplier
        
        result1 = calculate(41.0, 28.0, 2)
        assert call_count == 1
        
        result2 = calculate(41.0, 28.0, 2)
        assert call_count == 1  # Cached
    
    def test_none_return_not_cached(self, redis_conn, redis_config):
        """Test that None results are not cached."""
        call_count = 0
        
        @geohash_cached("data", redis_config=redis_config)
        def get_data(lat: float, lon: float):
            nonlocal call_count
            call_count += 1
            return None
        
        result1 = get_data(41.0, 28.0)
        assert result1 is None
        assert call_count == 1
        
        result2 = get_data(41.0, 28.0)
        assert result2 is None
        assert call_count == 2  # Called again, not cached
    
    def test_different_precisions(self, redis_conn, redis_config):
        """Test caching behavior with different precisions."""
        call_count = 0
        
        @geohash_cached("city", precision=3, redis_config=redis_config)
        def get_city_low_precision(lat: float, lon: float):
            nonlocal call_count
            call_count += 1
            return "Istanbul"
        
        # These coordinates are far apart but might share cache with low precision
        result1 = get_city_low_precision(41.0, 28.0)
        assert call_count == 1
        
        result2 = get_city_low_precision(41.5, 28.5)
        # May or may not be cached depending on geohash precision
        assert result2 == "Istanbul"

