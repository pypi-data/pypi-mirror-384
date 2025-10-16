"""
Tests for execution error handling context manager.
"""

import pytest
from lark.exceptions import VisitError

from dilemma.errors.execution import execution_error_handling
from dilemma.errors.exc import EvaluationError, VariableError


def test_no_error_passes_through():
    """Test that when no error occurs, the context manager doesn't interfere."""
    expression = "test expression"

    with execution_error_handling(expression):
        result = "success"

    assert result == "success"


def test_dilemma_error_propagates_unchanged():
    """Test that DilemmaError subclasses are propagated unchanged."""
    expression = "test expression"
    original_error = VariableError(variable="test_var", details="Variable not found")

    with pytest.raises(VariableError) as exc_info:
        with execution_error_handling(expression):
            raise original_error

    # Should be the exact same error instance
    assert exc_info.value is original_error


def test_visit_error_with_dilemma_original_exception():
    """Test VisitError containing a DilemmaError as original exception."""
    expression = "test expression"
    original_dilemma_error = VariableError(variable="nested_var", details="Nested error")
    visit_error = VisitError("test_rule", "test_tree", original_dilemma_error)

    with pytest.raises(VariableError) as exc_info:
        with execution_error_handling(expression):
            raise visit_error

    # Should get the original DilemmaError back
    assert exc_info.value is original_dilemma_error


def test_visit_error_with_non_dilemma_original_exception():
    """Test VisitError containing a non-DilemmaError as original exception."""
    expression = "test expression"
    original_error = ValueError("Some value error")
    visit_error = VisitError("test_rule", "test_tree", original_error)

    with pytest.raises(EvaluationError) as exc_info:
        with execution_error_handling(expression):
            raise visit_error

    # Should be wrapped in EvaluationError
    assert isinstance(exc_info.value, EvaluationError)
    assert exc_info.value.context["expression"] == expression
    assert exc_info.value.context["error_type"] == "VisitError"
    assert "test_rule" in exc_info.value.context["details"]
    assert exc_info.value.__cause__ is visit_error


def test_generic_exception_wrapped_in_evaluation_error():
    """Test that generic exceptions are wrapped in EvaluationError."""
    expression = "test expression"
    original_error = RuntimeError("Some runtime error")

    with pytest.raises(EvaluationError) as exc_info:
        with execution_error_handling(expression):
            raise original_error

    # Should be wrapped in EvaluationError
    assert isinstance(exc_info.value, EvaluationError)
    assert exc_info.value.context["expression"] == expression
    assert exc_info.value.context["error_type"] == str(type(original_error))
    assert exc_info.value.context["details"] == str(original_error)
    assert exc_info.value.__cause__ is original_error


def test_custom_exception_wrapped_in_evaluation_error():
    """Test that custom non-DilemmaError exceptions are wrapped properly."""
    expression = "custom test"

    class CustomError(Exception):
        """Custom exception for testing."""

        pass

    original_error = CustomError("Custom error message")

    with pytest.raises(EvaluationError) as exc_info:
        with execution_error_handling(expression):
            raise original_error

    # Should be wrapped in EvaluationError
    assert isinstance(exc_info.value, EvaluationError)
    assert exc_info.value.context["expression"] == expression
    assert exc_info.value.context["error_type"] == str(type(original_error))
    assert exc_info.value.context["details"] == "Custom error message"
    assert exc_info.value.__cause__ is original_error


def test_visit_error_without_original_exception():
    """Test VisitError that doesn't have an original exception."""
    expression = "test expression"
    visit_error = VisitError("test_rule", "test_tree", None)

    with pytest.raises(EvaluationError) as exc_info:
        with execution_error_handling(expression):
            raise visit_error

    # Should be wrapped in EvaluationError since orig_exc is None
    assert isinstance(exc_info.value, EvaluationError)
    assert exc_info.value.context["expression"] == expression
    assert exc_info.value.context["error_type"] == "VisitError"
    assert exc_info.value.__cause__ is visit_error
