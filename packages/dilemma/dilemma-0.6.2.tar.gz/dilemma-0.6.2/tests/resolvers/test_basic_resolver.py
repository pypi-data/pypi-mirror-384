"""Tests for BasicResolver implementation."""

import pytest
from dilemma.resolvers.basic_resolver import BasicResolver
from dilemma.errors import VariableError


@pytest.fixture
def resolver():
    """Create a basic BasicResolver for testing."""
    return BasicResolver()


@pytest.fixture
def simple_data():
    """Create a simple data structure for testing."""
    return {
        "name": "John",
        "age": 30,
        "status": "active",
        "is_admin": True,
        "score": 95.5,
        "tags": ["python", "testing"],
        "config": {"theme": "dark", "lang": "en"},
        "empty_value": None,
        "zero_value": 0,
        "false_value": False,
        "empty_string": "",
    }


def test_convert_path_no_conversion(resolver):
    """Test that path conversion returns the path unchanged."""
    assert resolver._convert_path("name") == "name"
    assert resolver._convert_path("nested.path") == "nested.path"
    assert resolver._convert_path("complex[0].path") == "complex[0].path"


def test_resolve_path_existing_key(resolver, simple_data):
    """Test resolving existing top-level keys."""
    assert resolver.resolve_path("name", simple_data) == "John"
    assert resolver.resolve_path("age", simple_data) == 30
    assert resolver.resolve_path("status", simple_data) == "active"
    assert resolver.resolve_path("is_admin", simple_data) is True
    assert resolver.resolve_path("score", simple_data) == 95.5


def test_resolve_path_nonexistent_key(resolver, simple_data):
    """Test resolving a key that doesn't exist."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("nonexistent", simple_data)
    
    assert "nonexistent" in str(excinfo.value)


def test_resolve_path_none_context(resolver):
    """Test resolving with None context."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("name", None)
    
    assert "name" in str(excinfo.value)


def test_resolve_path_non_dict_context(resolver):
    """Test resolving with non-dictionary context."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("name", "not a dict")
    
    assert "name" in str(excinfo.value)


def test_resolve_path_list_context(resolver):
    """Test resolving with list context."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("0", [1, 2, 3])
    
    assert "0" in str(excinfo.value)


def test_resolve_path_falsy_values(resolver, simple_data):
    """Test resolving keys with falsy values."""
    # The resolver treats None values as unresolved, so these should raise VariableError
    with pytest.raises(VariableError):
        resolver.resolve_path("empty_value", simple_data)
    
    # But other falsy values should work fine
    assert resolver.resolve_path("zero_value", simple_data) == 0
    assert resolver.resolve_path("false_value", simple_data) is False
    assert resolver.resolve_path("empty_string", simple_data) == ""


def test_resolve_path_complex_values(resolver, simple_data):
    """Test resolving keys with complex values."""
    assert resolver.resolve_path("tags", simple_data) == ["python", "testing"]
    assert resolver.resolve_path("config", simple_data) == {"theme": "dark", "lang": "en"}


def test_nested_path_not_supported(resolver, simple_data):
    """Test that nested paths are not supported and raise VariableError."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("config.theme", simple_data)
    
    assert "config.theme" in str(excinfo.value)


def test_array_access_not_supported(resolver, simple_data):
    """Test that array access is not supported and raises VariableError."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("tags[0]", simple_data)
    
    assert "tags[0]" in str(excinfo.value)


def test_raw_query_same_as_regular(resolver, simple_data):
    """Test that raw queries work the same as regular queries."""
    # Test existing key
    result = resolver._execute_raw_query("name", simple_data)
    assert result == "John"
    
    # Test non-existing key
    result = resolver._execute_raw_query("nonexistent", simple_data)
    assert result is None
    
    # Test None value - raw query should return None without raising error
    result = resolver._execute_raw_query("empty_value", simple_data)
    assert result is None


