"""
Redis connection management supporting standalone, sentinel, and cluster configurations.
"""
import logging
from enum import Enum
from typing import Optional, List, Dict, Any, Union

import redis
from redis import Redis
from redis.sentinel import Sentinel


logger = logging.getLogger(__name__)


class RedisConnectionType(str, Enum):
    """Redis connection types."""
    STANDALONE = "standalone"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


class RedisConfig:
    """
    Configuration holder for Redis connections.
    
    Attributes:
        connection_type: Type of Redis connection
        host: Redis host (for standalone)
        port: Redis port (for standalone)
        db: Redis database number
        password: Redis password
        username: Redis username
        ssl: Enable SSL/TLS
        decode_responses: Decode responses to strings
        sentinel_hosts: List of sentinel host:port strings
        sentinel_name: Sentinel master name
        cluster_nodes: List of cluster nodes
    """
    
    def __init__(
        self,
        connection_type: RedisConnectionType = RedisConnectionType.STANDALONE,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        username: Optional[str] = None,
        ssl: bool = False,
        decode_responses: bool = True,
        sentinel_hosts: Optional[List[str]] = None,
        sentinel_name: Optional[str] = None,
        cluster_nodes: Optional[List[Dict[str, Any]]] = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        **kwargs: Any,
    ):
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.username = username
        self.ssl = ssl
        self.decode_responses = decode_responses
        self.sentinel_hosts = sentinel_hosts or []
        self.sentinel_name = sentinel_name
        self.cluster_nodes = cluster_nodes or []
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.extra_kwargs = kwargs


# Global Redis connection instances
_redis_connection: Optional[Redis] = None
_redis_connection_raw: Optional[Redis] = None  # Without decode_responses


def get_redis_connection(
    config: Optional[RedisConfig] = None,
    decode_responses: bool = True,
    force_new: bool = False,
) -> Redis:
    """
    Get a Redis connection based on configuration.
    
    This function maintains singleton connections for better performance.
    Use force_new=True to create a new connection.
    
    Args:
        config: Redis configuration. If None, uses default standalone config
        decode_responses: Whether to decode responses to strings
        force_new: Force creation of a new connection instead of reusing
        
    Returns:
        Redis connection instance
        
    Examples:
        >>> # Standalone connection
        >>> config = RedisConfig(host='localhost', port=6379)
        >>> redis_conn = get_redis_connection(config)
        
        >>> # Sentinel connection
        >>> config = RedisConfig(
        ...     connection_type=RedisConnectionType.SENTINEL,
        ...     sentinel_hosts=['sentinel1:26379', 'sentinel2:26379'],
        ...     sentinel_name='mymaster'
        ... )
        >>> redis_conn = get_redis_connection(config)
    """
    global _redis_connection, _redis_connection_raw
    
    # Use default config if none provided
    if config is None:
        config = RedisConfig()
    
    # Return cached connection if available and not forcing new
    if not force_new:
        if decode_responses and _redis_connection is not None:
            return _redis_connection
        elif not decode_responses and _redis_connection_raw is not None:
            return _redis_connection_raw
    
    # Create new connection based on type
    if config.connection_type == RedisConnectionType.SENTINEL:
        conn = _create_sentinel_connection(config, decode_responses)
    elif config.connection_type == RedisConnectionType.CLUSTER:
        conn = _create_cluster_connection(config, decode_responses)
    else:
        conn = _create_standalone_connection(config, decode_responses)
    
    # Cache the connection
    if not force_new:
        if decode_responses:
            _redis_connection = conn
        else:
            _redis_connection_raw = conn
    
    return conn


def _create_standalone_connection(config: RedisConfig, decode_responses: bool) -> Redis:
    """Create a standalone Redis connection."""
    logger.info(f"Creating standalone Redis connection to {config.host}:{config.port}")
    
    return Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        username=config.username,
        ssl=config.ssl,
        decode_responses=decode_responses,
        socket_timeout=config.socket_timeout,
        socket_connect_timeout=config.socket_connect_timeout,
        **config.extra_kwargs,
    )


def _create_sentinel_connection(config: RedisConfig, decode_responses: bool) -> Redis:
    """Create a Redis Sentinel connection."""
    if not config.sentinel_hosts:
        raise ValueError("sentinel_hosts must be provided for sentinel connection")
    if not config.sentinel_name:
        raise ValueError("sentinel_name must be provided for sentinel connection")
    
    logger.info(f"Creating Sentinel connection to {config.sentinel_name}")
    
    # Parse sentinel hosts
    hosts = []
    for host_str in config.sentinel_hosts:
        if ':' in host_str:
            host, port = host_str.split(':')
            hosts.append((host, int(port)))
        else:
            hosts.append((host_str, 26379))  # Default sentinel port
    
    # Create sentinel
    sentinel = Sentinel(
        hosts,
        socket_timeout=config.socket_timeout,
        password=config.password,
        sentinel_kwargs={"password": config.password} if config.password else {},
    )
    
    # Get master connection
    return sentinel.master_for(
        config.sentinel_name,
        socket_timeout=config.socket_timeout,
        password=config.password,
        db=config.db,
        decode_responses=decode_responses,
    )


def _create_cluster_connection(config: RedisConfig, decode_responses: bool) -> Any:
    """Create a Redis Cluster connection."""
    try:
        from rediscluster import RedisCluster
    except ImportError:
        raise ImportError(
            "redis-py-cluster is required for cluster support. "
            "Install it with: pip install redis-cache-toolkit[cluster]"
        )
    
    if not config.cluster_nodes:
        raise ValueError("cluster_nodes must be provided for cluster connection")
    
    logger.info(f"Creating Redis Cluster connection with {len(config.cluster_nodes)} nodes")
    
    return RedisCluster(
        startup_nodes=config.cluster_nodes,
        decode_responses=decode_responses,
        skip_full_coverage_check=True,
        password=config.password,
    )


def reset_connections() -> None:
    """
    Reset global Redis connections.
    
    Useful for testing or when configuration changes.
    """
    global _redis_connection, _redis_connection_raw
    _redis_connection = None
    _redis_connection_raw = None
    logger.info("Redis connections reset")

