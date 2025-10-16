import threading

import pytest

from dilemma.lang import (
    evaluate,
    MAX_STRING_LENGTH,
    ExpressionTransformer,
    compile_expression,
)
from dilemma.errors import DilemmaError, VariableError, TypeMismatchError


def test_specific_cases():
    """Test specific edge cases"""
    test_cases = [
        # Basic integers
        ("0", 0),
        ("1", 1),
        ("42", 42),
        # Addition
        ("1 + 2", 3.0),
        ("5 + 10", 15.0),
        ("0 + 0", 0.0),
        # Subtraction
        ("5 - 2", 3.0),
        ("10 - 5", 5.0),
        ("10 - 5 + 3", 8.0),
        ("1 + 2 + 3", 6.0),
        ("10 - 5 - 3", 2.0),
        # Multiplication tests
        ("3 * 4", 12.0),
        ("0 * 5", 0.0),
        ("5 * 0", 0.0),
        ("1 * 42", 42.0),
        # Division tests
        ("10 / 2", 5.0),
        ("9 / 3", 3.0),
        ("8 / 4", 2.0),
        ("7 / 2", 3.5),  # Float division
        ("100 / 1", 100.0),
        # Combined operations with precedence
        ("2 + 3 * 4", 14.0),
        ("2 * 3 + 4", 10.0),
        ("10 - 2 * 3", 4.0),
        ("10 / 2 + 3", 8.0),
        ("10 + 20 / 5", 14.0),
        ("10 * 2 / 4", 5.0),
        ("20 / 4 * 2", 10.0),
        # Complex expressions
        ("1 + 2 * 3 + 4", 11.0),
        ("10 / 2 + 3 * 4", 17.0),
        ("1 + 2 + 3 * 4", 15.0),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_division_by_zero():
    """Test that division by zero raises an error"""
    with pytest.raises(DilemmaError):
        evaluate("5 / 0")


# Add a test for triggering other VisitErrors
class CustomTransformer(ExpressionTransformer):
    def mul(self, items):
        # Intentionally raise a custom error for testing
        raise ValueError("Custom error for testing")


def test_other_visit_errors(monkeypatch):
    """Test that other VisitErrors are properly handled"""

    # Create an instance of our custom transformer
    custom_transformer = CustomTransformer()

    # Keep the original function to restore later
    original_transform = ExpressionTransformer.transform

    # Replace the transform method on the ExpressionTransformer class
    def mock_transform(self, tree):
        if self.__class__ == ExpressionTransformer:
            return custom_transformer.transform(tree)
        return original_transform(self, tree)

    # Apply the monkeypatch to the class method
    monkeypatch.setattr(ExpressionTransformer, "transform", mock_transform)

    with pytest.raises(DilemmaError) as excinfo:
        evaluate("3 * 4")

    # Check that the error message contains the expression
    assert "3 * 4" in str(excinfo.value)


def test_comparison_operators():
    """Test comparison operators"""
    test_cases = [
        # Equality
        ("5 == 5", True),
        ("5 == 6", False),
        ("10 == 10", True),
        # Inequality
        ("5 != 5", False),
        ("5 != 6", True),
        ("10 != 20", True),
        # Less than
        ("5 < 10", True),
        ("10 < 5", False),
        ("5 < 5", False),
        # Greater than
        ("10 > 5", True),
        ("5 > 10", False),
        ("5 > 5", False),
        # Less than or equal
        ("5 <= 10", True),
        ("10 <= 5", False),
        ("5 <= 5", True),
        # Greater than or equal
        ("10 >= 5", True),
        ("5 >= 10", False),
        ("5 >= 5", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_comparison_with_arithmetic():
    """Test comparison operators combined with arithmetic operations"""
    test_cases = [
        # Arithmetic on both sides
        ("2 + 3 == 5", True),
        ("2 + 3 == 6", False),
        ("10 - 5 != 3", True),
        # With operator precedence
        ("2 + 3 * 2 == 8", True),
        ("2 + 3 * 2 != 11", True),
        ("10 - 2 * 3 < 5", True),  # 10 - 6 = 4.0, and 4.0 < 5 is True
        ("10 - 2 * 3 <= 4", True),  # 10 - 6 = 4.0, and 4.0 <= 4 is True
        # With division
        ("10 / 2 == 5", True),
        ("7 / 2 == 3.5", True),  # Float division
        ("20 / 4 > 3", True),
        ("20 / 4 < 6", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_thread_safety():
    def worker(expression, results, index):
        results[index] = evaluate(expression)

    expressions = ["1 + 1", "2 * 3", "4 / 2"]
    results = [None] * len(expressions)
    threads = []

    for i, expr in enumerate(expressions):
        thread = threading.Thread(target=worker, args=(expr, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert results == [2, 6, 2.0]


def test_variables_processing_json_error(monkeypatch):
    """Test that errors during JSON processing raise the appropriate error"""
    import json
    import dilemma.lang

    # Create a mock json.dumps that raises an error
    original_dumps = json.dumps

    def mock_dumps(*args, **kwargs):
        # Only raise the error for our specific test case
        if args and isinstance(args[0], dict) and "trigger_error" in args[0]:
            raise TypeError("Mock JSON processing error")
        return original_dumps(*args, **kwargs)

    # Apply the monkeypatch
    monkeypatch.setattr(json, "dumps", mock_dumps)

    # Test that the error path in ExpressionTransformer.__init__ is triggered
    with pytest.raises(DilemmaError) as excinfo:
        evaluate("1 + 1", context={"trigger_error": "value"})

    # Check the error message matches what we expect
    assert "Failed to process variables" in str(excinfo.value)
    assert "Mock JSON processing error" in str(excinfo.value)


def test_compiled_expression():
    """Test that compiled expressions work correctly"""

    # Compile the expression
    expr = compile_expression("x + y * 2")

    # Test with different variable contexts
    variables1 = {"x": 1, "y": 2}
    variables2 = {"x": 10, "y": 5}

    assert expr.evaluate(variables1) == 5.0  # 1 + 2*2 = 5
    assert expr.evaluate(variables2) == 20.0  # 10 + 5*2 = 20


def test_compiled_expression_with_path_variables():
    """Test that compiled expressions work with path variables"""

    # Compile an expression with paths
    expr = compile_expression("project.status == 'active' and project.team.size >= 3")

    # Test with different variable contexts
    variables1 = {"project": {"status": "active", "team": {"size": 5}}}
    variables2 = {"project": {"status": "active", "team": {"size": 2}}}
    variables3 = {"project": {"status": "inactive", "team": {"size": 10}}}

    assert expr.evaluate(variables1)  # active and size(5) >= 3
    assert expr.evaluate(variables2) == False  # active but size(2) < 3
    assert expr.evaluate(variables3) == False  # inactive and size(10) >= 3


def test_compiled_expression_error_handling():
    """Test that compiled expressions handle errors correctly"""

    # Compile an expression
    expr = compile_expression("x / y")

    # Test division by zero error
    variables = {"x": 10, "y": 0}
    with pytest.raises(DilemmaError):
        expr.evaluate(variables)

    # Test missing variable error
    variables = {"x": 10}  # Missing y
    with pytest.raises(DilemmaError):
        expr.evaluate(variables)


def test_jq_expressions():
    """Test that JQ expressions work correctly"""
    # Test data
    variables = {
        "users": [
            {"name": "Alice", "roles": ["admin", "user"]},
            {"name": "Bob", "roles": ["user"]},
        ],
        "settings": {"features": {"advanced": True, "beta": False}},
    }

    # Test expressions with angle bracket syntax
    expressions = [
        # Basic JQ expressions
        ('`.users[0].name` == "Alice"', True),
        ('`.users[1].name` == "Bob"', True),
        # Array access
        ('`.users[0].roles[0]` == "admin"', True),
        # Nested property access
        ("`.settings.features.advanced`", True),
        ("`.settings.features.beta`", False),
        # JQ expressions in complex conditions
        ('`.users[0].roles` contains "admin" and `.settings.features.advanced`', True),
        ('`.users[1].roles` contains "admin" or `.settings.features.beta`', False),
        # Mixed with regular variable paths
        ("users[0].name == `.users[0].name`", True),
    ]

    for expr, expected in expressions:
        assert evaluate(expr, variables) == expected


def test_jq_expression_errors():
    """Test error handling for JQ expressions"""
    variables = {"user": {"name": "Alice"}}

    # Invalid JQ syntax
    with pytest.raises(VariableError) as excinfo:
        evaluate("`invalid[syntax`", variables)

    # Empty JQ expression
    with pytest.raises(VariableError) as excinfo:
        evaluate("``", variables)


def test_valid_string_concatenation():
    """Test valid string concatenation operations"""
    test_cases = [
        ("'hello' + ' world'", "hello world"),
        ("'a' + 'b' + 'c'", "abc"),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


@pytest.mark.parametrize(
    "expr,error_type,error_msg",
    [
        # String length limit test
        (
            f"'{'a' * (MAX_STRING_LENGTH // 2)}' + '{'b' * (MAX_STRING_LENGTH // 2 + 1)}'",
            TypeMismatchError,
            "String result exceeds maximum allowed length",
        ),
        # Mixing strings with other types
        (
            "'hello' + 5",
            TypeMismatchError,
            "'+' operator cannot mix string and non-string types",
        ),
        (
            "5 + 'hello'",
            TypeMismatchError,
            "'+' operator cannot mix string and non-string types",
        ),
        # Subtraction with strings
        (
            "'hello' - 'h'",
            TypeMismatchError,
            "'-' operator not supported with string operands",
        ),
        (
            "'hello' - 5",
            TypeMismatchError,
            "'-' operator not supported with string operands",
        ),
        # Multiplication with strings
        (
            "'hello' * 3",
            TypeMismatchError,
            "'*' operator not supported with string operands",
        ),
        (
            "3 * 'hello'",
            TypeMismatchError,
            "'*' operator not supported with string operands",
        ),
        # Division with strings
        (
            "'hello' / 'h'",
            TypeMismatchError,
            "'/' operator not supported with string operands",
        ),
        (
            "'hello' / 5",
            TypeMismatchError,
            "'/' operator not supported with string operands",
        ),
    ],
)
def test_string_math_restrictions(expr, error_type, error_msg):
    """Test restrictions on mathematical operations with strings"""
    with pytest.raises(error_type) as excinfo:
        evaluate(expr)
    assert error_msg in str(excinfo.value)


def test_pattern_matching_type_error():
    """Test that pattern matching with non-string operands raises appropriate error"""
    # Test cases where pattern matching is used with non-string types
    test_cases = [
        "5 like 10",  # both integers
        "true like 'pattern'",  # boolean like string
        "'text' like 42",  # string like integer
        "3.14 like '*'",  # float like pattern
    ]

    for expr in test_cases:
        with pytest.raises(DilemmaError) as excinfo:
            evaluate(expr)
        # Should contain the TypeError message wrapped in VisitError/EvaluationError
        assert "Pattern matching requires string operands" in str(excinfo.value)


def test_possesive_lookup():
    expr = "user's name =='bob'"
    context = {"user": {"name": "bob"}}
    assert evaluate(expr, context) is True
