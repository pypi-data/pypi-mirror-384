"""
Tests for JSON data flattening functionality.
"""

import pytest
from embedding_model.data.flatten import flatten_to_text, flatten_pairs, _flatten_json, _to_str


class TestDataFlattening:
    """Test JSON flattening functions."""
    
    def test_simple_flat_object(self):
        """Test flattening a simple flat object."""
        obj = {"name": "John", "age": 30, "city": "NYC"}
        
        result = flatten_to_text(obj)
        
        # Should contain all key-value pairs
        assert "name: John" in result
        assert "age: 30" in result
        assert "city: NYC" in result
        
        # Should be separated by " | "
        parts = result.split(" | ")
        assert len(parts) == 3
    
    def test_nested_object(self):
        """Test flattening nested objects."""
        obj = {
            "user": {
                "name": "John",
                "details": {
                    "age": 30,
                    "city": "NYC"
                }
            }
        }
        
        result = flatten_to_text(obj)
        
        # Should flatten with dot notation
        assert "user.name: John" in result
        assert "user.details.age: 30" in result
        assert "user.details.city: NYC" in result
    
    def test_array_handling(self):
        """Test flattening objects with arrays."""
        obj = {
            "name": "Product",
            "tags": ["electronics", "laptop", "apple"]
        }
        
        result = flatten_to_text(obj)
        
        # Arrays should be indexed
        assert "name: Product" in result
        assert "tags.0: electronics" in result
        assert "tags.1: laptop" in result
        assert "tags.2: apple" in result
    
    def test_custom_separators(self):
        """Test custom separators."""
        obj = {"a": 1, "b": 2}
        
        result = flatten_to_text(
            obj,
            field_kv_sep=" = ",
            field_pair_sep=" & "
        )
        
        assert "a = 1" in result
        assert "b = 2" in result
        assert " & " in result
    
    def test_null_values(self):
        """Test handling of null values."""
        obj = {"name": "John", "middle": None, "age": 30}
        
        result = flatten_to_text(obj)
        
        assert "name: John" in result
        assert "middle: null" in result
        assert "age: 30" in result
    
    def test_flatten_pairs_function(self):
        """Test the flatten_pairs function."""
        obj = {"user": {"name": "John", "age": 30}}
        
        pairs = flatten_pairs(obj)
        
        # Should return sorted list of tuples
        assert isinstance(pairs, list)
        assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in pairs)
        
        # Check specific pairs
        pair_dict = dict(pairs)
        assert pair_dict["user.name"] == "John"
        assert pair_dict["user.age"] == "30"
    
    def test_to_str_function(self):
        """Test the _to_str helper function."""
        assert _to_str(None) == "null"
        assert _to_str(42) == "42"
        assert _to_str("hello") == "hello"
        assert _to_str(True) == "True"
    
    def test_complex_nested_structure(self):
        """Test a complex nested structure."""
        obj = {
            "product": {
                "name": "MacBook Pro",
                "specs": {
                    "cpu": "M2 Pro",
                    "ram": "16GB",
                    "storage": ["512GB", "1TB"]
                },
                "reviews": [
                    {"rating": 5, "comment": "Great!"},
                    {"rating": 4, "comment": "Good"}
                ]
            }
        }
        
        result = flatten_to_text(obj)
        
        # Check various nested paths
        assert "product.name: MacBook Pro" in result
        assert "product.specs.cpu: M2 Pro" in result
        assert "product.specs.storage.0: 512GB" in result
        assert "product.reviews.0.rating: 5" in result
        assert "product.reviews.1.comment: Good" in result
    
    def test_empty_object(self):
        """Test flattening an empty object."""
        result = flatten_to_text({})
        assert result == ""
    
    def test_single_value(self):
        """Test flattening a single key-value pair."""
        obj = {"key": "value"}
        result = flatten_to_text(obj)
        assert result == "key: value"
