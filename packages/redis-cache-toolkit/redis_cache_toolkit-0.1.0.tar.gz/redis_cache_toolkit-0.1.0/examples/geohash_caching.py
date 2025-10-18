"""
Geohash-based Location Caching Examples
========================================

This example demonstrates efficient location-based caching using geohash encoding.
"""
import time
import random
from redis_cache_toolkit import geohash_cached, GeohashCacheManager


# Example 1: Basic geohash caching
print("=" * 60)
print("Example 1: Basic Geohash Caching")
print("=" * 60)

@geohash_cached("city_id", precision=5, timeout=1800)
def get_city_from_coordinates(lat: float, lon: float) -> int:
    """Reverse geocoding with geohash-based caching."""
    print(f"  → Reverse geocoding ({lat}, {lon})...")
    time.sleep(1)  # Simulate API call
    
    # Simplified city detection
    if 40.5 <= lat <= 41.5 and 28.5 <= lon <= 29.5:
        return 34  # Istanbul
    elif 39.5 <= lat <= 40.5 and 32.5 <= lon <= 33.5:
        return 6   # Ankara
    else:
        return 0   # Unknown

print("\nFirst call - API request:")
city_id = get_city_from_coordinates(41.0082, 28.9784)
print(f"  City ID: {city_id}")

print("\nSecond call - same coordinates (cached):")
city_id = get_city_from_coordinates(41.0082, 28.9784)
print(f"  City ID: {city_id}")

print("\nThird call - nearby coordinates (same geohash, cached!):")
city_id = get_city_from_coordinates(41.0085, 28.9786)
print(f"  City ID: {city_id}")
print(f"  ⚡ Nearby locations share the same cache!")


# Example 2: Geohash precision comparison
print("\n" + "=" * 60)
print("Example 2: Geohash Precision Comparison")
print("=" * 60)

manager = GeohashCacheManager(precision=5, timeout=1800)

# Show geohash for different precision levels
lat, lon = 41.0082, 28.9784
print(f"\nCoordinates: {lat}, {lon}")
print("\nGeohash at different precisions:")

for precision in [3, 4, 5, 6, 7]:
    geohash = manager.encode_location(lat, lon, precision=precision)
    print(f"  Precision {precision}: {geohash}")


# Example 3: Manual geohash cache management
print("\n" + "=" * 60)
print("Example 3: Manual Geohash Cache Management")
print("=" * 60)

manager = GeohashCacheManager(precision=5, timeout=1800)

# Store multiple types of location data
istanbul_lat, istanbul_lon = 41.0082, 28.9784

print("\nStoring location data:")
manager.set_location_data(istanbul_lat, istanbul_lon, "city_id", 34)
manager.set_location_data(istanbul_lat, istanbul_lon, "city_name", "Istanbul")
manager.set_location_data(istanbul_lat, istanbul_lon, "weather", {
    "temp": 20,
    "condition": "sunny",
    "humidity": 60
})
print("  ✓ Stored city_id, city_name, and weather data")

print("\nRetrieving location data:")
city_id = manager.get_location_data(istanbul_lat, istanbul_lon, "city_id")
city_name = manager.get_location_data(istanbul_lat, istanbul_lon, "city_name")
weather = manager.get_location_data(istanbul_lat, istanbul_lon, "weather")

print(f"  City ID: {city_id}")
print(f"  City Name: {city_name}")
print(f"  Weather: {weather}")


# Example 4: Weather service with geohash caching
print("\n" + "=" * 60)
print("Example 4: Weather Service")
print("=" * 60)

@geohash_cached("weather_data", precision=5, timeout=600)
def get_weather(lat: float, lon: float) -> dict:
    """Fetch weather data (cached for 10 minutes)."""
    print(f"  → Fetching weather for ({lat}, {lon})...")
    time.sleep(0.5)
    return {
        "temperature": random.randint(15, 30),
        "condition": random.choice(["sunny", "cloudy", "rainy"]),
        "humidity": random.randint(40, 90),
        "wind_speed": random.randint(5, 25)
    }

print("\nFetching weather for different locations:")
locations = [
    (41.0082, 28.9784, "Istanbul"),
    (41.0085, 28.9786, "Istanbul (nearby)"),
    (39.9334, 32.8597, "Ankara"),
]

for lat, lon, name in locations:
    weather = get_weather(lat, lon)
    print(f"\n  {name} ({lat}, {lon}):")
    print(f"    Temperature: {weather['temperature']}°C")
    print(f"    Condition: {weather['condition']}")
    print(f"    Humidity: {weather['humidity']}%")
    print(f"    Wind: {weather['wind_speed']} km/h")


# Example 5: Restaurant finder with geohash
print("\n" + "=" * 60)
print("Example 5: Restaurant Finder")
print("=" * 60)

