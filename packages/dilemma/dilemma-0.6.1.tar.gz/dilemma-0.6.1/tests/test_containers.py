"""Tests for container (list and dictionary) operations in the expression language."""

import pytest
from dilemma.lang import evaluate, ExpressionTransformer
from dilemma.errors.exc import ContainerError, VariableError

def test_list_membership():
    """Test basic list membership operations."""
    variables = {
        "roles": ["admin", "editor", "viewer"],
        "numbers": [1, 2, 3, 4, 5],
        "empty_list": [],
    }

    # Testing 'in' operator
    assert evaluate("'admin' in roles", variables) is True
    assert evaluate("'manager' in roles", variables) is False
    assert evaluate("'editor' in roles", variables) is True

    # Testing 'contains' operator
    assert evaluate("roles contains 'viewer'", variables) is True
    assert evaluate("roles contains 'guest'", variables) is False

    # Testing with numbers
    assert evaluate("3 in numbers", variables) is True
    assert evaluate("6 in numbers", variables) is False
    assert evaluate("numbers contains 5", variables) is True

    # Testing with empty list
    assert evaluate("'anything' in empty_list", variables) is False
    assert evaluate("empty_list contains 'something'", variables) is False


def test_dict_membership():
    """Test dictionary key membership operations."""
    variables = {
        "user": {
            "name": "John Doe",
            "role": "admin",
            "settings": {"theme": "dark", "notifications": True},
        },
        "empty_dict": {},
    }

    # Testing 'in' operator (key existence)
    assert evaluate("'name' in user", variables) is True
    assert evaluate("'age' in user", variables) is False
    assert evaluate("'theme' in user.settings", variables) is True

    # Testing 'contains' operator
    assert evaluate("user contains 'role'", variables) is True
    assert evaluate("user contains 'email'", variables) is False
    assert evaluate("user.settings contains 'notifications'", variables) is True

    # Testing with empty dict
    assert evaluate("'key' in empty_dict", variables) is False
    assert evaluate("empty_dict contains 'value'", variables) is False


def test_mixed_container_types():
    """Test operations with mixed container types."""
    variables = {
        "data": {
            "tags": ["important", "urgent", "review"],
            "properties": {"color": "red", "priority": "high"},
        },
        "items": ["apple", "banana", {"type": "fruit"}],
        # Add a direct reference to the dictionary item for testing
        "fruit_object": {"type": "fruit"},
    }

    # Test accessing lists inside dicts
    assert evaluate("'urgent' in data.tags", variables) is True
    assert evaluate("data.tags contains 'review'", variables) is True

    # Test accessing dict properties without using array indexing
    assert evaluate("'type' in fruit_object", variables) is True


def test_collection_equality():
    """Test equality operations with collections."""
    variables = {
        "list1": [1, 2, 3],
        "list2": [1, 2, 3],
        "list3": [3, 2, 1],
        "dict1": {"a": 1, "b": 2},
        "dict2": {"b": 2, "a": 1},
        "dict3": {"a": 1, "c": 3},
    }

    # List equality
    assert evaluate("list1 == list2", variables) is True
    assert evaluate("list1 == list3", variables) is False
    assert evaluate("list1 != list3", variables) is True

    # Dict equality (order doesn't matter)
    assert evaluate("dict1 == dict2", variables) is True
    assert evaluate("dict1 != dict3", variables) is True


def test_container_type_errors():
    """Test ContainerError handling for container operations."""
    variables = {
        "number": 42,
        "string": "hello",
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"a": 1, "b": 2},
    }

    # These should raise ContainerError because the right operand is not a collection
    with pytest.raises(ContainerError, match="must be a collection"):
        evaluate("'test' in number", variables)

    # This should work (string contains)
    assert evaluate("'e' in string", variables) is True

    # This should fail (boolean is not a collection)
    with pytest.raises(ContainerError, match="must be a collection"):
        evaluate("'true' in boolean", variables)

    # These should raise ContainerError because the left operand is not a collection
    with pytest.raises(ContainerError, match="must be a collection"):
        evaluate("number contains 1", variables)

    # This should work (string contains)
    assert evaluate("string contains 'll'", variables) is True

    # This should fail
    with pytest.raises(ContainerError, match="must be a collection"):
        evaluate("boolean contains 'r'", variables)



