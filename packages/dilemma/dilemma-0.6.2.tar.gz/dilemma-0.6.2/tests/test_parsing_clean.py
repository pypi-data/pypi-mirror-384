"""
Tests for the parsing module error handling functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from contextlib import ExitStack

from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedToken

from dilemma.errors import parsing
from dilemma.errors.exc import UnexpectedCharacterError, UnexpectedEOFError, UnexpectedTokenError


# Tests for suggest_correction functionality
def test_suggest_correction_no_interactive_parser():
    """Test suggest_correction when interactive_parser is None."""
    token = MagicMock()
    suggestions = parsing.suggest_correction(None, token)
    
    assert suggestions == []


def test_suggest_correction_no_accepts():
    """Test suggest_correction when interactive_parser.accepts() returns empty."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = set()
    token = MagicMock()
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    assert suggestions == []


def test_suggest_correction_with_known_tokens():
    """Test suggest_correction with known token types."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"PLUS", "MINUS", "MULT", "DIV"}
    token = MagicMock()
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert "Expected:" in suggestion
    assert "+ (plus)" in suggestion
    assert "- (minus)" in suggestion
    assert "* (multiply)" in suggestion
    assert "/ (divide)" in suggestion


def test_suggest_correction_with_unknown_tokens():
    """Test suggest_correction with unknown token types."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"UNKNOWN_TOKEN", "ANOTHER_TOKEN"}
    token = MagicMock()
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert "Expected:" in suggestion
    assert "UNKNOWN_TOKEN" in suggestion
    assert "ANOTHER_TOKEN" in suggestion


def test_suggest_correction_mixed_known_unknown():
    """Test suggest_correction with mix of known and unknown tokens."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"PLUS", "UNKNOWN_TOKEN"}
    token = MagicMock()
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert "Expected:" in suggestion
    assert "+ (plus)" in suggestion
    assert "UNKNOWN_TOKEN" in suggestion


def test_suggest_correction_variable_with_and_or():
    """Test suggest_correction for VARIABLE token when AND/OR are expected."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"AND", "OR", "PLUS"}
    
    token = MagicMock()
    token.type = "VARIABLE"
    token.value = "and"
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    assert len(suggestions) == 2
    assert any("Expected:" in s for s in suggestions)
    assert any("might be a reserved keyword" in s and "and" in s for s in suggestions)


