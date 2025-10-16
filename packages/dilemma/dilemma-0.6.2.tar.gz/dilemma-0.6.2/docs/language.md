# Dilemma Expression Language Grammar

This document describes the grammar and syntax for the Dilemma Expression Language,
a flexible language for evaluating conditions and expressions, with special support for
 date/time operations and human-friendly syntax.

## Overview

The Dilemma Expression Language is a lightweight expression language implemented using
the Lark parser. It supports various data types, operators, and functions that enable complex
condition evaluation, particularly useful for decision making and validation scenarios.

## Data Types

The language supports the following data types:

- **Numbers**: Integers and floating-point values (e.g., `42`, `3.14`, `-10`)
- **Strings**: Text enclosed in single or double quotes (e.g., `"hello"`, `'world'`)
- **Booleans**: `true` or `false`
- **Dates**: DateTime objects (typically accessed through variables or `$now`)
- **Collections**: Lists and dictionaries (accessed through variables)

## Operators

### Arithmetic Operators

- Addition: `+` (also performs string concatenation when both operands are strings)
- Subtraction: `-`
- Multiplication: `*`
- Division: `/`

### Comparison Operators

- Equal: `==` or `is`
- Not equal: `!=` or `is not`
- Less than: `<`
- Greater than: `>`
- Less than or equal: `<=`
- Greater than or equal: `>=`

### Logical Operators

- And: `and`
- Or: `or`

### Containment Operators

- `in`: Checks if left operand is contained in right operand
- `contains`: Checks if left operand contains the right operand

### Pattern Matching

- `like`: Case-insensitive wildcard pattern matching (e.g., `filename like "*.txt"`)
- `not like`: Negated pattern matching

## Date/Time Operations

The language has rich support for date and time comparisons:

### Date State Checks

- `date is $past`: Checks if date is in the past
- `date is $future`: Checks if date is in the future
- `date is $today`: Checks if date is today

### Relative Date Comparisons

- `date upcoming within X unit`: Checks if a date is within the specified time period in the future from now.
  - Example: `eventDate upcoming within 7 days` evaluates to `true` if `eventDate` is within the next 7 days from today.
- `date older than X unit`: Checks if a date is older than the specified time period from now.
  - Example: `lastUpdate older than 1 month` evaluates to `true` if `lastUpdate` is more than 1 month in the past.

### Date-to-Date Comparisons

- `date1 before date2`: Checks if first date is before second date
- `date1 after date2`: Checks if first date is after second date
- `date1 same_day_as date2`: Checks if two dates fall on the same calendar day

### Time Units

Supported time units (singular or plural forms):
- minute(s)
- hour(s)
- day(s)
- week(s)
- month(s)
- year(s)

## Special Values

- `$now`: Current date and time
- `$past`, `$future`, `$today`: Date state constants
- `$empty`: Used to check if a container (list, dict) is empty

## Variables and Data Access

### Variable Notation

- Simple variables: `variable_name`
- Nested properties can be accessed using:
  - Possessive notation: `user's name`
  - Dot notation: `user.name`
  - Array indexing: `items[0]`

### JQ Expressions

For more complex data access, JQ-style expressions are supported:
- Syntax: `` `expression` ``
- Allows querying complex JSON structures

## Array Operations and Quantifiers

The language provides powerful array operations for evaluating conditions across collections of data.

### Array Functions

These functions operate on arrays and return numerical or boolean results:

- `count_of(array)`: Returns the total number of items in the array
- `count_of(array, condition)`: Returns the count of items that satisfy the condition
- `any_of(array, condition)`: Returns `true` if any item satisfies the condition
- `all_of(array, condition)`: Returns `true` if all items satisfy the condition
- `none_of(array, condition)`: Returns `true` if no items satisfy the condition

### Array Sugar Syntax (Human-Friendly Quantifiers)

For more readable expressions, the language supports natural language quantifiers:

#### Exact Quantity
- `exactly N of array has condition`: True if exactly N items satisfy the condition

#### Minimum Quantity
- `at least N of array has condition`: True if N or more items satisfy the condition

#### Maximum Quantity
- `at most N of array has condition`: True if N or fewer items satisfy the condition

#### Convenience Quantifiers
- `any of array has condition`: Equivalent to `any_of(array, condition)`
- `all of array has condition`: Equivalent to `all_of(array, condition)`
- `none of array has condition`: Equivalent to `none_of(array, condition)`

### Array Condition Syntax

Array conditions are specified using JQ-style backtick expressions that are evaluated against each item in the array:

```
`property > value`
`nested.property == "string"`
`status in ["active", "pending"]`
```



## Operator Precedence

Operators follow standard precedence rules:
1. Parentheses `()`
2. Array functions and quantifiers (`count_of`, `any_of`, `at least`, etc.)
3. Multiplication, division `*`, `/`
4. Addition, subtraction `+`, `-`
5. Comparison operators `==`, `!=`, `<`, `>`, `<=`, `>=`, etc.
6. Logical AND `and`
7. Logical OR `or`

## Examples

Here are some examples of Dilemma Expression Language usage:

- Basic arithmetic:
  ```
  3 + 4 * 2
  ```
  Evaluates to `11`.

- String concatenation:
  ```
  "Hello, " + "world!"
  ```
  Evaluates to `"Hello, world!"`.

- Date comparison:
  ```
  orderDate is $past
  ```
  Evaluates to `true` if `orderDate` is before the current date.

- Collection containment:
  ```
  "apple" in fruits
  ```
  Evaluates to `true` if `fruits` is a list that contains `"apple"`.

- Array quantification:
  ```
  at least 3 of orders matches | total > 100 |
  ```
  Evaluates to `true` if 3 or more orders have a total greater than 100.

- Array functions:
  ```
  count_of(users, `active == true`) > 10
  ```
  Evaluates to `true` if more than 10 users are active.

- JQ expression:
  ```
  `.[0].name`
  ```
  Extracts the `name` field of the first object in a JSON array.

Extensive [examples](examples.md) are available [here](examples.md)

## Error Handling

The language provides error handling for various scenarios:
- Division by zero
- Type mismatch errors
- Invalid syntax
- Excessive string length (strings have a maximum length limit)
- Container errors (using array operations on non-array values)
- Invalid array conditions or malformed JQ expressions

## Implementation Details

The language is implemented in Python using the Lark parsing library. It compiles expressions
to intermediate representations that can be evaluated against variable contexts.

## Additional Features

#### Empty Check
- `is $empty`: Checks if a container (list, dict) is empty
  - Example: `data is $empty` (returns true if data is an empty container)

#### Float Comparison Behavior
- Float comparisons use a small epsilon value (1e-10) to avoid floating-point precision issues
  - Example: `0.1 + 0.2 == 0.3` will evaluate to `true` despite floating-point imprecision

#### Type Handling
- Type mismatches in operations are properly detected and reported
  - String concatenation only allowed when both operands are strings
  - Arithmetic operations reject string operands
  - Pattern matching requires string operands

## Implementation Notes

### Compilation and Evaluation
The language provides two main ways to evaluate expressions:
- `evaluate(expression, variables)`: Parse and evaluate in one step
- `compile_expression(expression)`: Pre-compile an expression for repeated evaluation with different variables

### Thread Safety
The parser implementation is thread-safe, using thread-local storage to maintain separate parser instances per thread.

### Error Handling
The language implements comprehensive error handling for:
- Invalid syntax in expressions
- Division by zero
- Type mismatches in operations
- Maximum string length restrictions (10,000 characters)
- Invalid variable references
