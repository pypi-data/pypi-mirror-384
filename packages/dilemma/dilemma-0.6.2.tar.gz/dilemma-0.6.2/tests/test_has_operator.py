"""Tests for the 'has' property existence operator in the expression language."""

from dilemma.lang import evaluate


def test_has_operator_basic_dict():
    """Test basic 'has' operator with dictionary objects."""
    variables = {
        "user": {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
        },
        "empty_dict": {},
    }

    # Test with string literals
    assert evaluate("user has 'name'", variables) is True
    assert evaluate("user has 'email'", variables) is True
    assert evaluate("user has 'phone'", variables) is False

    # Test with empty dictionary
    assert evaluate("empty_dict has 'anything'", variables) is False


def test_has_operator_with_variables():
    """Test 'has' operator using variables for property names."""
    variables = {
        "user": {
            "username": "johndoe",
            "password": "secret",
            "settings": {"theme": "dark"},
        },
        "property_name": "username",
        "missing_property": "email",
    }

    # Test using variable as property name
    assert evaluate("user has property_name", variables) is True
    assert evaluate("user has missing_property", variables) is False

    # Test with nested objects
    assert evaluate("user.settings has 'theme'", variables) is True


def test_has_operator_with_lists():
    """Test 'has' operator with list objects."""
    variables = {
        "tags": ["important", "urgent", "review"],
        "numbers": [1, 2, 3, 4, 5],
        "empty_list": [],
    }

    # For lists, 'has' should check for item existence (like 'contains')
    assert evaluate("tags has 'important'", variables) is True
    assert evaluate("tags has 'missing'", variables) is False
    assert evaluate("numbers has 3", variables) is True
    assert evaluate("numbers has 10", variables) is False

    # Test with empty list
    assert evaluate("empty_list has 'anything'", variables) is False


def test_has_operator_with_nested_objects():
    """Test 'has' operator with complex nested structures."""
    variables = {
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"username": "admin", "password": "secret"},
            },
            "features": {"authentication": True, "logging": True},
        }
    }

    # Test nested property access
    assert evaluate("config has 'database'", variables) is True
    assert evaluate("config.database has 'host'", variables) is True
    assert evaluate("config.database has 'ssl'", variables) is False
    assert evaluate("config.database.credentials has 'username'", variables) is True
    assert evaluate("config.features has 'authentication'", variables) is True


def test_has_operator_with_combined_conditions():
    """Test 'has' operator combined with other logical operators."""
    variables = {
        "user": {
            "name": "Alice",
            "email": "alice@example.com",
            "profile": {"bio": "Software developer", "avatar": "avatar.jpg"},
        },
        "required_fields": ["name", "email"],
    }

    # Test with logical AND
    assert evaluate("user has 'name' and user has 'email'", variables) is True
    assert evaluate("user has 'name' and user has 'phone'", variables) is False

    # Test with logical OR
    assert evaluate("user has 'phone' or user has 'email'", variables) is True
    assert evaluate("user has 'phone' or user has 'fax'", variables) is False

    # Test with nested access and logical operators
    complex_expr = (
        "user has 'profile' and user.profile has 'bio' and " "user.profile has 'avatar'"
    )
    assert evaluate(complex_expr, variables) is True


def test_has_operator_with_non_dict_types():
    """Test 'has' operator with non-dictionary types."""
    variables = {
        "number": 42,
        "string": "hello world",
        "boolean": True,
        "empty_string": "",
    }

    # Non-dict types should return False for property checks
    assert evaluate("number has 'toString'", variables) is False
    assert evaluate("string has 'length'", variables) is False
    assert evaluate("boolean has 'value'", variables) is False
    assert evaluate("empty_string has 'anything'", variables) is False


def test_has_operator_with_mixed_expressions():
    """Test 'has' operator in complex expressions with other operators."""
    variables = {
        "users": [
            {"name": "Alice", "role": "admin", "active": True},
            {"name": "Bob", "role": "user", "active": False},
            {"name": "Charlie", "role": "user", "active": True},
        ],
        "admin_user": {"name": "Alice", "role": "admin", "active": True},
    }

    # Combine 'has' with membership tests
    assert evaluate("'role' in admin_user and admin_user has 'name'", variables) is True

    # Test with equality comparisons
    expr1 = "admin_user has 'role' and admin_user.role == 'admin'"
    assert evaluate(expr1, variables) is True
    expr2 = "admin_user has 'status' or admin_user.role == 'admin'"
    assert evaluate(expr2, variables) is True


def test_has_operator_readability_examples():
    """Test examples that demonstrate the readability improvement of 'has' operator."""
    variables = {
        "customer": {
            "personal_info": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
            },
            "preferences": {
                "newsletter": True,
                "notifications": {"email": True, "sms": False},
            },
            "account": {"premium": True, "credits": 100},
        }
    }

    # These expressions read more naturally than "'email' in customer.personal_info"
    assert evaluate("customer.personal_info has 'email'", variables) is True
    assert evaluate("customer.preferences has 'newsletter'", variables) is True
    assert evaluate("customer.account has 'premium'", variables) is True
    assert evaluate("customer.preferences.notifications has 'email'", variables) is True

    # Test some missing properties
    assert evaluate("customer has 'billing_address'", variables) is False
    assert evaluate("customer.account has 'expiration_date'", variables) is False


def test_has_operator_error_cases():
    """Test edge cases and potential error scenarios."""
    variables = {
        "data": {"key": "value"},
        "list_data": [1, 2, 3],
    }

    # These should work without errors, returning False
    assert evaluate("data has ''", variables) is False  # Empty string key
    assert evaluate("list_data has ''", variables) is False  # Empty string in list

    # Test with complex key expressions
    key_var = "computed_key"
    variables["key_name"] = key_var
    assert evaluate("data has key_name", variables) is False  # key doesn't exist


def test_has_vs_in_operator_comparison():
    """Compare 'has' operator with existing 'in' operator for clarity."""
    variables = {
        "user": {"name": "John", "settings": {"theme": "dark", "language": "en"}}
    }

    # Both should work the same way, but 'has' reads more naturally
    # Traditional 'in' syntax: property in object
    assert evaluate("'name' in user", variables) is True
    assert evaluate("'email' in user", variables) is False

    # New 'has' syntax: object has property (more natural)
    assert evaluate("user has 'name'", variables) is True
    assert evaluate("user has 'email'", variables) is False

    # Both should give same results
    in_result = evaluate("'theme' in user.settings", variables)
    has_result = evaluate("user.settings has 'theme'", variables)
    assert in_result == has_result

    in_missing = evaluate("'missing' in user.settings", variables)
    has_missing = evaluate("user.settings has 'missing'", variables)
    assert in_missing == has_missing
