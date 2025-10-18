"""Tests for helper utilities."""
import pytest
from redis_cache_toolkit.helpers import (
    make_cache_key,
    check_is_identifiable_object,
    parse_identifiable_object,
    serialize_for_cache,
    deserialize_from_cache,
)


class MockModel:
    """Mock model for testing object identifier extraction."""
    def __init__(self, id_value):
        self.id = id_value


class TestMakeCacheKey:
    """Tests for cache key generation."""
    
    def test_simple_args(self):
        """Test cache key generation with simple arguments."""
        key1 = make_cache_key((1, 2, 3), {})
        key2 = make_cache_key((1, 2, 3), {})
        assert key1 == key2
        
        key3 = make_cache_key((1, 2, 4), {})
        assert key1 != key3
    
    def test_with_kwargs(self):
        """Test cache key generation with keyword arguments."""
        key1 = make_cache_key((1,), {"x": 10, "y": 20})
        key2 = make_cache_key((1,), {"x": 10, "y": 20})
        assert key1 == key2
        
        # Different kwargs
        key3 = make_cache_key((1,), {"x": 10, "y": 30})
        assert key1 != key3
    
    def test_typed_keys(self):
        """Test typed cache key generation."""
        key1 = make_cache_key((5,), {}, typed=True)
        key2 = make_cache_key((5.0,), {}, typed=True)
        assert key1 != key2  # Different types
        
        key3 = make_cache_key((5,), {}, typed=False)
        key4 = make_cache_key((5.0,), {}, typed=False)
        # May or may not be equal depending on hash
    
    def test_single_fasttype(self):
        """Test optimization for single fast-type argument."""
        key = make_cache_key((42,), {})
        assert key == 42  # Returns value directly for single int
        
        key = make_cache_key(("hello",), {})
        assert key == "hello"  # Returns value directly for single str
    
    def test_identifiable_objects(self):
        """Test cache key with objects having id attribute."""
        obj1 = MockModel(123)
        obj2 = MockModel(123)
        
        key1 = make_cache_key((), {"obj": obj1})
        key2 = make_cache_key((), {"obj": obj2})
        # Should generate same key for objects with same id
        assert key1 == key2
        
        obj3 = MockModel(456)
        key3 = make_cache_key((), {"obj": obj3})
        assert key1 != key3


class TestObjectIdentifiers:
    """Tests for object identifier utilities."""
    
    def test_check_identifiable_object(self):
        """Test checking if object has identifier."""
        obj = MockModel(123)
        assert check_is_identifiable_object(obj) is True
        
        assert check_is_identifiable_object(42) is False
        assert check_is_identifiable_object("string") is False
    
    def test_parse_identifiable_object(self):
        """Test extracting identifier from object."""
        obj = MockModel(123)
        identifier = parse_identifiable_object(obj)
        assert identifier == 123


class TestSerialization:
    """Tests for cache serialization."""
    
    def test_serialize_deserialize_primitives(self):
        """Test serialization of primitive types."""
        # Integer
        data = 42
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
        
        # String
        data = "hello world"
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
        
        # Float
        data = 3.14159
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
    
    def test_serialize_deserialize_collections(self):
        """Test serialization of collections."""
        # List
        data = [1, 2, 3, "four", 5.0]
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
        
        # Dict
        data = {"a": 1, "b": 2, "nested": {"c": 3}}
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
        
        # Tuple
        data = (1, 2, 3)
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
    
    def test_serialize_deserialize_complex_objects(self):
        """Test serialization of complex objects."""
        data = {
            "id": 123,
            "name": "Test",
            "items": [1, 2, 3],
            "nested": {
                "key": "value",
                "list": ["a", "b", "c"]
            },
            "tuple": (1, 2, 3),
            "float": 3.14
        }
        
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized == data
    
    def test_serialize_none(self):
        """Test serialization of None."""
        data = None
        serialized = serialize_for_cache(data)
        deserialized = deserialize_from_cache(serialized)
        assert deserialized is None

