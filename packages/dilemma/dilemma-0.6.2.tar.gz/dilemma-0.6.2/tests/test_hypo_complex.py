"""Integration tests that combine all operators in complex expressions."""

from hypothesis import given, strategies as st
from dilemma.lang import evaluate

# Import strategies from other test modules
try:
    from tests.test_hypo_basic_math import (  # type: ignore
        integers_st,
        addition_expressions,
        subtraction_expressions,
        multiplication_expressions,
        division_expressions,
        complex_expressions,
    )
except ImportError:
    # Default strategies if imports fail
    integers_st = st.integers(min_value=-100, max_value=100)

    @st.composite
    def addition_expressions(draw):
        left = draw(integers_st)
        right = draw(integers_st)
        return f"{left} + {right}", float(left + right)

    @st.composite
    def subtraction_expressions(draw):
        left = draw(integers_st)
        right = draw(integers_st)
        return f"{left} - {right}", float(left - right)

    @st.composite
    def multiplication_expressions(draw):
        left = draw(integers_st)
        right = draw(integers_st)
        return f"{left} * {right}", float(left * right)

    @st.composite
    def division_expressions(draw):
        left = draw(integers_st)
        right = draw(st.integers(min_value=1, max_value=100))
        # Ensure right is not zero for division
        if right == 0:  # Should not happen with min_value=1, but as safeguard
            right = 1
        return f"{left} / {right}", left / right  # Use float division

    @st.composite
    def complex_expressions(draw):
        # Simplified version if import fails
        a = draw(integers_st)
        b = draw(integers_st)
        op = draw(st.sampled_from(["+", "-", "*"]))  # Division not included here
        expr = f"{a} {op} {b}"
        # eval result for +,-,* with ints is int. Cast to float for consistency.
        expected = float(eval(expr))
        return expr, expected


# Strategy for comparison expressions
@st.composite
def comparison_expressions(draw):
    """Generate a comparison expression and its expected result"""
    left = draw(integers_st)
    right = draw(integers_st)
    op = draw(st.sampled_from(["==", "!=", "<", ">", "<=", ">="]))
    expr = f"{left} {op} {right}"

    if op == "==":
        expected = left == right
    elif op == "!=":
        expected = left != right
    elif op == "<":
        expected = left < right
    elif op == ">":
        expected = left > right
    elif op == "<=":
        expected = left <= right
    else:  # op == ">="
        expected = left >= right

    return expr, expected


# Strategy for logical expressions
@st.composite
def logical_expressions(draw):
    """Generate a logical expression and its expected result"""
    left = draw(st.booleans())
    right = draw(st.booleans())
    op = draw(st.sampled_from(["and", "or"]))

    left_expr = str(int(left))  # Convert to 1/0
    right_expr = str(int(right))  # Convert to 1/0

    expr = f"{left_expr} {op} {right_expr}"

    if op == "and":
        expected = left and right
    else:  # op == "or"
        expected = left or right

    return expr, expected


# Strategy for parenthesized expressions
@st.composite
def parenthesized_expressions(draw):
    """Generate a parenthesized expression and its expected result"""
    base_expr, expected = draw(
        st.one_of(
            addition_expressions(),
            subtraction_expressions(),
            multiplication_expressions(),
            division_expressions(),
            comparison_expressions(),
            logical_expressions(),
        )
    )

    return f"({base_expr})", expected


# Strategy for complex nested expressions
@st.composite
def nested_complex_expressions(draw):
    """Generate a complex nested expression with multiple operators and parentheses"""
    # Start with a simple expression
    expr1, val1 = draw(
        st.one_of(
            addition_expressions(), multiplication_expressions(), comparison_expressions()
        )
    )

    # Add a logical operator and another expression
    log_op = draw(st.sampled_from(["and", "or"]))

    expr2, val2 = draw(
        st.one_of(
            subtraction_expressions(), division_expressions(), comparison_expressions()
        )
    )

    # Decide if we want to use parentheses
    use_parens = draw(st.booleans())

    if use_parens:
        final_expr = f"({expr1}) {log_op} ({expr2})"
    else:
        final_expr = f"{expr1} {log_op} {expr2}"

    # Calculate expected value based on type
    if isinstance(val1, bool) and isinstance(val2, bool):
        if log_op == "and":
            expected = val1 and val2
        else:  # log_op == "or"
            expected = val1 or val2
    else:
        # Convert to boolean as needed
        bool_val1 = bool(val1)
        bool_val2 = bool(val2)

        if log_op == "and":
            expected = bool_val1 and bool_val2
        else:  # log_op == "or"
            expected = bool_val1 or bool_val2

    return final_expr, expected


