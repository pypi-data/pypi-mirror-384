from hypothesis import given, strategies as st
from dilemma.lang import evaluate


def test_basic_logical_operations():
    """Test basic logical AND and OR operations"""
    test_cases = [
        # Basic AND operations
        ("1 and 1", True),
        ("1 and 0", False),
        ("0 and 1", False),
        ("0 and 0", False),
        # Basic OR operations
        ("1 or 1", True),
        ("1 or 0", True),
        ("0 or 1", True),
        ("0 or 0", False),
        # Non-zero values are truthy
        ("5 and 3", True),
        ("0 and 5", False),
        ("5 and 0", False),
        ("5 or 0", True),
        ("0 or 5", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_logical_with_comparisons():
    """Test logical operations with comparison operators"""
    test_cases = [
        # AND with comparisons
        ("5 > 3 and 10 < 20", True),
        ("5 > 3 and 10 > 20", False),
        ("5 < 3 and 10 < 20", False),
        ("5 < 3 and 10 > 20", False),
        # OR with comparisons
        ("5 > 3 or 10 < 20", True),
        ("5 > 3 or 10 > 20", True),
        ("5 < 3 or 10 < 20", True),
        ("5 < 3 or 10 > 20", False),
        # Mixed expressions
        ("(5 == 5) and (3 != 4)", True),
        ("(5 != 5) and (3 == 3)", False),
        ("(5 <= 10) or (3 >= 4)", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_logical_precedence():
    """Test operator precedence with logical operators"""
    test_cases = [
        # AND has higher precedence than OR
        ("0 or 1 and 0", False),  # Equivalent to: 0 or (1 and 0) = 0 or 0 = False
        ("0 or 1 and 1", True),  # Equivalent to: 0 or (1 and 1) = 0 or 1 = True
        ("1 or 0 and 0", True),  # Equivalent to: 1 or (0 and 0) = 1 or 0 = True
        # Comparison has higher precedence than logical
        ("5 > 3 and 10 < 20", True),  # Equivalent to: (5 > 3) and (10 < 20)
        # Arithmetic has higher precedence than comparison
        ("5 + 2 > 3 * 2 and 10 - 5 < 20 / 2", True),  # (7 > 6) and (5 < 10)
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_logical_with_parentheses():
    """Test how parentheses affect logical operations"""
    test_cases = [
        # Using parentheses to change precedence
        ("0 or (1 and 0)", False),
        ("(0 or 1) and 0", False),
        ("(0 or 1) and 1", True),
        # Complex expressions with parentheses
        ("(5 > 3 or 2 < 1) and (10 != 10 or 4 <= 4)", True),
        ("(5 > 3 and 2 < 1) or (10 != 10 and 4 <= 4)", False),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


@given(st.integers(min_value=-10, max_value=10), st.integers(min_value=-10, max_value=10))
def test_hypothesis_logical_operations(a, b):
    """Use hypothesis to test logical operations with various values"""
    # Truth values based on Python's bool conversion
    a_truth = bool(a)
    b_truth = bool(b)

    # Test AND operation
    assert evaluate(f"{a} and {b}") == (a_truth and b_truth)

    # Test OR operation
    assert evaluate(f"{a} or {b}") == (a_truth or b_truth)

    # Test with comparisons
    assert evaluate(f"{a} > 0 and {b} > 0") == (a > 0 and b > 0)
    assert evaluate(f"{a} > 0 or {b} > 0") == (a > 0 or b > 0)


def test_boolean_literals():
    """Test boolean literals true/false and true/false."""
    # Test literal False values
    assert evaluate("true") is True
    assert evaluate("false") is False

    # Test in logical expressions
    assert evaluate("false and true") is False
    assert evaluate("true and false") is False
    assert evaluate("false or false") is False
    assert evaluate("false or true") is True
