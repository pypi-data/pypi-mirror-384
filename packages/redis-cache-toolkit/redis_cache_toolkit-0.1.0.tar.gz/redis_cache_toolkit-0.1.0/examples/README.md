# Redis Cache Toolkit - Examples

This directory contains comprehensive examples demonstrating the features of redis-cache-toolkit.

## Prerequisites

Before running the examples, make sure you have:

1. **Redis server running**:
   ```bash
   # On macOS with Homebrew
   brew services start redis
   
   # On Ubuntu/Debian
   sudo systemctl start redis
   
   # Or using Docker
   docker run -d -p 6379:6379 redis:latest
   ```

2. **redis-cache-toolkit installed**:
   ```bash
   pip install redis-cache-toolkit[all]
   ```

## Running the Examples

### Basic Caching
```bash
python examples/basic_caching.py
```

Demonstrates:
- Simple function caching
- Different argument handling
- Custom cache key prefixes
- Type-sensitive caching
- Custom Redis configurations
- Caching with keyword arguments

### Pydantic Model Caching
```bash
python examples/pydantic_models.py
```

Demonstrates:
- Basic model caching
- Model validation
- Nested models
- Error handling
- Complex e-commerce examples
- API response caching

### Geohash Location Caching
```bash
python examples/geohash_caching.py
```

Demonstrates:
- Basic geohash caching
- Precision comparison
- Manual cache management
- Weather service example
- Restaurant finder
- Custom argument names
- Complete geocoding service

## Example Outputs

### Basic Caching Output
```
============================================================
Example 1: Simple Function Caching
============================================================

First call (will take 2 seconds):
  → Executing expensive operation: 10 + 20
  Result: 30, Time: 2.01s

Second call (instant from cache):
  Result: 30, Time: 0.00s
  ⚡ Speedup: 201.0x faster!
```

### Pydantic Models Output
```
============================================================
Example 1: Basic Pydantic Model Caching
============================================================

First call (from database):
  → Fetching user 123 from database...
  Type: <class '__main__.User'>
  User: User 123 <user123@example.com>
  Active: True

Second call (from cache):
  Type: <class '__main__.User'>
  User: User 123 <user123@example.com>
```

### Geohash Caching Output
```
============================================================
Example 1: Basic Geohash Caching
============================================================

First call - API request:
  → Reverse geocoding (41.0082, 28.9784)...
  City ID: 34

Second call - same coordinates (cached):
  City ID: 34

Third call - nearby coordinates (same geohash, cached!):
  City ID: 34
  ⚡ Nearby locations share the same cache!
```

## Tips for Learning

1. **Start with basic_caching.py** - Understand the fundamentals
2. **Move to pydantic_models.py** - Learn type-safe caching
3. **Explore geohash_caching.py** - Master location-based caching
4. **Mix and match** - Combine different features in your projects

## Common Pitfalls

1. **Redis not running**: Make sure Redis server is running before examples
2. **Port conflicts**: Check if Redis is running on default port 6379
3. **Import errors**: Install all dependencies with `pip install redis-cache-toolkit[all]`

## Extending the Examples

Feel free to modify these examples to test:
- Different timeout values
- Custom Redis configurations
- Your own data models
- Real API integrations

## Need Help?

- 📚 Check the main [README.md](../README.md)
- 🐛 Report issues on [GitHub](https://github.com/yourusername/redis-cache-toolkit/issues)
- 💬 Ask questions in [Discussions](https://github.com/yourusername/redis-cache-toolkit/discussions)

## Contributing

If you create interesting examples, please consider contributing them back to the project!