@geohash_cached("nearby_restaurants", precision=6, timeout=300)
def find_nearby_restaurants(lat: float, lon: float, radius_km: int = 1) -> list:
    """Find restaurants near coordinates."""
    print(f"  → Searching restaurants within {radius_km}km of ({lat}, {lon})...")
    time.sleep(0.8)
    
    # Simulate restaurant search
    restaurants = [
        {"name": "Restaurant A", "cuisine": "Turkish", "rating": 4.5},
        {"name": "Restaurant B", "cuisine": "Italian", "rating": 4.2},
        {"name": "Restaurant C", "cuisine": "Japanese", "rating": 4.8},
    ]
    return restaurants

print("\nSearching for restaurants:")
restaurants = find_nearby_restaurants(41.0082, 28.9784)
print(f"\n  Found {len(restaurants)} restaurants:")
for r in restaurants:
    print(f"    - {r['name']} ({r['cuisine']}) - ⭐ {r['rating']}")

print("\nSearching again (cached):")
restaurants = find_nearby_restaurants(41.0082, 28.9784)
print(f"  Found {len(restaurants)} restaurants (from cache)")


# Example 6: Custom argument names
print("\n" + "=" * 60)
print("Example 6: Custom Argument Names")
print("=" * 60)

@geohash_cached(
    "elevation",
    precision=7,
    timeout=3600,
    lat_arg="latitude",
    lon_arg="longitude"
)
def get_elevation(latitude: float, longitude: float) -> float:
    """Get elevation for coordinates with custom arg names."""
    print(f"  → Fetching elevation for ({latitude}, {longitude})...")
    time.sleep(0.5)
    return random.uniform(0, 1000)

print("\nFetching elevation:")
elevation = get_elevation(latitude=41.0082, longitude=28.9784)
print(f"  Elevation: {elevation:.2f}m")

print("\nFetching again (cached):")
elevation = get_elevation(latitude=41.0082, longitude=28.9784)
print(f"  Elevation: {elevation:.2f}m")


# Example 7: Geocoding service
print("\n" + "=" * 60)
print("Example 7: Complete Geocoding Service")
print("=" * 60)

manager = GeohashCacheManager(precision=5, timeout=1800)

def geocode_location(lat: float, lon: float) -> dict:
    """Complete geocoding with multiple data points."""
    
    # Try to get from cache
    city_id = manager.get_location_data(lat, lon, "city_id")
    city_name = manager.get_location_data(lat, lon, "city_name")
    district = manager.get_location_data(lat, lon, "district")
    
    if all([city_id, city_name, district]):
        print(f"  ✓ All data from cache for ({lat}, {lon})")
        return {
            "city_id": city_id,
            "city_name": city_name,
            "district": district,
            "cached": True
        }
    
    # Simulate API call
    print(f"  → Geocoding ({lat}, {lon})...")
    time.sleep(1)
    
    result = {
        "city_id": 34,
        "city_name": "Istanbul",
        "district": "Kadıköy",
        "cached": False
    }
    
    # Cache all data
    manager.set_location_data(lat, lon, "city_id", result["city_id"])
    manager.set_location_data(lat, lon, "city_name", result["city_name"])
    manager.set_location_data(lat, lon, "district", result["district"])
    
    return result

print("\nFirst geocoding call:")
location1 = geocode_location(41.0082, 28.9784)
print(f"  {location1['city_name']}, {location1['district']}")
print(f"  Cached: {location1['cached']}")

print("\nSecond geocoding call (all from cache):")
location2 = geocode_location(41.0085, 28.9786)
print(f"  {location2['city_name']}, {location2['district']}")
print(f"  Cached: {location2['cached']}")


# Example 8: Geohash encoding/decoding
print("\n" + "=" * 60)
print("Example 8: Geohash Encoding/Decoding")
print("=" * 60)

manager = GeohashCacheManager()

test_locations = [
    (41.0082, 28.9784, "Istanbul"),
    (39.9334, 32.8597, "Ankara"),
    (38.4192, 27.1287, "İzmir"),
]

print("\nGeohash encoding:")
for lat, lon, name in test_locations:
    geohash = manager.encode_location(lat, lon, precision=5)
    decoded_lat, decoded_lon = manager.decode_location(geohash)
    
    print(f"\n  {name}:")
    print(f"    Original:  ({lat}, {lon})")
    print(f"    Geohash:   {geohash}")
    print(f"    Decoded:   ({decoded_lat:.4f}, {decoded_lon:.4f})")
    print(f"    Precision: ~4.9km x 4.9km area")


print("\n" + "=" * 60)
print("✅ All geohash examples completed!")
print("=" * 60)
print("\n💡 Key Takeaways:")
print("  - Nearby locations share the same cache (efficient!)")
print("  - Precision determines the area size")
print("  - Perfect for reverse geocoding and location-based services")
print("  - Significantly reduces API calls for location data")

