from hypothesis import given, strategies as st
from dilemma.lang import evaluate


# Test basic parentheses functionality
def test_basic_parentheses():
    """Test basic parentheses functionality"""
    test_cases = [
        # Simple expressions
        ("(5)", 5),
        ("(-10)", -10),
        # Basic operations in parentheses
        ("(2 + 3)", 5),
        ("(10 - 4)", 6),
        ("(3 * 4)", 12),
        ("(8 / 2)", 4),
        # Ensure parentheses don't change simple evaluation
        ("(5) + (3)", 8),
        ("(10) - (4)", 6),
        ("(2) * (6)", 12),
        ("(10) / (2)", 5),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


# Test nested parentheses
def test_nested_parentheses():
    """Test nested parentheses"""
    test_cases = [
        ("((5))", 5),
        ("(((2 + 3)))", 5),
        ("(2 + (3 + 4))", 9),
        ("((2 + 3) + 4)", 9),
        ("(2 + (3 * 4))", 14),
        ("((10 - 2) / 2)", 4),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


# Test parentheses changing operator precedence
def test_precedence_with_parentheses():
    """Test how parentheses affect operator precedence"""
    test_cases = [
        # Changing addition/multiplication precedence
        ("2 + 3 * 4", 14),  # Normal precedence: 2 + (3 * 4)
        ("(2 + 3) * 4", 20),  # Parentheses change: (2 + 3) * 4
        # Changing multiplication/division precedence
        ("6 * 8 / 4", 12),  # Normal: (6 * 8) / 4
        ("6 * (8 / 4)", 12),  # Parentheses: 6 * (8 / 4)
        # Complex precedence changes
        ("2 + 3 * 4 + 5", 19),  # Normal: 2 + (3 * 4) + 5
        ("(2 + 3) * (4 + 5)", 45),  # With parentheses
        ("2 * (3 + 4) - 5", 9),  # Normal: (2 * 7) - 5
        ("2 * ((3 + 4) - 5)", 4),  # With nested parentheses: 2 * (7 - 5)
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


# Test parentheses with comparison operators
def test_comparison_with_parentheses():
    """Test comparison operators with parentheses"""
    test_cases = [
        # Basic comparison with parentheses
        ("(5) == (5)", True),
        ("(5) != (6)", True),
        ("(10) > (5)", True),
        ("(5) < (10)", True),
        ("(5) <= (5)", True),
        ("(5) >= (5)", True),
        # Parentheses changing comparison precedence
        ("2 + 3 == 5", True),  # Normal
        ("(2 + 3) == 5", True),  # Same with parentheses
        ("2 + 3 * 2 == 8", True),  # Normal: 2 + (3 * 2) == 8
        ("(2 + 3) * 2 == 10", True),  # Changed with parentheses
        ("5 * 2 > 8 + 1", True),  # Normal
        ("5 * (2 > 1) + 8", 13),  # Comparison in parentheses: 5 * 1 + 8
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


# Use hypothesis for more thorough testing
@given(
    st.integers(min_value=-100, max_value=100), st.integers(min_value=-100, max_value=100)
)
def test_hypothesis_basic_parentheses(a, b):
    """Use hypothesis to test basic parenthesized expressions"""
    # Test addition
    assert evaluate(f"({a} + {b})") == a + b

    # Test subtraction
    assert evaluate(f"({a} - {b})") == a - b

    # Test multiplication
    assert evaluate(f"({a} * {b})") == a * b

    # Test division (avoiding division by zero)
    if b != 0:
        assert evaluate(f"({a} / {b})") == a / b


@given(
    st.integers(min_value=-20, max_value=20),
    st.integers(min_value=-20, max_value=20),
    st.integers(min_value=-20, max_value=20),
)
def test_hypothesis_precedence_change(a, b, c):
    """Test how parentheses change precedence in various expressions"""
    # Addition and multiplication
    assert evaluate(f"{a} + {b} * {c}") == a + (b * c)
    assert evaluate(f"({a} + {b}) * {c}") == (a + b) * c

    # Addition and subtraction in parentheses
    assert evaluate(f"{a} - ({b} + {c})") == a - (b + c)

    # Nested operations
    if c != 0:
        assert evaluate(f"{a} * ({b} / {c})") == a * (b / c)

    # Complex grouping
    assert evaluate(f"({a} + {b}) - ({a} * {c})") == (a + b) - (a * c)
