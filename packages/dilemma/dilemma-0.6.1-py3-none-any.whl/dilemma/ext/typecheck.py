"""
Type validation for Dilemma expressions using JSON Schema.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from lark import Lark, Transformer, Token
from datetime import datetime


# Type definitions
TypeInfo = Union[str, List[str]]  # e.g., "number", ["number", "string"], "datetime"


class TypeValidator(Transformer):
    """
    Walks expression trees to validate type compatibility using JSON Schema.
    Instead of computing values, this transformer tracks and validates types.
    """

    def __init__(self, schema: Dict[str, Any]):
        super().__init__()
        self.schema = schema
        # Map of basic JSON schema types to Python types
        self.type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            # Custom type for dates
            "datetime": datetime,
        }

    def get_variable_type(self, path: str) -> TypeInfo:
        """
        Get expected type for a variable path using JSON Schema.

        Args:
            path: Variable path (e.g., "user.profile.age")

        Returns:
            Type information for the variable

        Raises:
            ValueError: If path cannot be resolved in schema
        """
        # Split path into components
        components = path.split(".")
        current = self.schema

        # Navigate through schema properties
        for component in components:
            # Handle array indexing
            if "[" in component:
                name = component.split("[")[0]
                if name not in current.get("properties", {}):
                    raise ValueError(f"Cannot find '{name}' in schema")
                # For arrays, check items type
                current = current["properties"][name]
                if current.get("type") != "array":
                    raise ValueError(f"Expected array type for '{name}'")
                current = current.get("items", {})
            else:
                # Regular property
                if component not in current.get("properties", {}):
                    raise ValueError(f"Cannot find '{component}' in schema")
                current = current["properties"][component]

        # Extract type information
        type_info = current.get("type")
        if type_info is None:
            # Check for format hint for datetime
            if current.get("format") in ("date", "date-time"):
                return "datetime"
            raise ValueError(f"No type information for '{path}'")

        return type_info

    def is_compatible(
        self, left_type: TypeInfo, right_type: TypeInfo, operation: str
    ) -> bool:
        """Check if types are compatible for the given operation."""
        # Handle union types (lists of possible types)
        if isinstance(left_type, list):
            return any(self.is_compatible(t, right_type, operation) for t in left_type)
        if isinstance(right_type, list):
            return any(self.is_compatible(left_type, t, operation) for t in right_type)

        # Basic arithmetic operations
        if operation in ("+", "-", "*", "/"):
            return left_type in ("number", "integer") and right_type in (
                "number",
                "integer",
            )

        # Equality operations
        if operation in ("==", "!="):
            # Most types can be compared for equality
            return True

        # Comparison operations
        if operation in ("<", ">", "<=", ">="):
            # Numeric comparisons
            if left_type in ("number", "integer") and right_type in ("number", "integer"):
                return True
            # String comparisons (lexicographic)
            if left_type == "string" and right_type == "string":
                return True
            # Date comparisons
            if left_type == "datetime" and right_type == "datetime":
                return True
            return False

        # Logical operations
        if operation in ("and", "or"):
            return left_type == "boolean" and right_type == "boolean"

        # Contains/in operations
        if operation == "in" or operation == "contains":
            if left_type == "string" and right_type == "string":  # substring check
                return True
            if right_type == "array":  # membership check
                return True
            return False

        # Date operations
        if operation in ("before", "after", "same_day_as"):
            return left_type == "datetime" and right_type == "datetime"

        # Pattern matching
        if operation == "like":
            return left_type == "string" and right_type == "string"

        # Default: assume incompatible
        return False

    # Transformer methods that mirror the evaluation transformer

    def int_number(self, items: List[Token]) -> TypeInfo:
        return "integer"

    def float_number(self, items: List[Token]) -> TypeInfo:
        return "number"

    def negative_int(self, items: List[Token]) -> TypeInfo:
        return "integer"

    def negative_float(self, items: List[Token]) -> TypeInfo:
        return "number"

    def true_value(self, _) -> TypeInfo:
        return "boolean"

    def false_value(self, _) -> TypeInfo:
        return "boolean"

    def variable(self, items: List[Token]) -> TypeInfo:
        """Get the type of a variable from the schema."""
        var_path = items[0].value
        try:
            return self.get_variable_type(var_path)
        except ValueError as e:
            raise TypeError(f"Type error for variable '{var_path}': {str(e)}")

    def string_literal(self, items: List[Token]) -> TypeInfo:
        return "string"

    def add(self, items: List[TypeInfo]) -> TypeInfo:
        """Addition operator - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "+"):
            raise TypeError(f"Cannot add types {items[0]} and {items[1]}")

        # String concatenation case
        if items[0] == "string" and items[1] == "string":
            return "string"

        # Numeric addition case
        return "number"

    def sub(self, items: List[TypeInfo]) -> TypeInfo:
        """Subtraction operator - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "-"):
            raise TypeError(f"Cannot subtract types {items[0]} and {items[1]}")
        return "number"

    def mul(self, items: List[TypeInfo]) -> TypeInfo:
        """Multiplication operator - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "*"):
            raise TypeError(f"Cannot multiply types {items[0]} and {items[1]}")
        return "number"

    def div(self, items: List[TypeInfo]) -> TypeInfo:
        """Division operator - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "/"):
            raise TypeError(f"Cannot divide types {items[0]} and {items[1]}")
        return "number"

    def paren(self, items: List[TypeInfo]) -> TypeInfo:
        """Parenthesis just returns the inner type."""
        return items[0]

    # Comparison operations - all return boolean

    def eq(self, items: List[TypeInfo]) -> TypeInfo:
        """Equality comparison - most types can be compared."""
        return "boolean"

    def ne(self, items: List[TypeInfo]) -> TypeInfo:
        """Inequality comparison - most types can be compared."""
        return "boolean"

    def lt(self, items: List[TypeInfo]) -> TypeInfo:
        """Less than comparison - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "<"):
            raise TypeError(f"Cannot compare types {items[0]} and {items[1]} with '<'")
        return "boolean"

    def gt(self, items: List[TypeInfo]) -> TypeInfo:
        """Greater than comparison - check type compatibility."""
        if not self.is_compatible(items[0], items[1], ">"):
            raise TypeError(f"Cannot compare types {items[0]} and {items[1]} with '>'")
        return "boolean"

    def le(self, items: List[TypeInfo]) -> TypeInfo:
        """Less than or equal - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "<="):
            raise TypeError(f"Cannot compare types {items[0]} and {items[1]} with '<='")
        return "boolean"

    def ge(self, items: List[TypeInfo]) -> TypeInfo:
        """Greater than or equal - check type compatibility."""
        if not self.is_compatible(items[0], items[1], ">="):
            raise TypeError(f"Cannot compare types {items[0]} and {items[1]} with '>='")
        return "boolean"

    # Logical operations

    def and_op(self, items: List[TypeInfo]) -> TypeInfo:
        """Logical AND - both sides must be boolean."""
        if not (items[0] == "boolean" and items[1] == "boolean"):
            raise TypeError("Logical AND requires boolean operands")
        return "boolean"

    def or_op(self, items: List[TypeInfo]) -> TypeInfo:
        """Logical OR - both sides must be boolean."""
        if not (items[0] == "boolean" and items[1] == "boolean"):
            raise TypeError("Logical OR requires boolean operands")
        return "boolean"

    def contains(self, items: List[TypeInfo]) -> TypeInfo:
        """Contains operation (in) - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "in"):
            raise TypeError(f"Cannot check if {items[0]} is in {items[1]}")
        return "boolean"

    def contained_in(self, items: List[TypeInfo]) -> TypeInfo:
        """Contains operation - check type compatibility."""
        if not self.is_compatible(items[0], items[1], "contains"):
            raise TypeError(f"Cannot check if {items[0]} contains {items[1]}")
        return "boolean"

    def pattern_match(self, items: List[TypeInfo]) -> TypeInfo:
        """Pattern matching - both sides must be strings."""
        if not (items[0] == "string" and items[1] == "string"):
            raise TypeError("Pattern matching requires string operands")
        return "boolean"

    def jq_expression(self, items: List[Token]) -> TypeInfo:
        """
        JQ expressions are difficult to type check without executing.
        We'll allow them but warn about potential type issues.
        """
        import warnings

        warnings.warn(f"Type validation for JQ expression '{items[0].value}' skipped")
        return ["string", "number", "boolean", "array", "object"]  # Could be any type

    # Date operations

    def date_is_past(self, items: List[TypeInfo]) -> TypeInfo:
        """Date is past - operand must be a date."""
        if items[0] != "datetime":
            raise TypeError(f"'is past' requires datetime operand, got {items[0]}")
        return "boolean"

    def date_is_future(self, items: List[TypeInfo]) -> TypeInfo:
        """Date is future - operand must be a date."""
        if items[0] != "datetime":
            raise TypeError(f"'is future' requires datetime operand, got {items[0]}")
        return "boolean"

    def date_is_today(self, items: List[TypeInfo]) -> TypeInfo:
        """Date is today - operand must be a date."""
        if items[0] != "datetime":
            raise TypeError(f"'is today' requires datetime operand, got {items[0]}")
        return "boolean"

    def date_within(self, items: List) -> TypeInfo:
        """Date within - first operand must be a date."""
        if items[0] != "datetime":
            raise TypeError(f"'within' requires datetime operand, got {items[0]}")
        return "boolean"

    def date_older_than(self, items: List) -> TypeInfo:
        """Date older than - first operand must be a date."""
        if items[0] != "datetime":
            raise TypeError(f"'older than' requires datetime operand, got {items[0]}")
        return "boolean"

    def date_before(self, items: List[TypeInfo]) -> TypeInfo:
        """Date before - both operands must be dates."""
        if not (items[0] == "datetime" and items[1] == "datetime"):
            raise TypeError(
                f"'before' requires datetime operands, got {items[0]} and {items[1]}"
            )
        return "boolean"

    def date_after(self, items: List[TypeInfo]) -> TypeInfo:
        """Date after - both operands must be dates."""
        if not (items[0] == "datetime" and items[1] == "datetime"):
            raise TypeError(
                f"'after' requires datetime operands, got {items[0]} and {items[1]}"
            )
        return "boolean"

    def date_same_day(self, items: List[TypeInfo]) -> TypeInfo:
        """Date same day - both operands must be dates."""
        if not (items[0] == "datetime" and items[1] == "datetime"):
            raise TypeError(
                f"'same_day_as' requires datetime operands, got {items[0]} and {items[1]}"
            )
        return "boolean"


def validate_expression_types(
    expression: str, schema: Dict[str, Any], parser: Lark
) -> Tuple[bool, Optional[str]]:
    """
    Validate expression types against a JSON schema.

    Args:
        expression: The expression to validate
        schema: JSON Schema describing variable types
        parser: Lark parser for the expression language

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Parse the expression
        parse_tree = parser.parse(expression)

        # Create type validator
        validator = TypeValidator(schema)

        # Validate types
        result_type = validator.transform(parse_tree)

        # The final result should normally be a boolean
        if result_type != "boolean":
            return False, f"Expression result type should be boolean, got {result_type}"

        return True, None
    except TypeError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error validating expression: {str(e)}"
