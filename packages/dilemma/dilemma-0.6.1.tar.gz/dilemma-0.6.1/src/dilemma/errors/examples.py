ERROR_EXAMPLES = {
    "missing_operator": [
        "x y",  # Missing operator between variables
        "5 10",  # Missing operator between numbers
        "(a + b) (c + d)",  # Missing operator between parenthesized expressions
    ],
    "unclosed_parenthesis": [
        "(a + b",  # Missing closing parenthesis
        "a + (b * c",  # Missing closing parenthesis in nested expression
    ],
    "invalid_variable": [
        "and + 5",  # Using reserved keyword as variable
        "or > 10",  # Using reserved keyword as variable
    ],
    "trailing_operator": [
        "x + ",  # Operator at end of expression
        "10 * ",  # Operator at end of expression
    ],
    # Add more common error patterns...
}
