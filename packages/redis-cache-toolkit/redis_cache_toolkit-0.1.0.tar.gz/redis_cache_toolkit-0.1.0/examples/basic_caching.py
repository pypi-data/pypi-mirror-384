"""
Basic Caching Examples
======================

This example demonstrates basic function caching with redis-cache-toolkit.
"""
import time
from redis_cache_toolkit import cached, RedisConfig


# Example 1: Simple function caching
print("=" * 60)
print("Example 1: Simple Function Caching")
print("=" * 60)

@cached(timeout=60)
def expensive_operation(x: int, y: int) -> int:
    """Simulate an expensive operation."""
    print(f"  → Executing expensive operation: {x} + {y}")
    time.sleep(2)  # Simulate delay
    return x + y

print("\nFirst call (will take 2 seconds):")
start = time.time()
result1 = expensive_operation(10, 20)
elapsed1 = time.time() - start
print(f"  Result: {result1}, Time: {elapsed1:.2f}s")

print("\nSecond call (instant from cache):")
start = time.time()
result2 = expensive_operation(10, 20)
elapsed2 = time.time() - start
print(f"  Result: {result2}, Time: {elapsed2:.2f}s")
print(f"  ⚡ Speedup: {elapsed1/elapsed2:.1f}x faster!")


# Example 2: Different arguments create different cache entries
print("\n" + "=" * 60)
print("Example 2: Different Arguments")
print("=" * 60)

print("\nCall with different arguments:")
result3 = expensive_operation(5, 15)
print(f"  Result: {result3}")


# Example 3: Custom cache key prefix
print("\n" + "=" * 60)
print("Example 3: Custom Cache Key Prefix")
print("=" * 60)

@cached(timeout=300, key_prefix="api_v1")
def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from API."""
    print(f"  → Fetching user {user_id} from API...")
    time.sleep(1)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

print("\nFetching user data:")
user1 = fetch_user_data(123)
print(f"  First call: {user1}")

user2 = fetch_user_data(123)
print(f"  Second call (cached): {user2}")


# Example 4: Type-sensitive caching
print("\n" + "=" * 60)
print("Example 4: Type-Sensitive Caching")
print("=" * 60)

call_count = 0

@cached(timeout=60, typed=True)
def type_sensitive_function(x):
    """Cache separately for different types."""
    global call_count
    call_count += 1
    print(f"  → Executing function (call #{call_count}) with {type(x).__name__}: {x}")
    return x * 2

print("\nCalling with int 5:")
result = type_sensitive_function(5)
print(f"  Result: {result}")

print("\nCalling with int 5 again (cached):")
result = type_sensitive_function(5)
print(f"  Result: {result}")

print("\nCalling with float 5.0 (different type, new cache entry):")
result = type_sensitive_function(5.0)
print(f"  Result: {result}")


# Example 5: Custom Redis configuration
print("\n" + "=" * 60)
print("Example 5: Custom Redis Configuration")
print("=" * 60)

# Configure Redis connection
redis_config = RedisConfig(
    host="localhost",
    port=6379,
    db=1,  # Use different database
    # password="your_password",  # Uncomment if authentication needed
)

@cached(timeout=120, redis_config=redis_config)
def fetch_from_custom_redis(key: str) -> str:
    """Use custom Redis configuration."""
    print(f"  → Fetching {key} from custom Redis...")
    time.sleep(0.5)
    return f"Value for {key}"

print("\nUsing custom Redis config:")
value = fetch_from_custom_redis("my_key")
print(f"  Result: {value}")


# Example 6: Caching with kwargs
print("\n" + "=" * 60)
print("Example 6: Caching with Keyword Arguments")
print("=" * 60)

@cached(timeout=60)
def process_data(data: str, uppercase: bool = False, reverse: bool = False) -> str:
    """Process data with optional transformations."""
    print(f"  → Processing: data='{data}', uppercase={uppercase}, reverse={reverse}")
    result = data
    if uppercase:
        result = result.upper()
    if reverse:
        result = result[::-1]
    return result

print("\nWith default kwargs:")
result1 = process_data("hello")
print(f"  Result: {result1}")

print("\nWith uppercase=True:")
result2 = process_data("hello", uppercase=True)
print(f"  Result: {result2}")

print("\nWith uppercase=True (cached):")
result3 = process_data("hello", uppercase=True)
print(f"  Result: {result3}")

print("\nWith both options:")
result4 = process_data("hello", uppercase=True, reverse=True)
print(f"  Result: {result4}")


print("\n" + "=" * 60)
print("✅ All examples completed!")
print("=" * 60)

