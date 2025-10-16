"""Tests for JqResolver implementation."""

import pytest
from unittest.mock import patch, MagicMock


# Test ImportError handling
def test_import_error_when_jq_not_available():
    """Test that ImportError is raised when jq module is not available."""
    with patch.dict('sys.modules', {'jq': None}):
        with pytest.raises(ImportError) as excinfo:
            # This will trigger the import and raise the ImportError
            import importlib
            import sys
            if 'dilemma.resolvers.jq_resolver' in sys.modules:
                del sys.modules['dilemma.resolvers.jq_resolver']
            importlib.import_module('dilemma.resolvers.jq_resolver')
        
        assert "The jq library is not available" in str(excinfo.value)
        assert "pip install jq" in str(excinfo.value)


# Assuming jq is available for the rest of the tests
@pytest.fixture
def resolver():
    """Create a JqResolver for testing."""
    from dilemma.resolvers.jq_resolver import JqResolver
    return JqResolver()


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
        "status": "active",
        "scores": [85, 92, 78],
        "metadata": {
            "created": "2024-01-01",
            "tags": ["important", "user"]
        }
    }


def test_execute_query_simple_identifier(resolver, nested_data):
    """Test _execute_query with simple identifier paths."""
    # Test simple key lookup for dict - this uses the fast path
    result = resolver._execute_query("status", nested_data)
    assert result == "active"
    
    # Test missing key - this should raise KeyError based on the implementation
    with pytest.raises(KeyError):
        resolver._execute_query("missing", nested_data)


def test_execute_query_with_dot_prefix(resolver, nested_data):
    """Test _execute_query with paths that need dot prefix added."""
    # Test path without dot prefix - triggers line 33 (else branch)
    result = resolver._execute_query("person.name", nested_data)
    assert result == "John"


def test_execute_query_empty_results(resolver, nested_data):
    """Test _execute_query when jq returns empty results."""
    # Test query that returns no results - triggers "return None"
    # Using 'empty' which produces zero outputs, not null
    result = resolver._execute_query(".[] | select(false)", nested_data)
    assert result is None


def test_execute_raw_query_empty_results(resolver, nested_data):
    """Test _execute_raw_query when jq returns empty results."""
    # Test raw query that returns no results - triggers line 53
    result = resolver._execute_raw_query("empty", nested_data)
    assert result is None

