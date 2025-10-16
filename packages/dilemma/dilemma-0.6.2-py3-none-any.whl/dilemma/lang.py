"""
Expression language implementation using Lark
"""

import json
import threading
import fnmatch
from datetime import datetime
from typing import Union

from lark import Token
from lark import Lark, Transformer

from .errors import (
    execution_error_handling,
    parsing_error_handling,
    ContainerError,
    TypeMismatchError,
    DilemmaError,
)

from .dates import DateMethods, DateTimeEncoder
from .logconf import get_logger
from .resolvers import resolve_path
from .utils import (
    binary_op,
    both_strings,
    reject_strings,
    check_containment,
)
from .arraymethods import ArrayMethods

log = get_logger(__name__)

# ruff: noqa: E501
grammar = r"""

    ?start: expr

    ?expr: or_expr

    ?or_expr: and_expr
            | or_expr "or" and_expr -> or_op

    ?and_expr: comparison
             | and_expr "and" comparison -> and_op

    ?comparison: sum
               | sum "==" sum -> eq
               | sum "!=" sum -> ne
               | sum "is" sum -> eq
               | sum "is" "not" sum -> ne
               | sum "<" sum -> lt
               | sum ">" sum -> gt
               | sum "<=" sum -> le
               | sum ">=" sum -> ge
               | sum "in" sum -> contains
               | sum "contains" sum -> contained_in
               | sum "has" sum -> has_property
               | sum "like" sum -> pattern_match
               | sum "not" "like" sum -> pattern_not_match
               | sum "is" "$past" -> date_is_past
               | sum "is" "$future" -> date_is_future
               | sum "is" "$today" -> date_is_today
               | sum "is" "$empty" -> is_empty
               | sum "upcoming" "within" sum time_unit -> date_upcoming_within
               | sum "older" "than" sum time_unit -> date_older_than
               | sum "before" sum -> date_before
               | sum "after" sum -> date_after
               | sum "same_day_as" sum -> date_same_day

    ?sum: product
       | sum "+" product -> add
       | sum "-" product -> sub

    ?product: term
           | product "*" term -> mul
           | product "/" term -> div

    ?term: INTEGER -> int_number
         | FLOAT -> float_number
         | STRING -> string_literal
         | "-" INTEGER -> negative_int
         | "-" FLOAT -> negative_float
         | "true" -> true_value
         | "false" -> false_value
         | "$now" -> now_value
         | func_call
         | array_quantified
         | VARIABLE -> variable
         | RESOLVER_EXPR -> resolver_expression
         | "(" expr ")" -> paren

    ?array_quantified: "at" "least" INTEGER "of" expr ("match" | "matches") ARRAY_EXPR      -> at_least_of
                     | "at" "most"  INTEGER "of" expr ("match" | "matches") ARRAY_EXPR      -> at_most_of
                     | "exactly"    INTEGER "of" expr ("match" | "matches") ARRAY_EXPR      -> exactly_of
                     | "any"  "of" expr ("match" | "matches") ARRAY_EXPR                    -> any_of_sugar
                     | "all"  "of" expr ("match" | "matches") ARRAY_EXPR                    -> all_of_sugar
                     | "none" "of" expr ("match" | "matches") ARRAY_EXPR                    -> none_of_sugar

    // Define reserved keywords
    // But use string literals in rules above for "or", "and", "True", "False"
    // Use a negative lookahead in VARIABLE to exclude these as variable names

    FUNC_NAME: /(count_of|any_of|all_of|none_of)/

    VARIABLE: /(?!or\b|and\b|true\b|false\b|is\b|contains\b|like\b|in\b|has\b|match\b|matches\b|count_of\b|any_of\b|all_of\b|none_of\b)[a-zA-Z_][a-zA-Z0-9_]*(?:'s\s+[a-zA-Z_][a-zA-Z0-9_]*|\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*/

    func_call: FUNC_NAME "(" expr ("," RESOLVER_EXPR)? ")"

    // Array expression syntax: |expression| - must be matched as a single token
    // Used for array quantified expressions to avoid conflicts with jq syntax
    ARRAY_EXPR: /\|[^|]*\|/

    // JQ expression syntax: `expression` - must be matched as a single token
    // Define this before the STRING token to give it higher precedence
    RESOLVER_EXPR: /`[^`]*`/

    INTEGER: /[0-9]+/
    FLOAT: /([0-9]+\.[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?|[0-9]+[eE][-+]?[0-9]+/i
    STRING: /"(\\.|[^\\"])*"|\'(\\.|[^\\\'])*\'/

    ?time_unit: "minute" -> minute_unit
             | "minutes" -> minute_unit
             | "hour" -> hour_unit
             | "hours" -> hour_unit
             | "day" -> day_unit
             | "days" -> day_unit
             | "week" -> week_unit
             | "weeks" -> week_unit
             | "month" -> month_unit
             | "months" -> month_unit
             | "year" -> year_unit
             | "years" -> year_unit

    %import common.WS
    %ignore WS
"""


