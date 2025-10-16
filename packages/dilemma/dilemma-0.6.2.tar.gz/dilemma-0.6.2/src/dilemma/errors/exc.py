"""
Exception classes for the Dilemma expression language.
"""

from typing import Optional

from .messages import format_error


class DilemmaError(Exception):
    """Base exception for all Dilemma-specific errors."""

    template_key: Optional[str] = None  # Template key to use from error_messages

    def __init__(self, *args, template_key: Optional[str] = None, **context):
        """
        Initialize a Dilemma error with optional template and context.

        Args:
            *args: Positional arguments for the standard Exception
            template_key: Key to use for the error template lookup
            **context: Context variables to inject into the error template
        """
        self.template_key = template_key or self.template_key
        self.context = context
        self.help = None

        # Format the error message if we have a template
        if self.template_key:
            formatted_msg = format_error(self.template_key, **context)
            self.help = formatted_msg
            super().__init__(formatted_msg, *args[1:] if args else [])
        else:
            super().__init__(*args)


class SyntaxError(DilemmaError):
    """Error raised for syntax problems in expressions."""

    template_key = "syntax_error"


class VariableError(DilemmaError):
    """Error raised for issues with variables."""

    template_key = "undefined_variable"


class TypeMismatchError(DilemmaError):
    """Error raised when operands have incompatible types."""

    template_key = "type_mismatch"


class ContainerError(DilemmaError):
    """Error raised for invalid container operations."""

    template_key = "invalid_container"


class DateTimeError(DilemmaError):
    """Error raised for date-time related issues."""

    template_key = "date_parsing"


class EvaluationError(DilemmaError):
    """Error raised for general evaluation issues."""

    template_key = "evaluation_error"


class UnexpectedTokenError(SyntaxError):
    """Error raised when an unexpected token is encountered."""

    template_key = "unexpected_token"


class UnexpectedCharacterError(SyntaxError):
    """Error raised when an unexpected character is encountered."""

    template_key = "unexpected_character"


class UnexpectedEOFError(SyntaxError):
    """Error raised when input ends unexpectedly."""

    template_key = "unexpected_eof"
