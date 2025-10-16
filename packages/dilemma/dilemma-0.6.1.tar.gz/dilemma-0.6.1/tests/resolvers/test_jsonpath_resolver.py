"""Tests for JsonPathResolver implementation."""

import pytest
from dilemma.resolvers.jsonpath_resolver import JsonPathResolver
from dilemma.errors import VariableError


@pytest.fixture
def resolver():
    """Create a basic JsonPathResolver for testing."""
    return JsonPathResolver()


@pytest.fixture
def nested_data():
    """Create a nested data structure for testing."""
    return {
        "person": {
            "name": "John",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "Anytown"
            },
            "phones": [
                {"type": "home", "number": "555-1234"},
                {"type": "work", "number": "555-5678"}
            ]
        },
        "status": "active"
    }


def test_convert_path(resolver):
    """Test path conversion to jsonpath syntax."""
    assert resolver._convert_path("person.name") == "$.person.name"
    assert resolver._convert_path("$.person.name") == "$.person.name"


def test_resolve_simple_path(resolver, nested_data):
    """Test resolving a simple property path."""
    result = resolver.resolve_path("person.name", nested_data)
    assert result == "John"


def test_resolve_nested_path(resolver, nested_data):
    """Test resolving a nested property path."""
    result = resolver.resolve_path("person.address.city", nested_data)
    assert result == "Anytown"


def test_resolve_array_item(resolver, nested_data):
    """Test resolving an array item."""
    result = resolver.resolve_path("person.phones[0].number", nested_data)
    assert result == "555-1234"


def test_resolve_nonexistent_path(resolver, nested_data):
    """Test resolving a path that doesn't exist."""
    with pytest.raises(VariableError) as excinfo:
        resolver.resolve_path("person.email", nested_data)

    # Check that the error message contains the proper path
    assert "person.email" in str(excinfo.value)
    # Check that this is the expected error type by looking for parts of the message template
    assert "Lookup for a value matching" in str(excinfo.value)


def test_resolve_array_index(resolver, nested_data):
    """Test resolving an array with specific index."""
    result = resolver.resolve_path("person.phones[1].type", nested_data)
    assert result == "work"


def test_raw_expression_with_dot_prefix(resolver, nested_data):
    """Test resolving a raw expression that starts with dot."""
    result = resolver.resolve_path(".person.name", nested_data, raw=True)
    assert result == "John"


def test_raw_expression_with_dollar_prefix(resolver, nested_data):
    """Test resolving a raw expression that already has $ prefix."""
    result = resolver.resolve_path("$.status", nested_data, raw=True)
    assert result == "active"


def test_possessive_path_conversion(resolver):
    """Test handling of possessive paths."""
    assert resolver._convert_path("person's name") == "$.person.name"