MAX_STRING_LENGTH = 10000  # Define a reasonable maximum length


# Transformer to evaluate expressions
class ExpressionTransformer(Transformer, DateMethods, ArrayMethods):
    # Epsilon value for float comparison
    EPSILON = 1e-10

    def __init__(self, processed_json: dict | None = None):
        super().__init__()
        self.processed_json = processed_json or {}

    def int_number(self, items: list[Token]) -> int:
        return int(items[0])

    def float_number(self, items: list[Token]) -> float:
        return float(items[0])

    def negative_int(self, items: list[Token]) -> int:
        return -int(items[0])

    def negative_float(self, items: list[Token]) -> float:
        return -float(items[0])

    def true_value(self, _) -> bool:
        return True

    def false_value(self, _) -> bool:
        return False

    def variable(
        self, items: list[Token]
    ) -> int | float | bool | str | list | dict | datetime:
        var_path = items[0].value

        value = resolve_path(var_path, self.processed_json, raw=False)

        # Handle datetime reconstruction
        if isinstance(value, dict) and "__datetime__" in value:
            return datetime.fromisoformat(value["__datetime__"])

        return value

    @binary_op
    def add(self, left, right):
        """Addition operator (+) - allows string concatenation with limits"""
        # Allow string concatenation only when both operands are strings
        if both_strings(left, right):
            result = left + right
            if len(result) > MAX_STRING_LENGTH:
                raise TypeMismatchError(
                    template_key="string_length", max_length=MAX_STRING_LENGTH
                )
            return result

        # Prevent mixing strings with other types
        if isinstance(left, str) or isinstance(right, str):
            raise TypeMismatchError(template_key="string_mix", operation="+")

        # Regular addition for non-string types
        return left + right

    @binary_op
    def sub(self, left, right):
        """Subtraction operator (-) - deny for strings"""
        reject_strings(left, right, "-")
        return left - right

    @binary_op
    def mul(self, left, right):
        """Multiplication operator (*) - deny for strings"""
        reject_strings(left, right, "*")
        return left * right

    @binary_op
    def div(self, left, right):
        """Division operator (/) - deny for strings"""
        reject_strings(left, right, "/")
        if right == 0:
            raise DilemmaError(template_key="zero_division", left=left, right=right)
        return left / right  # Now using true division

    def paren(self, items: list) -> float:
        """Handle parenthesized expressions by returning the inner value"""
        return items[0]

    def string_literal(self, items: list[Token]) -> str:
        # Remove surrounding quotes and unescape
        return items[0][1:-1].encode("utf-8").decode("unicode_escape")

    # Comparison operations
    @binary_op
    def eq(self, left, right) -> bool:
        """Check if two items are equal, with special handling for different types"""

        # float is special case
        if isinstance(left, float) or isinstance(right, float):
            return abs(left - right) < self.EPSILON

        return left == right

    @binary_op
    def ne(self, left, right) -> bool:
        """Check if two items are not equal, with special handling for float comparison"""
        return not self.eq(left, right)

    @binary_op
    def lt(self, left, right) -> bool:
        return left < right

    @binary_op
    def gt(self, left, right) -> bool:
        return left > right

    @binary_op
    def le(self, left, right) -> bool:
        return left <= right

    @binary_op
    def ge(self, left, right) -> bool:
        return left >= right

    # Logical operations
    @binary_op
    def and_op(self, left, right) -> bool:
        return bool(left) and bool(right)

    @binary_op
    def or_op(self, left, right) -> bool:
        return bool(left) or bool(right)

    @binary_op
    def contains(self, left, right) -> bool:
        """Check if the left operand is contained in the right operand (container)"""
        return check_containment(container=right, item=left, container_position="in")

    @binary_op
    def contained_in(self, left, right) -> bool:
        """Check if the right operand is contained in the left operand (container)"""
        return check_containment(
            container=left, item=right, container_position="contains"
        )

    @binary_op
    def has_property(self, left, right) -> bool:
        """
        Check if the left operand (object) has the right operand as a property/key.

        This is similar to 'in' but with more natural syntax: object has property
        instead of property in object.

        Examples:
        - user has 'name'      -> checks if user object has a 'name' key
        - config has debug     -> checks if config object has a 'debug' key
        - user has field_name  -> checks using variable field_name as key
        """
        if isinstance(left, dict):
            # For dictionaries, check if the key exists
            return right in left
        elif isinstance(left, (list, tuple)):
            # For lists/tuples, check if the item exists in the collection
            return right in left
        else:
            # For other types, return False (they don't have properties)
            return False

    @binary_op
    def pattern_match(self, left, right) -> bool:
        """
        Implements case-insensitive wildcard pattern matching using fnmatch.

        Example: 'filename.txt' matches '*.txt'
        """
        if not both_strings(left, right):
            raise TypeError("Pattern matching requires string operands")

        string = left.lower()
        pattern = right.lower()

        return fnmatch.fnmatch(string, pattern)

    @binary_op
    def pattern_not_match(self, left, right) -> bool:
        """
        Implements negated case-insensitive wildcard pattern matching.
        Returns true when the string does NOT match the pattern.

        Example: 'document.doc' does not match '*.txt'
        """

        return not self.pattern_match(left, right)

    def is_empty(self, items: list) -> bool:
        """Check if a container (list or dict) is empty."""
        value = items[0]
        if isinstance(value, (list, tuple, dict)):
            return len(value) == 0
        else:
            raise ContainerError(template_key="wrong_container", operation="is $empty")

    def resolver_expression(
        self, items: list[Token]
    ) -> int | float | bool | str | list | dict | datetime:
        """Process a backticked expression using the configured resolver"""
        # Extract the expression from the token: `expression` -> expression
        raw_expr = items[0].value[1:-1]  # Remove ` prefix and ` suffix

        # Use the resolver system to evaluate with raw=True
        value = resolve_path(raw_expr, self.processed_json, raw=True)

        # Handle datetime reconstruction
        if isinstance(value, dict) and "__datetime__" in value:
            return datetime.fromisoformat(value["__datetime__"])

        return value

    # Array quantified sugar methods
    def at_least_of(self, items):
        """Transform 'at least N of X has P' to count_of(X, P) >= N"""
        n, coll, pred = int(items[0]), items[1], items[2]
        return self.func_call([Token("FUNC_NAME", "count_of"), coll, pred]) >= n

    def at_most_of(self, items):
        """Transform 'at most N of X has P' to count_of(X, P) <= N"""
        n, coll, pred = int(items[0]), items[1], items[2]
        return self.func_call([Token("FUNC_NAME", "count_of"), coll, pred]) <= n

    def exactly_of(self, items):
        """Transform 'exactly N of X has P' to count_of(X, P) == N"""
        n, coll, pred = int(items[0]), items[1], items[2]
        return self.func_call([Token("FUNC_NAME", "count_of"), coll, pred]) == n

    def any_of_sugar(self, items):
        """Transform 'any of X has P' to any_of(X, P)"""
        coll, pred = items[0], items[1]
        return self.func_call([Token("FUNC_NAME", "any_of"), coll, pred])

    def all_of_sugar(self, items):
        """Transform 'all of X has P' to all_of(X, P)"""
        coll, pred = items[0], items[1]
        return self.func_call([Token("FUNC_NAME", "all_of"), coll, pred])

    def none_of_sugar(self, items):
        """Transform 'none of X has P' to none_of(X, P)"""
        coll, pred = items[0], items[1]
        return self.func_call([Token("FUNC_NAME", "none_of"), coll, pred])


