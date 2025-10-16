from datetime import datetime, timezone

import jq
import pytest
from hypothesis import given, strategies as st, settings

from dilemma.lang import evaluate
from dilemma.errors import VariableError, DilemmaError


def test_lang_paren_expression():
    """
    Test parenthesized expressions to exercise the grammar's paren rule.
    (Covers missing lines in lang.py, e.g. handling of "( expr )")
    """
    # Simple arithmetic expression in parentheses
    result = evaluate("(2 + 3) * 4", {})
    assert result == 20


def test_lang_nested_arithmetic():
    """
    Test a complex nested arithmetic expression that uses multiple grammar branches.
    """
    # This forces use of the addition, subtraction, multiplication, and paren rules.
    result = evaluate("((10 - 3) * 2) + 5", {})
    expected = ((10 - 3) * 2) + 5
    assert result == expected


def test_evaluate_returns_datetime():
    """
    Test that evaluate reconstructs datetime objects correctly.
    This ensures the __datetime__ branch is covered in ExpressionTransformer.variable().
    """
    dt = datetime(2025, 5, 11, 14, 30, tzinfo=timezone.utc)
    context = {"event": dt}
    result = evaluate("event", context)
    assert isinstance(result, datetime)
    # Compare ISO strings to account for potential microsecond differences.
    assert result.isoformat() == dt.isoformat()


def test_evaluate_datetime_from_json_string():
    """
    Test that evaluate can correctly reconstruct datetime objects from JSON string.
    This specifically targets the datetime reconstruction from serialized JSON strings,
    which was moved from lookup_variable to ExpressionTransformer.variable().
    """
    # Create a JSON string with a serialized datetime in the exact format expected by the code
    # This format must match what DateTimeEncoder.default() produces
    json_string = '{"event": {"__datetime__": "2025-05-11T14:30:00+00:00"}}'

    # Test evaluation using the JSON string as variables
    result = evaluate("event", json_string)

    # Verify the result is a datetime object with the expected value
    assert isinstance(result, datetime)
    expected_dt = datetime(2025, 5, 11, 14, 30, tzinfo=timezone.utc)
    assert result.isoformat() == expected_dt.isoformat()

    # Test a more complex case with nested datetime objects
    nested_json = """
    {
        "user": {
            "name": "Test User",
            "registration": {"__datetime__": "2023-01-15T10:30:00+00:00"},
            "events": [
                {"id": 1, "timestamp": {"__datetime__": "2023-05-10T15:45:00+00:00"}},
                {"id": 2, "timestamp": {"__datetime__": "2023-06-20T09:15:00+00:00"}}
            ]
        }
    }
    """

    # Access the nested datetime objects
    reg_date = evaluate("user.registration", nested_json)
    assert isinstance(reg_date, datetime)
    assert reg_date.year == 2023 and reg_date.month == 1 and reg_date.day == 15

    # Access datetime in an array element
    event_date = evaluate("user.events[1].timestamp", nested_json)
    assert isinstance(event_date, datetime)
    assert event_date.year == 2023 and event_date.month == 6 and event_date.day == 20


# Strategy for generating valid variable names (alphanumeric, starting with
# a letter or underscore)
# Exclude "or" and "and" as they are now reserved keywords.
variable_names_st = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True).filter(
    lambda x: x not in ["or", "and", "is", "in"]
)

# Strategy for generating simple values (integers, floats, booleans)
simple_values_st = st.one_of(
    st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()
)


@settings(max_examples=50)
@given(var_name=variable_names_st, value=simple_values_st)
def test_evaluate_single_variable(var_name, value):
    """Test evaluating an expression that is just a single variable."""
    expression = var_name
    variables = {var_name: value}
    if (
        isinstance(value, float) and abs(value) < 1e-9
    ):  # Handle potential precision issues with zero floats
        assert abs(evaluate(expression, variables) - value) < 1e-9
    else:
        assert evaluate(expression, variables) == value


@settings(max_examples=50)
@given(var_name=variable_names_st, value=st.integers())
def test_evaluate_variable_as_integer(var_name, value):
    """Test that a variable holding an integer is evaluated correctly."""
    expression = var_name
    variables = {var_name: value}
    result = evaluate(expression, variables)
    assert isinstance(result, int)
    assert result == value


@settings(max_examples=50)
@given(var_name=variable_names_st, value=st.floats(allow_nan=False, allow_infinity=False))
def test_evaluate_variable_as_float(var_name, value):
    """Test that a variable holding a float is evaluated correctly."""
    expression = var_name
    variables = {var_name: value}
    result = evaluate(expression, variables)
    assert isinstance(result, float)
    if abs(value) < 1e-9:  # Handle potential precision issues with zero floats
        assert abs(result - value) < 1e-9
    else:
        assert result == pytest.approx(value)


@settings(max_examples=50)
@given(var_name=variable_names_st, value=st.booleans())
def test_evaluate_variable_as_boolean(var_name, value):
    """Test that a variable holding a boolean is evaluated correctly."""
    # Note: Booleans are not directly part of the grammar as literals,
    # but can be results of comparisons or stored in variables.
    # Here, we are testing if a variable *can hold* a boolean value
    # and if that value is returned correctly.
    expression = var_name
    variables = {var_name: value}
    result = evaluate(expression, variables)
    # Booleans are numbers in some contexts (0 or 1), ensure strict bool type if
    # that's the intent. For now, if value is bool, result should be bool.
    assert isinstance(result, bool)
    assert result == value


@settings(max_examples=30)
@given(var_name=variable_names_st, defined_value=simple_values_st)
def test_evaluate_variable_among_others(var_name, defined_value):
    """Test evaluating a variable when other variables are also defined."""
    expression = var_name
    variables = {var_name: defined_value, "another_var": 123, "yet_another": 45.6}
    if isinstance(defined_value, float) and abs(defined_value) < 1e-9:
        assert abs(evaluate(expression, variables) - defined_value) < 1e-9
    else:
        assert evaluate(expression, variables) == defined_value




@settings(max_examples=30)
@given(var_name=st.sampled_from(["or", "and"]))  # Actual reserved keywords
def test_evaluate_reserved_keyword_as_variable_name_fails_parsing(var_name):
    """
    Test that using an actual reserved keyword ("or", "and") as if it were a
    variable name causes a parse error (ValueError).
    """
    with pytest.raises(DilemmaError):  # Expecting a parse error from Lark
        evaluate(var_name, {var_name: 1})


@given(
    var_name=st.sampled_from(["if", "else", "then", "MyVar"]), value=simple_values_st
)  # Non-reserved strings
def test_evaluate_non_keyword_strings_as_variable_names(var_name, value):
    """
    Test that strings that resemble keywords but are not reserved (e.g., "if", "else")
    can be used as valid variable names.
    """
    expression = var_name
    variables = {var_name: value}
    if isinstance(value, float) and abs(value) < 1e-9:
        assert abs(evaluate(expression, variables) - value) < 1e-9
    else:
        assert evaluate(expression, variables) == value

