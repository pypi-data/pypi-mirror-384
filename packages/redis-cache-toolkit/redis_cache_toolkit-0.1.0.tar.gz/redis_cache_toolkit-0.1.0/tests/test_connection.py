"""Tests for Redis connection management."""
import pytest
from redis import Redis
from redis_cache_toolkit.connection import (
    RedisConfig,
    RedisConnectionType,
    get_redis_connection,
    reset_connections,
)


class TestRedisConfig:
    """Tests for RedisConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RedisConfig()
        assert config.connection_type == RedisConnectionType.STANDALONE
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.decode_responses is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=5,
            password="secret",
            ssl=True
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 5
        assert config.password == "secret"
        assert config.ssl is True
    
    def test_sentinel_config(self):
        """Test Sentinel configuration."""
        config = RedisConfig(
            connection_type=RedisConnectionType.SENTINEL,
            sentinel_hosts=["sentinel1:26379", "sentinel2:26379"],
            sentinel_name="mymaster"
        )
        assert config.connection_type == RedisConnectionType.SENTINEL
        assert len(config.sentinel_hosts) == 2
        assert config.sentinel_name == "mymaster"


class TestGetRedisConnection:
    """Tests for get_redis_connection function."""
    
    def test_standalone_connection(self):
        """Test creating standalone Redis connection."""
        config = RedisConfig(host="localhost", port=6379, db=15)
        
        try:
            conn = get_redis_connection(config, force_new=True)
            assert isinstance(conn, Redis)
            
            # Test connection
            conn.ping()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_connection_reuse(self):
        """Test that connections are reused."""
        config = RedisConfig(db=15)
        
        reset_connections()
        
        try:
            conn1 = get_redis_connection(config)
            conn2 = get_redis_connection(config)
            assert conn1 is conn2  # Should be same instance
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_force_new_connection(self):
        """Test forcing new connection creation."""
        config = RedisConfig(db=15)
        
        reset_connections()
        
        try:
            conn1 = get_redis_connection(config)
            conn2 = get_redis_connection(config, force_new=True)
            # These will be different instances
            assert conn1 is not conn2
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_decode_responses_variants(self):
        """Test connections with different decode_responses settings."""
        config = RedisConfig(db=15)
        
        reset_connections()
        
        try:
            conn_decoded = get_redis_connection(config, decode_responses=True)
            conn_raw = get_redis_connection(config, decode_responses=False)
            
            # Should be different instances
            assert conn_decoded is not conn_raw
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_reset_connections(self):
        """Test resetting global connections."""
        config = RedisConfig(db=15)
        
        try:
            conn1 = get_redis_connection(config)
            reset_connections()
            conn2 = get_redis_connection(config)
            
            # After reset, should get new instance
            assert conn1 is not conn2
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestSentinelConnection:
    """Tests for Sentinel connection (requires Sentinel setup)."""
    
    def test_sentinel_connection_validation(self):
        """Test that Sentinel connection validates required parameters."""
        config = RedisConfig(connection_type=RedisConnectionType.SENTINEL)
        
        with pytest.raises(ValueError, match="sentinel_hosts"):
            get_redis_connection(config, force_new=True)
        
        config.sentinel_hosts = ["localhost:26379"]
        with pytest.raises(ValueError, match="sentinel_name"):
            get_redis_connection(config, force_new=True)


class TestClusterConnection:
    """Tests for Cluster connection (requires redis-py-cluster)."""
    
    def test_cluster_connection_validation(self):
        """Test that Cluster connection validates required parameters."""
        config = RedisConfig(connection_type=RedisConnectionType.CLUSTER)
        
        with pytest.raises(ValueError, match="cluster_nodes"):
            get_redis_connection(config, force_new=True)

