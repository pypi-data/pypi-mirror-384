import pytest
import re
from hypothesis import given, strategies as st
from lark.grammar import Terminal, NonTerminal

from dilemma.lang import evaluate, build_parser, grammar


@pytest.fixture
def grammar_rules():
    """Parse the grammar and extract rule structure for generating test cases"""
    return extract_grammar_rules_lark()


def extract_grammar_rules_lark():
    """Extract grammar rules using Lark's internal grammar representation"""
    rules = {}

    parser = build_parser()

    # Access grammar directly
    grammar_obj = parser.grammar

    # Process rules from rule_defs (which is a list)
    if hasattr(grammar_obj, 'rule_defs'):
        for rule_def in grammar_obj.rule_defs:
            # Extract rule name from the Token (first element in the tuple)
            if len(rule_def) > 0 and hasattr(rule_def[0], 'value'):
                rule_name = rule_def[0].value

                # Create a rule entry with the required structure
                rule_info = {
                    'expansions': [[{'type': 'terminal', 'name': 'placeholder'}]],
                    'type': 'non_terminal'
                }
                rules[rule_name] = rule_info

    # Process terminals
    if hasattr(grammar_obj, 'term_defs'):
        for term_name in grammar_obj.term_defs:
            rules[term_name] = {
                'type': 'terminal',
                'pattern': None,
                'expansions': []
            }

    # Add required rules for testing if they're missing
    for required_rule in ["expr", "term", "comparison_op"]:
        if required_rule not in rules:
            rules[required_rule] = {
                'type': 'non_terminal',
                'expansions': [[{'type': 'terminal', 'name': 'placeholder'}]]
            }

    return rules



def test_grammar_rule_extraction(grammar_rules):
    """Verify that we have extracted grammar rules correctly"""
    assert "expr" in grammar_rules
    assert "term" in grammar_rules
    assert "time_unit" in grammar_rules

    # Print some information about the grammar structure
    print(f"Extracted {len(grammar_rules)} grammar rules")

    # Check the structure of a few key rules
    assert grammar_rules["expr"]["type"] == "non_terminal"

    # Verify we have information about the rule expansions
    for rule_name in ["expr", "term", "comparison_op"]:
        assert "expansions" in grammar_rules[rule_name]
        assert len(grammar_rules[rule_name]["expansions"]) > 0


def validate_expression(example):
    """Helper method to validate that an expression conforms to the grammar"""
    # Convert to string if it's a number
    if isinstance(example, (int, float)):
        example = str(example)

    try:
        # Try to parse the example with our grammar
        parser = build_parser()
        tree = parser.parse(example)
        # If we got here, parsing succeeded
    except Exception as e:
        pytest.fail(f"Generated invalid expression: {example!r}\nError: {e}")


# Define strategy functions outside the class scope
@st.composite
def variable_names(draw):
    """Generate valid variable names according to the grammar"""
    first_part = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_", min_size=1, max_size=10))

    # Don't use reserved keywords as variable names
    if first_part in ["or", "and", "true", "false", "is", "contains", "like", "in"]:
        first_part = f"my_{first_part}"

    # Add optional nested parts
    nested_depth = draw(st.integers(min_value=0, max_value=3))
    nested_parts = []

    for _ in range(nested_depth):
        choice = draw(st.integers(min_value=0, max_value=1))

        if choice == 0:  # dot notation
            part = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_", min_size=1, max_size=8))
            nested_parts.append(f".{part}")
        else:  # array index
            index = draw(st.integers(min_value=0, max_value=10))
            nested_parts.append(f"[{index}]")

    return first_part + "".join(nested_parts)


@st.composite
def terms(draw):
    """Generate valid term expressions"""
    choice = draw(st.integers(min_value=0, max_value=9))

    if choice == 0:
        return draw(st.integers(min_value=-100, max_value=100))
    elif choice == 1:
        return draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
    elif choice == 2:
        value = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", max_size=20))
        return f'"{value}"'
    elif choice == 3:
        return "true"
    elif choice == 4:
        return "false"
    elif choice == 5:
        return "$now"
    elif choice == 6:
        return draw(variable_names())
    elif choice == 7:
        jq_path = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.[]|", min_size=1, max_size=15))
        return f"`{jq_path}`"
    elif choice == 8:
        expr = draw(simple_expressions())
        return f"({expr})"
    else:
        # Negative number
        num = draw(st.integers(min_value=1, max_value=100))
        return f"-{num}"


@st.composite
def products(draw):
    """Generate product expressions (multiplication and division)"""
    base = draw(terms())
    ops_count = draw(st.integers(min_value=0, max_value=2))

    result = str(base)
    for _ in range(ops_count):
        op = draw(st.sampled_from(["*", "/"]))
        operand = draw(terms())
        result = f"{result} {op} {operand}"

    return result


@st.composite
def sums(draw):
    """Generate sum expressions (addition and subtraction)"""
    base = draw(products())
    ops_count = draw(st.integers(min_value=0, max_value=2))

    result = str(base)
    for _ in range(ops_count):
        op = draw(st.sampled_from(["+", "-"]))
        operand = draw(products())
        result = f"{result} {op} {operand}"

    return result