# Thread-local storage for the parser
_thread_local = threading.local()


def build_parser() -> Lark:
    """
    Returns a thread-local instance of the Lark parser.
    Ensures thread safety by creating a separate parser for each thread.
    """
    if not hasattr(_thread_local, "parser"):
        log.info("Building parser from grammar and assigning to thread local")
        _thread_local.parser = Lark(grammar, start="expr", parser="lalr")
    return _thread_local.parser


class CompiledExpression:
    """
    Represents a pre-compiled expression that can be evaluated multiple times
    with different variable contexts for improved performance.
    """

    def __init__(self, expression: str, parse_tree):
        self.expression = expression
        self.parse_tree = parse_tree

    def evaluate(
        self, context: Union[dict, str, "ProcessedContext", None] = None
    ) -> Union[int, float, bool, str]:
        """
        Evaluate this compiled expression with the provided context.

        Args:
            context: Dictionary, JSON string, or ProcessedContext containing variable values

        Returns:
            The result of evaluating the expression
        """
        processed_json = _extract_processed_json(context)

        with execution_error_handling(self.expression):
            transformer = ExpressionTransformer(processed_json=processed_json)
            return transformer.transform(self.parse_tree)


class ProcessedContext:
    """
    Represents a pre-processed variable context that can be reused across multiple
    expression evaluations for improved performance.

    This class encapsulates the JSON round-trip safety processing, allowing you to
    process variables once and reuse the safe representation multiple times.
    """

    def __init__(self, variables: dict | str | None = None):
        """
        Process variables into a safe, JSON-compatible format.

        Args:
            variables: Dictionary or JSON string containing variable values
        """
        self.processed_json = _process_variables(variables)

    def get_processed_json(self) -> dict:
        """Return the processed JSON object."""
        return self.processed_json


