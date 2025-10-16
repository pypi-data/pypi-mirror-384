"""Tests for ProcessedContext functionality"""

import pytest

from dilemma.lang import evaluate, compile_expression, ProcessedContext
from dilemma.errors import DilemmaError


def test_basic_processed_context_creation():
    """Test creating a ProcessedContext with various input types."""
    # Test with dictionary
    data = {"name": "Alice", "age": 30}
    ctx = ProcessedContext(data)
    assert ctx.get_processed_json() == data

    # Test with None
    ctx_none = ProcessedContext(None)
    assert ctx_none.get_processed_json() == {}

    # Test with JSON string
    json_str = '{"name": "Bob", "age": 25}'
    ctx_json = ProcessedContext(json_str)
    assert ctx_json.get_processed_json() == {"name": "Bob", "age": 25}


def test_evaluate_with_processed_context():
    """Test using ProcessedContext with the evaluate function."""
    data = {"user": {"name": "Alice", "age": 30}, "threshold": 25}
    ctx = ProcessedContext(data)

    # Test various expressions
    assert evaluate("user.name == 'Alice'", ctx) is True
    assert evaluate("user.age > threshold", ctx) is True
    assert evaluate("user.age < threshold", ctx) is False


def test_compiled_expression_with_processed_context():
    """Test using ProcessedContext with CompiledExpression."""
    expr = compile_expression("user.age > threshold and user.name == 'Alice'")

    # Different contexts
    ctx1 = ProcessedContext({"user": {"name": "Alice", "age": 30}, "threshold": 25})
    ctx2 = ProcessedContext({"user": {"name": "Bob", "age": 20}, "threshold": 25})

    assert expr.evaluate(ctx1) is True
    assert expr.evaluate(ctx2) is False


def test_processed_context_reuse():
    """Test that ProcessedContext can be reused across multiple evaluations."""
    data = {
        "items": [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20},
            {"name": "item3", "value": 30},
        ]
    }
    ctx = ProcessedContext(data)

    # Multiple expressions using the same context
    expressions = [
        ("items[0].value", 10),
        ("items[1].name", "item2"),
        ("items[2].value > 25", True),
        ("items[0].value + items[1].value", 30),
    ]

    for expr_str, expected in expressions:
        result = evaluate(expr_str, ctx)
        assert result == expected


def test_processed_context_equivalence():
    """Test that ProcessedContext gives same results as raw data."""
    data = {"numbers": [1, 2, 3, 4, 5], "threshold": 3, "active": True}

    ctx = ProcessedContext(data)
    expressions = [
        "numbers[0] + numbers[1]",
        "numbers[2] > threshold",
        "active and numbers[4] == 5",
        "numbers[1] * 2 == 4",
    ]

    for expr in expressions:
        result_raw = evaluate(expr, data)
        result_ctx = evaluate(expr, ctx)
        assert result_raw == result_ctx, f"Results differ for expression: {expr}"


def test_processed_context_with_datetime():
    """Test ProcessedContext handles datetime objects correctly."""
    from datetime import datetime

    data = {
        "created_at": datetime(2023, 1, 15, 12, 0, 0),
        "updated_at": datetime(2023, 2, 1, 12, 0, 0),
    }

    ctx = ProcessedContext(data)

    # Test datetime operations
    assert evaluate("created_at before updated_at", ctx) is True


def test_processed_context_error_handling():
    """Test error handling with ProcessedContext."""
    # Invalid JSON string should still raise an error
    with pytest.raises(DilemmaError):
        ProcessedContext('{"invalid": json}')


def test_mixed_usage_patterns():
    """Test mixing ProcessedContext with other context types."""
    data = {"x": 10, "y": 20}
    ctx = ProcessedContext(data)

    # Same expression with different context types
    expr = "x + y"

    result1 = evaluate(expr, data)  # Raw dict
    result2 = evaluate(expr, ctx)  # ProcessedContext
    result3 = evaluate(expr, '{"x": 10, "y": 20}')  # JSON string

    assert result1 == result2 == result3 == 30


def test_compiled_expression_context_switching():
    """Test switching contexts with compiled expressions."""
    expr = compile_expression("value * multiplier")

    contexts = [
        ProcessedContext({"value": 5, "multiplier": 2}),
        ProcessedContext({"value": 10, "multiplier": 3}),
        ProcessedContext({"value": 7, "multiplier": 4}),
    ]

    expected_results = [10, 30, 28]

    for ctx, expected in zip(contexts, expected_results):
        result = expr.evaluate(ctx)
        assert result == expected
