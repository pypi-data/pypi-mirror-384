from lark import Transformer
from dilemma.lang import build_parser


class IndentedHumanReadableTransformer(Transformer):
    """
    Walks the parse tree of an expression and generates a human-readable description
    as a structured, indented list.
    """

    def __init__(self):
        super().__init__()
        self.indentation_level = 0

    def _indent(self, text):
        return "    " * self.indentation_level + text

    def int_number(self, items):
        return str(items[0])

    def float_number(self, items):
        return str(items[0])

    def negative_int(self, items):
        return f"negative {items[0]}"

    def negative_float(self, items):
        return f"negative {items[0]}"

    def true_value(self, _):
        return "True"

    def false_value(self, _):
        return "False"

    def string_literal(self, items):
        return f'"{items[0]}"'

    def variable(self, items):
        return f"the value of '{items[0]}'"

    def add(self, items):
        return self._indent(f"the sum of:\n{items[0]}\n{items[1]}")

    def sub(self, items):
        return self._indent(f"the difference between:\n{items[0]}\n{items[1]}")

    def mul(self, items):
        return self._indent(f"the product of:\n{items[0]}\n{items[1]}")

    def div(self, items):
        return self._indent(f"the quotient of:\n{items[0]}\n{items[1]}")

    def eq(self, items):
        return self._indent(f"{items[0]} is equal to {items[1]}")

    def ne(self, items):
        return self._indent(f"{items[0]} is not equal to {items[1]}")

    def lt(self, items):
        return self._indent(f"{items[0]} is less than {items[1]}")

    def gt(self, items):
        return self._indent(f"{items[0]} is greater than {items[1]}")

    def le(self, items):
        return self._indent(f"{items[0]} is less than or equal to {items[1]}")

    def ge(self, items):
        return self._indent(f"{items[0]} is greater than or equal to {items[1]}")

    def and_op(self, items):
        return self._indent(f"{items[0]}\nand\n{items[1]}")

    def or_op(self, items):
        return self._indent(f"{items[0]}\nor\n{items[1]}")

    def paren(self, items):
        self.indentation_level += 1
        result = self._indent(f"(\n{items[0]}\n)")
        self.indentation_level -= 1
        return result

    def date_is_past(self, items):
        return self._indent(f"{items[0]} is in the past")

    def date_is_future(self, items):
        return self._indent(f"{items[0]} is in the future")

    def date_is_today(self, items):
        return self._indent(f"{items[0]} is today")

    def date_within(self, items):
        return self._indent(f"{items[0]} is within {items[1]} {items[2]}")

    def date_older_than(self, items):
        return self._indent(f"{items[0]} is older than {items[1]} {items[2]}")

    def date_before(self, items):
        return self._indent(f"{items[0]} is before {items[1]}")

    def date_after(self, items):
        return self._indent(f"{items[0]} is after {items[1]}")

    def date_same_day(self, items):
        return self._indent(f"{items[0]} is on the same day as {items[1]}")


def to_indented_human_readable(expression: str) -> str:
    """
    Convert an expression into a human-readable description with indentation.

    Args:
        expression: The expression string to convert.

    Returns:
        A human-readable description of the expression with indentation.

    Raises:
        ValueError: If the expression has invalid syntax.
    """
    parser = build_parser()
    try:
        parse_tree = parser.parse(expression)
        transformer = IndentedHumanReadableTransformer()
        return transformer.transform(parse_tree)
    except Exception as e:
        raise ValueError(
            f"Failed to convert expression to indented human-readable form: {e}"
        )