# Helper function to process variables
def _process_variables(variables: dict | str | None = None) -> dict:
    """
    Process variables into a standardized JSON-compatible format.

    Args:
        variables: Dictionary or JSON string containing variable values

    Returns:
        Processed JSON object ready for expression evaluation

    Raises:
        ValueError: If the variables cannot be processed
    """
    processed_json = {}
    if variables:
        try:
            if isinstance(variables, str):
                # Parse JSON string directly
                processed_json = json.loads(variables)
            else:
                # Convert dictionary to JSON-compatible structure
                processed_json = json.loads(json.dumps(variables, cls=DateTimeEncoder))
        except (TypeError, json.JSONDecodeError) as e:
            raise DilemmaError(template_key="variables_processing", details=str(e))
    return processed_json


def _extract_processed_json(
    context: Union[dict, str, "ProcessedContext", None] = None,
) -> dict:
    """
    Extract processed JSON from various context types.

    Args:
        context: Raw variables, JSON string, or ProcessedContext instance

    Returns:
        Processed JSON object ready for expression evaluation
    """
    if isinstance(context, ProcessedContext):
        return context.get_processed_json()
    else:
        return _process_variables(context)


def compile_expression(expression: str) -> CompiledExpression:
    """
    Compile an expression into a reusable CompiledExpression object that can be
    evaluated multiple times with different variable contexts.

    Args:
        expression: The expression string to compile

    Returns:
        A CompiledExpression object that can be evaluated with different contexts

    Raises:
        ValueError: If the expression has invalid syntax
    """
    parser = build_parser()
    with parsing_error_handling(expression, parser.parse):
        tree = parser.parse(expression)
        return CompiledExpression(expression, tree)


# Function to evaluate expressions
def evaluate(
    expression: str, context: Union[dict, str, "ProcessedContext", None] = None
) -> Union[int, float, bool, str]:
    """
    Evaluate an expression against the given context.

    Args:
        expression: The expression string to evaluate
        context: Dictionary, JSON string, or ProcessedContext containing variable values

    For better performance when evaluating the same expression multiple times with
    different variable contexts, use compile_expression().
    """

    processed_json = _extract_processed_json(context)
    parser = build_parser()

    with parsing_error_handling(expression, parser.parse):
        tree = parser.parse(expression)

    with execution_error_handling(expression):
        transformer = ExpressionTransformer(processed_json=processed_json)
        return transformer.transform(tree)
