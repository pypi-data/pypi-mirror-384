from typing import Callable
from contextlib import contextmanager

from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedToken


from .examples import ERROR_EXAMPLES
from ..logconf import get_logger
from .exc import UnexpectedCharacterError, UnexpectedEOFError, UnexpectedTokenError


log = get_logger(__name__)


def suggest_correction(interactive_parser, token):
    """
    Suggest possible corrections based on expected tokens at the error position.

    Args:
        interactive_parser: Lark's InteractiveParser instance from UnexpectedToken
                           exception. This parser maintains the state at the point
                           of failure and can tell us what tokens would have been
                           accepted at that position.
        token: The token that caused the error. Contains information about the
              actual token received (type, value, line, column).

    Returns:
        list: Suggestions for how to fix the error, based on what tokens
              were expected at this position in the grammar.

    Notes:
        The interactive_parser.accepts() method returns a set of terminal names
        that would have been valid at the error position. This can be used to
        create context-aware suggestions like "Did you mean to use '+' instead
        of ','?" or "Variable names cannot be reserved keywords like 'and'."
    """
    suggestions = []
    if interactive_parser:
        accepts = interactive_parser.accepts()

        # Map cryptic token names to user-friendly suggestions
        token_suggestions = {
            "PLUS": "+ (plus)",
            "MINUS": "- (minus)",
            "MULT": "* (multiply)",
            "DIV": "/ (divide)",
            "LPAR": "( (opening parenthesis)",
            "RPAR": ") (closing parenthesis)",
            "RESOLVER_EXPR": "backticked expression (`expression`)",
            "FUNC_NAME": "function name (count_of, any_of, all_of, none_of)",
            "__ANON_8": "$now (current datetime)",
            "TRUE": "true",
            "FALSE": "false",
            "VARIABLE": "variable name",
            "STRING": "quoted string",
            "INTEGER": "integer number",
            "FLOAT": "decimal number",
            "EXACTLY": "exactly (for quantified expressions)",
            "ANY": "any (for quantified expressions)",
            "ALL": "all (for quantified expressions)",
            "NONE": "none (for quantified expressions)",
            "AT": "at (for 'at least'/'at most' expressions)",
        }

        # Generate readable suggestions
        readable = [token_suggestions.get(t, t) for t in accepts]
        if readable:
            suggestions.append(f"Expected: {', '.join(readable)}")

        # Suggest corrections for common mistakes
        if token.type == "VARIABLE" and any(kw in accepts for kw in ["AND", "OR"]):
            suggestions.append(
                f"'{token.value}' might be a reserved keyword. Try quoting it."
            )

    return suggestions


@contextmanager
def parsing_error_handling(expression: str, parse_func: Callable):
    """
    Handle syntax and parsing errors with useful context and suggestions.

    Args:
        expression: The expression string being parsed
        parse_func: A callable that takes an expression string and returns
                   a parse tree, typically parser.parse from a Lark parser
    """
    try:
        yield
    except UnexpectedToken as ute:
        error_context = ute.get_context(expression)
        error_pattern = None
        log.debug("Caught lark UnexpectedToken Exception %s", ute)

        if hasattr(ute, "state") and ute.state is not None:
            log.debug("Found state on UnexpectedToken - attempting to match_examples")
            error_pattern = ute.match_examples(parse_func, ERROR_EXAMPLES)
        else:
            log.debug("No state found on UnexpectedToken")

        suggestions = (
            suggest_correction(ute.interactive_parser, ute.token)
            if ute.interactive_parser
            else []
        )

        raise UnexpectedTokenError(
            template_key=error_pattern or "unexpected_token",
            details=str(ute),
            context=error_context,
            line=ute.line,
            column=ute.column,
            token_value=ute.token.value,
            suggestions=suggestions,
        )
    except UnexpectedCharacters as uce:
        log.debug("Caught lark UnexpectedCharacters Exception %s", uce)
        error_context = uce.get_context(expression)
        raise UnexpectedCharacterError(
            template_key="unexpected_character",
            details=str(uce),
            context=error_context,
            line=uce.line,
            column=uce.column,
        )
    except UnexpectedEOF as eof:
        raise UnexpectedEOFError(
            template_key="unexpected_eof", details=str(eof), expected=list(eof.expected)
        )