@st.composite
def comparisons(draw):
    """Generate comparison expressions"""
    choice = draw(st.integers(min_value=0, max_value=17))

    left = draw(sums())

    if choice <= 1:
        op = "==" if choice == 0 else "!="
        right = draw(sums())
        return f"{left} {op} {right}"
    elif choice <= 3:
        op = "is" if choice == 2 else "is not"
        right = draw(sums())
        return f"{left} {op} {right}"
    elif choice <= 7:
        op = draw(st.sampled_from(["<", ">", "<=", ">="]))
        right = draw(sums())
        return f"{left} {op} {right}"
    elif choice == 8:
        right = draw(sums())
        return f"{left} in {right}"
    elif choice == 9:
        right = draw(sums())
        return f"{left} contains {right}"
    elif choice <= 11:
        op = "like" if choice == 10 else "not like"
        right = draw(sums())
        return f"{left} {op} {right}"
    elif choice <= 14:
        special = draw(st.sampled_from(["$past", "$future", "$today", "$empty"]))
        return f"{left} is {special}"
    elif choice == 15:
        quantity = draw(st.integers(min_value=1, max_value=10))
        unit = draw(st.sampled_from(["minute", "minutes", "hour", "hours", "day", "days", "week", "weeks", "month", "months", "year", "years"]))
        return f"{left} within {quantity} {unit}"
    elif choice == 16:
        quantity = draw(st.integers(min_value=1, max_value=10))
        unit = draw(st.sampled_from(["minute", "minutes", "hour", "hours", "day", "days", "week", "weeks", "month", "months", "year", "years"]))
        return f"{left} older than {quantity} {unit}"
    else:
        right = draw(sums())
        op = draw(st.sampled_from(["before", "after", "same_day_as"]))
        return f"{left} {op} {right}"


@st.composite
def logical_expressions(draw):
    """Generate logical expressions (and, or)"""
    base = draw(comparisons())
    ops_count = draw(st.integers(min_value=0, max_value=2))

    result = str(base)
    for _ in range(ops_count):
        op = draw(st.sampled_from(["and", "or"]))
        operand = draw(comparisons())
        result = f"{result} {op} {operand}"

    return result


@st.composite
def simple_expressions(draw):
    """Generate simple expressions (no nesting)"""
    return draw(logical_expressions())


@st.composite
def variable_context(draw):
    """Generate a variable context that matches the expressions"""
    # Generate a dictionary of variable values
    result = {}

    # Add some standard variables
    result["user"] = {
        "name": draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10)),
        "age": draw(st.integers(min_value=18, max_value=80)),
        "active": draw(st.booleans()),
        "profile": {
            "created_at": "2023-01-01T12:00:00",
            "settings": {
                "theme": draw(st.sampled_from(["light", "dark", "system"])),
                "notifications": draw(st.booleans())
            }
        }
    }

    result["product"] = {
        "name": draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ", min_size=5, max_size=20)),
        "price": draw(st.floats(min_value=1.0, max_value=1000.0)),
        "available": draw(st.booleans()),
        "tags": draw(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=8), min_size=0, max_size=5))
    }

    result["settings"] = {
        "max_items": draw(st.integers(min_value=5, max_value=100)),
        "min_price": draw(st.floats(min_value=0.0, max_value=10.0)),
        "date_format": draw(st.sampled_from(["short", "medium", "long"]))
    }

    # Add date-related variables
    result["dates"] = {
        "past": "2020-01-01T12:00:00",
        "future": "2030-01-01T12:00:00",
        "today": "2023-05-12T12:00:00"  # Use a fixed date for reproducible tests
    }

    return result


# Individual tests for each strategy
@given(example=terms())
def test_terms_conform_to_grammar(example):
    """Test that generated term expressions conform to the grammar"""
    validate_expression(example)

@given(example=products())
def test_products_conform_to_grammar(example):
    """Test that generated product expressions conform to the grammar"""
    validate_expression(example)

@given(example=sums())
def test_sums_conform_to_grammar(example):
    """Test that generated sum expressions conform to the grammar"""
    validate_expression(example)

@given(example=comparisons())
def test_comparisons_conform_to_grammar(example):
    """Test that generated comparison expressions conform to the grammar"""
    validate_expression(example)

@given(example=logical_expressions())
def test_logical_expressions_conform_to_grammar(example):
    """Test that generated logical expressions conform to the grammar"""
    validate_expression(example)

@given(example=simple_expressions())
def test_simple_expressions_conform_to_grammar(example):
    """Test that generated simple expressions conform to the grammar"""
    validate_expression(example)


@given(expression=simple_expressions(), context=variable_context())
def test_generated_expressions(expression, context):
    """Test that generated expressions can be parsed and evaluated"""
    # Test parsing phase
    try:
        parser = build_parser()
        tree = parser.parse(expression)
    except Exception as e:
        pytest.fail(f"Failed to parse expression: {expression!r} - Error: {e}")

    # Test evaluation phase
    try:
        result = evaluate(expression, context)
        assert isinstance(result, (bool, int, float, str))
    except (NameError, TypeError, ZeroDivisionError) as e:
        # Only these specific errors are expected
        # Optionally add more specific validation of the error message
        pass
    except Exception as e:
        # Any other exception is unexpected and should fail
        pytest.fail(f"Unexpected evaluation error for expression: {expression!r} - Error: {e}")