# Strategy for extremely complex expressions
@st.composite
def extreme_expressions(draw):
    """Generate extremely complex expressions with many operators and parentheses"""
    # Only use boolean comparison expressions to ensure consistent behavior
    comp_expr1, comp_val1 = draw(comparison_expressions())
    comp_expr2, comp_val2 = draw(comparison_expressions())
    comp_expr3, comp_val3 = draw(comparison_expressions())

    # Construct a more controlled expression with clear expectations
    log_op1 = draw(st.sampled_from(["and", "or"]))
    log_op2 = draw(st.sampled_from(["and", "or"]))

    # Add parentheses in a controlled way
    if draw(st.booleans()):
        expr = f"({comp_expr1}) {log_op1} ({comp_expr2} {log_op2} {comp_expr3})"
        # Calculate expected value
        if log_op2 == "and":
            inner_result = comp_val2 and comp_val3
        else:
            inner_result = comp_val2 or comp_val3

        if log_op1 == "and":
            expected = comp_val1 and inner_result
        else:
            expected = comp_val1 or inner_result
    else:
        expr = f"({comp_expr1} {log_op1} {comp_expr2}) {log_op2} ({comp_expr3})"
        # Calculate expected value
        if log_op1 == "and":
            inner_result = comp_val1 and comp_val2
        else:
            inner_result = comp_val1 or comp_val2

        if log_op2 == "and":
            expected = inner_result and comp_val3
        else:
            expected = inner_result or comp_val3

    return expr, expected


@given(nested_complex_expressions())
def test_nested_expressions(expr_tuple):
    """Test nested expressions combining arithmetic, comparison, and logical operations"""
    expr, expected = expr_tuple
    assert evaluate(expr) == expected


@given(extreme_expressions())
def test_extreme_expressions(expr_tuple):
    """Test extremely complex expressions"""
    expr, expected = expr_tuple
    assert evaluate(expr) == expected


def test_hardcoded_complex_cases():
    """Test specific complex cases that combine all operators"""
    test_cases = [
        # Arithmetic with comparison and logical operators
        ("(2 * 3 + 4) > (1 + 2) and 5 - 2 == 3", True),
        ("10 / 2 == 5 or 3 * 2 != 6", True),
        ("(7 > 4) and (10 / 2 <= 6)", True),
        ("(4 < 3) or (12 / 4 == 3 and 2 + 2 == 4)", True),
        # Multiple levels of precedence
        ("2 + 3 * 4 == 14 and 5 > 3 + 1", True),
        ("10 - 2 * 3 < 8 or 5 * 2 > 8 and 4 / 2 == 2", True),
        # Complex nested expressions
        ("(5 > 3 and (10 / 2) == 5) or ((4 < 3) and 7 * 2 > 10)", True),
        ("((3 + 4 * 2 > 10) and (5 * 2 == 10)) or (7 - 2 > 4 and 6 / 3 == 2)", True),
        # Very complex expressions
        ("(2 * (3 + 4) > 10) and ((15 / 3) == 5 or 7 <= (10 - 2))", True),
        ("(5 + 3 * 2 > 10) and (20 / 4 == 5) or (7 <= 3 + 4 and 2 * 3 != 7)", True),
        # Edge case combinations
        ("(0 and 5 > 3) or (1 and 4 <= 10)", True),
        ("(5 > 0) and (0 or 1) and (3 + 2 * 2 == 7)", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected, f"Failed for: {expr}"
