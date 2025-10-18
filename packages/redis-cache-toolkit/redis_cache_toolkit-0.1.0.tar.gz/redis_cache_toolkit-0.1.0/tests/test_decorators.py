"""Tests for caching decorators."""
import time
import pytest
from redis_cache_toolkit.decorators import (
    cached,
    cached_model,
    capture_exception_decorator,
    dont_unpack_list,
    default_positive_int,
)


class TestCachedDecorator:
    """Tests for @cached decorator."""
    
    def test_basic_caching(self, redis_conn, redis_config):
        """Test basic function result caching."""
        call_count = 0
        
        @cached(timeout=60, redis_config=redis_config)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call - should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented
        
        # Different argument - should execute function
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2
    
    def test_cache_expiration(self, redis_conn, redis_config):
        """Test that cache expires after timeout."""
        call_count = 0
        
        @cached(timeout=1, redis_config=redis_config)
        def short_lived_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = short_lived_function(5)
        assert call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        result2 = short_lived_function(5)
        assert call_count == 2  # Function called again
    
    def test_typed_caching(self, redis_conn, redis_config):
        """Test typed argument caching."""
        call_count = 0
        
        @cached(timeout=60, typed=True, redis_config=redis_config)
        def typed_function(x):
            nonlocal call_count
            call_count += 1
            return str(x)
        
        # Call with int
        result1 = typed_function(5)
        assert call_count == 1
        
        # Call with same int - should use cache
        result2 = typed_function(5)
        assert call_count == 1
        
        # Call with float - should execute function due to different type
        result3 = typed_function(5.0)
        assert call_count == 2
    
    def test_custom_key_prefix(self, redis_conn, redis_config):
        """Test custom cache key prefix."""
        @cached(timeout=60, key_prefix="custom", redis_config=redis_config)
        def custom_prefix_function(x):
            return x * 2
        
        result = custom_prefix_function(5)
        
        # Check that key exists with custom prefix
        keys = redis_conn.keys("cache:custom:*")
        assert len(keys) > 0
    
    def test_kwargs_caching(self, redis_conn, redis_config):
        """Test caching with keyword arguments."""
        call_count = 0
        
        @cached(timeout=60, redis_config=redis_config)
        def kwargs_function(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y
        
        result1 = kwargs_function(5)
        assert result1 == 15
        assert call_count == 1
        
        result2 = kwargs_function(5)
        assert call_count == 1  # Cached
        
        result3 = kwargs_function(5, y=20)
        assert result3 == 25
        assert call_count == 2  # Different kwargs


class TestCachedModelDecorator:
    """Tests for @cached_model decorator."""
    
    def test_pydantic_model_caching(self, redis_conn, redis_config):
        """Test caching with Pydantic model validation."""
        pytest.importorskip("pydantic")
        from pydantic import BaseModel
        
        class User(BaseModel):
            id: int
            name: str
            email: str
        
        call_count = 0
        
        @cached_model(User, timeout=60, redis_config=redis_config)
        def get_user(user_id):
            nonlocal call_count
            call_count += 1
            return {
                "id": user_id,
                "name": "John Doe",
                "email": "john@example.com"
            }
        
        # First call
        user1 = get_user(1)
        assert isinstance(user1, User)
        assert user1.id == 1
        assert user1.name == "John Doe"
        assert call_count == 1
        
        # Second call - from cache
        user2 = get_user(1)
        assert isinstance(user2, User)
        assert call_count == 1
    
    def test_validation_error_handling(self, redis_conn, redis_config):
        """Test handling of validation errors."""
        pytest.importorskip("pydantic")
        from pydantic import BaseModel
        
        class StrictUser(BaseModel):
            id: int
            name: str
        
        @cached_model(StrictUser, timeout=60, redis_config=redis_config, return_none_on_error=True)
        def get_invalid_user(user_id):
            return {"id": "not_an_int", "name": "John"}  # Invalid id type
        
        result = get_invalid_user(1)
        assert result is None  # Should return None on validation error


class TestUtilityDecorators:
    """Tests for utility decorators."""
    
    def test_capture_exception_decorator(self):
        """Test exception capturing."""
        @capture_exception_decorator(fallback_value="error", log_errors=False)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "error"
    
    def test_dont_unpack_list(self):
        """Test list unpacking decorator."""
        @dont_unpack_list
        def return_list():
            return [1, 2, 3]
        
        result = return_list()
        assert result == 1
        
        @dont_unpack_list
        def return_single():
            return 42
        
        result2 = return_single()
        assert result2 == 42
    
    def test_default_positive_int(self):
        """Test default positive int decorator."""
        @default_positive_int
        def return_none():
            return None
        
        result = return_none()
        assert result == 1
        
        @default_positive_int
        def return_zero():
            return 0
        
        result2 = return_zero()
        assert result2 == 1
        
        @default_positive_int
        def return_five():
            return 5
        
        result3 = return_five()
        assert result3 == 5