def test_suggest_correction_variable_no_keywords():
    """Test suggest_correction for VARIABLE token when AND/OR are not expected."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"PLUS", "MINUS"}
    
    token = MagicMock()
    token.type = "VARIABLE"
    token.value = "somevar"
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    # Should only have the "Expected:" suggestion, not the keyword suggestion
    assert len(suggestions) == 1
    assert "Expected:" in suggestions[0]
    assert "reserved keyword" not in suggestions[0]


def test_suggest_correction_non_variable_token():
    """Test suggest_correction for non-VARIABLE token types."""
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"AND", "OR"}
    
    token = MagicMock()
    token.type = "NUMBER"
    token.value = "42"
    
    suggestions = parsing.suggest_correction(interactive_parser, token)
    
    # Should only have the "Expected:" suggestion, not the keyword suggestion
    assert len(suggestions) == 1
    assert "Expected:" in suggestions[0]
    assert "reserved keyword" not in suggestions[0]


# Tests for parsing_error_handling context manager
def test_parsing_error_handling_no_error():
    """Test parsing_error_handling when no error occurs."""
    expression = "x + y"
    parse_func = MagicMock()
    
    with parsing.parsing_error_handling(expression, parse_func):
        result = "success"
    
    assert result == "success"


def test_parsing_error_handling_unexpected_token_with_state():
    """Test handling UnexpectedToken with state and interactive parser."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Create a mock UnexpectedToken exception
    ute = UnexpectedToken(
        token=MagicMock(type="PLUS", value="+", line=1, column=5),
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock(),
        state=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context around error")
    ute.match_examples = MagicMock(return_value="trailing_operator")
    ute.interactive_parser.accepts.return_value = {"VARIABLE", "NUMBER"}
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "trailing_operator"
    assert error.context["context"] == "Context around error"
    assert error.context["line"] == 1
    assert error.context["column"] == 5
    assert "suggestions" in error.context


def test_parsing_error_handling_unexpected_token_no_state():
    """Test handling UnexpectedToken without state."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Create a mock UnexpectedToken exception without state
    ute = UnexpectedToken(
        token=MagicMock(type="PLUS", value="+", line=1, column=5),
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context around error")
    ute.state = None  # Explicitly set state to None
    ute.interactive_parser.accepts.return_value = {"VARIABLE", "NUMBER"}
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "unexpected_token"  # Default template when no pattern match
    assert error.context["context"] == "Context around error"


def test_parsing_error_handling_unexpected_token_no_interactive_parser():
    """Test handling UnexpectedToken without interactive parser."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Create a mock UnexpectedToken exception without interactive parser
    ute = UnexpectedToken(
        token=MagicMock(type="PLUS", value="+", line=1, column=5),
        expected={"VARIABLE", "NUMBER"}
    )
    ute.get_context = MagicMock(return_value="Context around error")
    ute.interactive_parser = None
    ute.state = MagicMock()
    ute.match_examples = MagicMock(return_value="trailing_operator")
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "trailing_operator"
    assert error.context["suggestions"] == []  # Empty suggestions when no interactive parser


def test_parsing_error_handling_unexpected_token_no_hasattr_state():
    """Test handling UnexpectedToken when hasattr(ute, 'state') is False."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Create a mock UnexpectedToken exception
    ute = UnexpectedToken(
        token=MagicMock(type="PLUS", value="+", line=1, column=5),
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context around error")
    ute.interactive_parser.accepts.return_value = {"VARIABLE", "NUMBER"}
    ute.line = 1
    ute.column = 5
    
    # Remove the state attribute entirely
    if hasattr(ute, 'state'):
        delattr(ute, 'state')
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "unexpected_token"  # Should use default template


def test_parsing_error_handling_unexpected_characters():
    """Test handling UnexpectedCharacters exception."""
    expression = "x + @"
    parse_func = MagicMock()
    
    # Create a mock UnexpectedCharacters exception
    uce = UnexpectedCharacters(
        seq="x + @",
        lex_pos=4,
        line=1,
        column=5
    )
    uce.get_context = MagicMock(return_value="Context around error")
    
    def mock_operation():
        raise uce
    
    with pytest.raises(UnexpectedCharacterError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "unexpected_character"
    assert error.context["context"] == "Context around error"
    assert error.context["line"] == 1
    assert error.context["column"] == 5


def test_parsing_error_handling_unexpected_eof():
    """Test handling UnexpectedEOF exception."""
    expression = "x + "
    parse_func = MagicMock()
    
    # Create a mock UnexpectedEOF exception
    eof = UnexpectedEOF(expected={"VARIABLE", "NUMBER"})
    
    def mock_operation():
        raise eof
    
    with pytest.raises(UnexpectedEOFError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "unexpected_eof"
    assert set(error.context["expected"]) == {"VARIABLE", "NUMBER"}


def test_parsing_error_handling_other_exception():
    """Test that other exceptions are not caught."""
    expression = "x + y"
    parse_func = MagicMock()
    
    def mock_operation():
        raise ValueError("Some other error")
    
    with pytest.raises(ValueError):
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()


# Integration tests for the complete parsing error workflow
def test_full_workflow_unexpected_token():
    """Test the complete workflow from UnexpectedToken to formatted error."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Create a realistic UnexpectedToken exception
    token = MagicMock()
    token.type = "PLUS"
    token.value = "+"
    token.line = 1
    token.column = 5
    
    interactive_parser = MagicMock()
    interactive_parser.accepts.return_value = {"VARIABLE", "NUMBER"}
    
    ute = UnexpectedToken(
        token=token,
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=interactive_parser,
        state=MagicMock()
    )
    ute.get_context = MagicMock(return_value="x + +\n    ^")
    ute.match_examples = MagicMock(return_value="trailing_operator")
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    
    # Check that all the error context is properly set
    assert error.template_key == "trailing_operator"
    assert error.context["details"] == str(ute)
    assert error.context["context"] == "x + +\n    ^"
    assert error.context["line"] == 1
    assert error.context["column"] == 5
    assert isinstance(error.context["suggestions"], list)
    assert len(error.context["suggestions"]) > 0


def test_full_workflow_unexpected_characters():
    """Test the complete workflow from UnexpectedCharacters to formatted error."""
    expression = "x + @"
    parse_func = MagicMock()
    
    uce = UnexpectedCharacters(
        seq="x + @",
        lex_pos=4,
        line=1,
        column=5
    )
    uce.get_context = MagicMock(return_value="x + @\n    ^")
    
    def mock_operation():
        raise uce
    
    with pytest.raises(UnexpectedCharacterError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    
    # Check that all the error context is properly set
    assert error.template_key == "unexpected_character"
    assert error.context["details"] == str(uce)
    assert error.context["context"] == "x + @\n    ^"
    assert error.context["line"] == 1
    assert error.context["column"] == 5


def test_full_workflow_unexpected_eof():
    """Test the complete workflow from UnexpectedEOF to formatted error."""
    expression = "x + "
    parse_func = MagicMock()
    
    eof = UnexpectedEOF(expected={"VARIABLE", "NUMBER"})
    
    def mock_operation():
        raise eof
    
    with pytest.raises(UnexpectedEOFError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    
    # Check that all the error context is properly set
    assert error.template_key == "unexpected_eof"
    assert error.context["details"] == str(eof)
    assert set(error.context["expected"]) == {"VARIABLE", "NUMBER"}


def test_error_examples_integration():
    """Test that ERROR_EXAMPLES integration works correctly."""
    expression = "x + +"
    parse_func = MagicMock()
    
    # Mock the match_examples to return a specific pattern
    token = MagicMock()
    token.type = "PLUS"
    token.value = "+"
    token.line = 1
    token.column = 5
    
    ute = UnexpectedToken(
        token=token,
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock(),
        state=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context")
    ute.match_examples = MagicMock(return_value="trailing_operator")
    ute.interactive_parser.accepts.return_value = {"VARIABLE"}
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "trailing_operator"
    
    # Verify that match_examples was called with the correct arguments
    ute.match_examples.assert_called_once_with(parse_func, parsing.ERROR_EXAMPLES)


# Test various scenarios with ERROR_EXAMPLES mocking
def test_match_examples_returns_none():
    """Test when match_examples returns None."""
    expression = "x + +"
    parse_func = MagicMock()
    
    token = MagicMock()
    token.type = "PLUS"
    token.value = "+"
    token.line = 1
    token.column = 5
    
    ute = UnexpectedToken(
        token=token,
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock(),
        state=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context")
    ute.match_examples = MagicMock(return_value=None)  # Returns None
    ute.interactive_parser.accepts.return_value = {"VARIABLE"}
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    with pytest.raises(UnexpectedTokenError) as exc_info:
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
    
    error = exc_info.value
    assert error.template_key == "unexpected_token"  # Falls back to default


def test_match_examples_raises_exception():
    """Test when match_examples raises an exception."""
    expression = "x + +"
    parse_func = MagicMock()
    
    token = MagicMock()
    token.type = "PLUS"
    token.value = "+"
    token.line = 1
    token.column = 5
    
    ute = UnexpectedToken(
        token=token,
        expected={"VARIABLE", "NUMBER"},
        interactive_parser=MagicMock(),
        state=MagicMock()
    )
    ute.get_context = MagicMock(return_value="Context")
    ute.match_examples = MagicMock(side_effect=Exception("Match failed"))
    ute.interactive_parser.accepts.return_value = {"VARIABLE"}
    ute.line = 1
    ute.column = 5
    
    def mock_operation():
        raise ute
    
    # The match_examples exception should propagate (not caught by parsing_error_handling)
    with pytest.raises(Exception, match="Match failed"):
        with parsing.parsing_error_handling(expression, parse_func):
            mock_operation()
