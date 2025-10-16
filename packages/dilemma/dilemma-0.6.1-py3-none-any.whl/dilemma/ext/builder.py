"""
IF

        the value of 'user.age' is greater than 18
        and
        the value of 'user.is_active' is equal to True

    OR

        the value of 'user.subscription.end_date' is in the past
        and
        the value of 'user.account.balance' is greater than 0

"""

from lark import Lark
from dilemma.lang import ExpressionTransformer

# Lark grammar for the human-readable indented format
human_readable_grammar = r"""
    ?start: expr

    ?expr: or_expr

    ?or_expr: and_expr
            | or_expr "OR" _INDENT and_expr _DEDENT -> or_op

    ?and_expr: comparison
             | and_expr "and" _INDENT comparison _DEDENT -> and_op

    ?comparison: sum
               | "IF" _INDENT sum "is equal to" sum _DEDENT -> eq
               | "IF" _INDENT sum "is not equal to" sum _DEDENT -> ne
               | "IF" _INDENT sum "is less than" sum _DEDENT -> lt
               | "IF" _INDENT sum "is greater than" sum _DEDENT -> gt
               | "IF" _INDENT sum "is less than or equal to" sum _DEDENT -> le
               | "IF" _INDENT sum "is greater than or equal to" sum _DEDENT -> ge
               | "IF" _INDENT sum "is in the past" _DEDENT -> date_is_past
               | "IF" _INDENT sum "is in the future" _DEDENT -> date_is_future
               | "IF" _INDENT sum "is today" _DEDENT -> date_is_today
               | "IF" _INDENT sum "is within" INTEGER time_unit _DEDENT -> date_within
               | "IF" _INDENT sum "is older than" INTEGER time_unit _DEDENT
                 -> date_older_than
               | "IF" _INDENT sum "is before" sum _DEDENT -> date_before
               | "IF" _INDENT sum "is after" sum _DEDENT -> date_after
               | "IF" _INDENT sum "is on the same day as" sum _DEDENT -> date_same_day

    ?sum: product
       | sum "the sum of" product -> add
       | sum "the difference between" product -> sub

    ?product: term
           | product "the product of" term -> mul
           | product "the quotient of" term -> div

    ?term: INTEGER -> int_number
         | FLOAT -> float_number
         | STRING -> string_literal
         | "negative" INTEGER -> negative_int
         | "negative" FLOAT -> negative_float
         | "True" -> true_value
         | "False" -> false_value
         | VARIABLE -> variable
         | "(" expr ")" -> paren

    VARIABLE: /[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*/

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

    _INDENT: /\n[ ]+/  // Match significant indentation
    _DEDENT: /\n/      // Match dedentation

    %import common.WS
    %ignore WS
"""

# Build the parser for the human-readable indented format
human_readable_parser = Lark(human_readable_grammar, start="start", parser="lalr")

# Example usage
if __name__ == "__main__":
    example_expression = """
    (
        the value of 'user.age' is greater than 18
        and
        the value of 'user.is_active' is equal to True
    )
    or
    (
        the value of 'user.subscription.end_date' is in the past
        and
        the value of 'user.account.balance' is greater than 0
    )
    """

    parse_tree = human_readable_parser.parse(example_expression)
    transformer = ExpressionTransformer()
    logical_expression = transformer.transform(parse_tree)
    print(logical_expression)