def test_direct_transformer_methods():
    """Test ExpressionTransformer methods directly to ensure coverage."""
    transformer = ExpressionTransformer()

    # Test contains with list
    assert transformer.contains(["key", ["value1", "value2", "key"]]) is True

    # Test contains with dict
    assert transformer.contains(["key", {"key": "value", "other": 123}]) is True

    # Test contained_in with list
    assert transformer.contained_in([["value1", "value2", "key"], "key"]) is True

    # Test contained_in with dict
    assert transformer.contained_in([{"key": "value", "other": 123}, "key"]) is True

    # Test with non-collection types (these should raise ContainerError)
    with pytest.raises(ContainerError):
        transformer.contains([42, 100])

    with pytest.raises(ContainerError):
        transformer.contained_in([42, "test"])


def test_datetime_in_collections():
    """Test handling of datetime objects in collections."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    variables = {
        "dates": [yesterday, now, tomorrow],
        "event": {"start": yesterday, "end": tomorrow},
    }

    # Test datetime comparisons in lists
    # Need to use a datetime that would serialize/deserialize correctly
    iso_now = now.isoformat()
    assert (
        evaluate(f"'{iso_now}' in dates", variables) is False
    )  # String comparison won't match

    # Test access to datetime in dict
    assert evaluate("event.start is $past", variables) is True
    assert evaluate("event.end is $future", variables) is True


def test_complex_nested_structures():
    """Test complex nested data structures with mixed types."""
    variables = {
        "organization": {
            "name": "Acme Corp",
            "departments": [
                {
                    "name": "Engineering",
                    "teams": [
                        {"name": "Frontend", "members": ["Alice", "Bob"]},
                        {"name": "Backend", "members": ["Charlie", "Dave"]},
                    ],
                },
                {
                    "name": "Marketing",
                    "teams": [{"name": "Digital", "members": ["Eve", "Frank"]}],
                },
            ],
        },
        # Add direct references to the nested objects for testing
        "frontend_team": {"name": "Frontend", "members": ["Alice", "Bob"]},
        "marketing_team": {"name": "Digital", "members": ["Eve", "Frank"]},
        "marketing_dept": {"name": "Marketing"},
    }

    # Test with directly referenced objects instead of array indexes
    assert evaluate("'Bob' in frontend_team.members", variables) is True
    assert evaluate("marketing_team.members contains 'Eve'", variables) is True

    # Test composite conditions with direct object references
    complex_expr = (
        "'Marketing' in marketing_dept.name and 'Frank' in marketing_team.members"
    )
    assert evaluate(complex_expr, variables) is True


def test_empty_containers():
    """Test the 'is $empty' operation for checking empty containers."""
    variables = {
        "empty_list": [],
        "filled_list": [1, 2, 3],
        "empty_dict": {},
        "filled_dict": {"a": 1, "b": 2},
        "string": "hello",
        "number": 42,
        "boolean": True,
    }

    # Test with empty containers
    assert evaluate("empty_list is $empty", variables) is True
    assert evaluate("empty_dict is $empty", variables) is True

    # Test with non-empty containers
    assert evaluate("filled_list is $empty", variables) is False
    assert evaluate("filled_dict is $empty", variables) is False

    # Test with non-container types (should raise ContainerError)
    with pytest.raises(ContainerError, match="can only be used with container types"):
        evaluate("string is $empty", variables)

    with pytest.raises(ContainerError, match="can only be used with container types"):
        evaluate("number is $empty", variables)

    with pytest.raises(ContainerError, match="can only be used with container types"):
        evaluate("boolean is $empty", variables)

    # Test with complex expressions - using valid syntax
    assert evaluate("empty_list is $empty and empty_dict is $empty", variables) is True
    assert evaluate("filled_list is $empty or empty_list is $empty", variables) is True
    assert evaluate("(filled_dict is $empty) == false", variables) is True
