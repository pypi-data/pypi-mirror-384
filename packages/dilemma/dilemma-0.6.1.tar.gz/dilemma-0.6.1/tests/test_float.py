"""Tests for float value support in the expression language."""

from hypothesis import given, strategies as st
from dilemma.lang import evaluate


def test_basic_float_values():
    """Test basic float literals and operations"""
    test_cases = [
        # Float literals
        ("5.0", 5.0),
        ("3.14", 3.14),
        ("0.5", 0.5),
        ("-2.5", -2.5),
        # Basic operations with floats
        ("1.5 + 2.5", 4.0),
        ("5.0 - 2.5", 2.5),
        ("2.0 * 3.0", 6.0),
        ("5.0 / 2.0", 2.5),  # True division
        # Mixed integer and float
        ("5 + 2.5", 7.5),
        ("10 - 0.5", 9.5),
        ("2 * 3.5", 7.0),
        ("10 / 4", 2.5),  # True division even with integers
        # Complex expressions
        ("2.5 * 3.0 + 1.5", 9.0),
        ("10.0 / 2.0 - 1.5", 3.5),
        ("(3.0 + 2.0) * 2.5", 12.5),
    ]

    for expr, expected in test_cases:
        result = evaluate(expr)
        assert abs(result - expected) < 1e-10, (
            f"Failed for '{expr}': got {result}, expected {expected}"
        )


def test_float_comparison():
    """Test comparison operators with float values"""
    test_cases = [
        ("3.5 == 3.5", True),
        ("3.5 != 3.5", False),
        ("3.5 < 4.0", True),
        ("3.5 > 3.0", True),
        ("3.5 <= 3.5", True),
        ("3.5 >= 4.0", False),
        # Close values
        ("0.1 + 0.2 == 0.3", True),  # Handle floating point precision
    ]

    for expr, expected in test_cases:
        result = evaluate(expr)
        assert result == expected, (
            f"Failed for '{expr}': got {result}, expected {expected}"
        )


def test_float_with_logical():
    """Test logical operations combined with float values"""
    test_cases = [
        ("3.5 > 3.0 and 2.5 < 3.0", True),
        ("3.5 < 3.0 or 2.5 < 3.0", True),
        ("(3.5 > 3.0) and (2.5 > 3.0)", False),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


# Use hypothesis for property-based testing of float expressions
@given(
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_addition_property(a, b):
    """Test that addition works correctly for floats"""
    expr = f"{a} + {b}"
    expected = a + b
    result = evaluate(expr)
    assert abs(result - expected) < 1e-10


@given(
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_subtraction_property(a, b):
    """Test that subtraction works correctly for floats"""
    expr = f"{a} - {b}"
    expected = a - b
    result = evaluate(expr)
    assert abs(result - expected) < 1e-10


@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_multiplication_property(a, b):
    """Test that multiplication works correctly for floats"""
    expr = f"{a} * {b}"
    expected = a * b
    result = evaluate(expr)
    assert abs(result - expected) < 1e-10


@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_division_property(a, b):
    """Test that division works correctly for floats"""
    expr = f"{a} / {b}"
    expected = a / b
    result = evaluate(expr)
    assert abs(result - expected) < 1e-10


def test_float_precision_edge_cases():
    """Test handling of float precision edge cases"""
    # For the expression language, we want 0.1 + 0.2 to equal 0.3 exactly
    assert evaluate("0.1 + 0.2 == 0.3") is True

    # Test very small values
    assert abs(evaluate("0.0000001 + 0.0000002") - 0.0000003) < 1e-10

    # Test with larger exponents
    assert abs(evaluate("1000000.0 * 0.000001") - 1.0) < 1e-10
