"""Pytest configuration and fixtures."""
import pytest
from redis import Redis
from redis_cache_toolkit.connection import RedisConfig, reset_connections


@pytest.fixture(scope="function")
def redis_config():
    """Provide Redis configuration for tests."""
    return RedisConfig(
        host="localhost",
        port=6379,
        db=15,  # Use separate DB for tests
        decode_responses=True,
    )


@pytest.fixture(scope="function")
def redis_conn(redis_config):
    """Provide Redis connection for tests."""
    from redis_cache_toolkit.connection import get_redis_connection
    
    conn = get_redis_connection(redis_config, force_new=True)
    
    # Clean up before test
    conn.flushdb()
    
    yield conn
    
    # Clean up after test
    conn.flushdb()
    reset_connections()


@pytest.fixture(scope="function")
def mock_redis(monkeypatch):
    """Mock Redis connection for unit tests without Redis server."""
    from unittest.mock import MagicMock
    
    mock = MagicMock(spec=Redis)
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    
    def mock_get_connection(*args, **kwargs):
        return mock
    
    monkeypatch.setattr(
        "redis_cache_toolkit.connection.get_redis_connection",
        mock_get_connection
    )
    
    return mock

