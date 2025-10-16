import pytest
from hypothesis import given, strategies as st, settings, example

from dilemma.errors import DilemmaError
from dilemma.lang import evaluate

# Strategy for generating nested variable names with smaller size limits
nested_variable_names_st = st.lists(
    st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]{1,5}", fullmatch=True), min_size=2, max_size=3
).map(".".join)

# Strategy for generating smaller nested dictionaries with fewer potential values
nested_dicts_st = st.recursive(
    st.dictionaries(
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]{1,5}", fullmatch=True),
        st.one_of(st.integers(min_value=-10, max_value=10), st.booleans()),
        max_size=3,
    ),
    lambda children: st.dictionaries(
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]{1,5}", fullmatch=True), children, max_size=2
    ),
    max_leaves=5,
)


# Use settings to limit the number of test examples
@settings(max_examples=10)
@given(
    var_path=nested_variable_names_st,
    value=st.integers(min_value=-10, max_value=10),
    context=nested_dicts_st,
)
@example(var_path="a.b.c", value=42, context={"a": {"b": {}}})
def test_evaluate_nested_variable(var_path, value, context):
    """Test evaluating nested variable names."""
    # Inject the value into the context at the specified path
    segments = var_path.split(".")

    # Create a new context to avoid modifying the original
    modified_context = context.copy()
    current = modified_context

    # Inject value at the path, ensuring all intermediate segments are dictionaries
    for segment in segments[:-1]:
        if segment not in current or not isinstance(current[segment], dict):
            current[segment] = {}
        current = current[segment]
    current[segments[-1]] = value

    # Evaluate the expression using the modified context
    result = evaluate(var_path, modified_context)
    assert result == value


# Add specific test cases for edge cases
def test_evaluate_nested_variable_specific_cases():
    """Test evaluating nested variable names with specific test cases."""
    # Test case 1: Simple nested path
    context = {"a": {"b": 42}}
    assert evaluate("a.b", context) == 42

    # Test case 2: Deeper nesting
    context = {"x": {"y": {"z": 99}}}
    assert evaluate("x.y.z", context) == 99

    # Test case 3: Path with boolean value
    context = {"flag": {"state": True}}
    assert evaluate("flag.state", context) is True


@settings(max_examples=10)
@given(var_path=nested_variable_names_st, context=nested_dicts_st)
@example(var_path="a.b.c", context={"a": {"x": 5}})
@example(var_path="A0.A0", context={"A0": 0})  # Add the failing example explicitly
def test_evaluate_undefined_nested_variable(var_path, context):
    """Test evaluating undefined nested variable paths."""
    # Create a context that definitely doesn't contain the path
    segments = var_path.split(".")

    # Make a copy of the context to avoid modifying the original
    modified_context = context.copy()
    current = modified_context

    for i, segment in enumerate(segments[:-1]):
        if not isinstance(current, dict) or segment not in current:
            # If the current segment is not a dictionary or the key is missing, we're done
            break

        if i == len(segments) - 2:
            # Make sure the last segment is missing
            if isinstance(current[segment], dict) and segments[-1] in current[segment]:
                del current[segment][segments[-1]]

        # Move to the next level in the context
        current = current.get(segment, {})

    # Try to evaluate the expression, should raise some kind of lookup error
    with pytest.raises((DilemmaError, AttributeError)):  # Accept either error type
        evaluate(var_path, modified_context)