def test_execute_query_with_non_dict(resolver):
    """Test _execute_query with non-dictionary context."""
    result = resolver._execute_query("key", "not a dict")
    assert result is None
    
    result = resolver._execute_query("key", 123)
    assert result is None
    
    result = resolver._execute_query("key", [1, 2, 3])
    assert result is None


def test_execute_query_missing_key(resolver, simple_data):
    """Test _execute_query with missing key returns None."""
    result = resolver._execute_query("missing", simple_data)
    assert result is None


def test_execute_query_existing_key(resolver, simple_data):
    """Test _execute_query with existing key."""
    result = resolver._execute_query("name", simple_data)
    assert result == "John"


def test_execute_query_none_value(resolver, simple_data):
    """Test _execute_query with None value returns None."""
    result = resolver._execute_query("empty_value", simple_data)
    assert result is None


def test_empty_dict_context(resolver):
    """Test resolving with empty dictionary."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("any_key", {})
    
    assert "any_key" in str(excinfo.value)


def test_case_sensitive_keys(resolver):
    """Test that key lookup is case sensitive."""
    data = {"Name": "John", "name": "Jane"}
    
    assert resolver.resolve_path("Name", data) == "John"
    assert resolver.resolve_path("name", data) == "Jane"
    
    with pytest.raises(VariableError):
        resolver.resolve_path("NAME", data)


def test_numeric_string_keys(resolver):
    """Test resolving with numeric string keys."""
    data = {"0": "zero", "1": "one", "123": "one-two-three"}
    
    assert resolver.resolve_path("0", data) == "zero"
    assert resolver.resolve_path("1", data) == "one"
    assert resolver.resolve_path("123", data) == "one-two-three"


def test_special_character_keys(resolver):
    """Test resolving with special character keys."""
    data = {
        "key-with-dashes": "value1",
        "key_with_underscores": "value2",
        "key.with.dots": "value3",
        "key with spaces": "value4",
        "key@with#symbols": "value5",
    }
    
    assert resolver.resolve_path("key-with-dashes", data) == "value1"
    assert resolver.resolve_path("key_with_underscores", data) == "value2"
    assert resolver.resolve_path("key.with.dots", data) == "value3"
    assert resolver.resolve_path("key with spaces", data) == "value4"
    assert resolver.resolve_path("key@with#symbols", data) == "value5"


def test_unicode_keys(resolver):
    """Test resolving with unicode keys."""
    data = {
        "名前": "田中",
        "año": 2024,
        "🔑": "emoji_key",
        "café": "coffee",
    }
    
    assert resolver.resolve_path("名前", data) == "田中"
    assert resolver.resolve_path("año", data) == 2024
    assert resolver.resolve_path("🔑", data) == "emoji_key"
    assert resolver.resolve_path("café", data) == "coffee"


def test_direct_execute_query_usage(resolver, simple_data):
    """Test using _execute_query directly."""
    # Successful resolution
    assert resolver._execute_query("name", simple_data) == "John"
    assert resolver._execute_query("age", simple_data) == 30
    
    # Missing keys return None instead of raising exception
    assert resolver._execute_query("missing", simple_data) is None
    
    # Invalid context returns None
    assert resolver._execute_query("key", None) is None
    assert resolver._execute_query("key", "string") is None
    
    # None values also return None at the low level
    assert resolver._execute_query("empty_value", simple_data) is None


def test_difference_between_resolve_path_and_execute_query(resolver, simple_data):
    """Test the difference between high-level and low-level methods."""
    # High-level method raises exception for None values
    with pytest.raises(VariableError):
        resolver.resolve_path("empty_value", simple_data)
    
    # Low-level method returns None for None values
    assert resolver._execute_query("empty_value", simple_data) is None
    
    # Both work the same for valid values
    assert resolver.resolve_path("name", simple_data) == "John"
    assert resolver._execute_query("name", simple_data) == "John"
    
    # Both handle missing keys differently
    with pytest.raises(VariableError):
        resolver.resolve_path("missing", simple_data)
    
    assert resolver._execute_query("missing", simple_data) is None