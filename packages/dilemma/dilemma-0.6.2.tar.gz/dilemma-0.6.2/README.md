# Dilemma Expression Language

[![CI](https://github.com/patrickcd/dilemma/workflows/CI/badge.svg)](https://github.com/patrickcd/dilemma/actions)
[![codecov](https://codecov.io/gh/patrickcd/dilemma/branch/main/graph/badge.svg)](https://codecov.io/gh/patrickcd/dilemma)
[![PyPI version](https://img.shields.io/pypi/v/dilemma.svg)](https://pypi.org/project/dilemma/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

An expression evaluation engine for Python applications that makes complex logical expressions readable and maintainable.

- Business rules
- Data validation
- Authorisation checks
- Data filtering
- Formulas and calculations

## Why Dilemma?

Given context data like this:
```yaml
---
project:
  status: review
signoffs:
- user:
    name: Alice Chen
    role: Audit
  timestamp: '2025-10-07T10:30:00Z'
- user:
    name: Bob Smith
    role: Audit
  timestamp: '2025-10-07T14:20:00Z'
- user:
    name: Carol Wong
    role: Audit
  timestamp: '2025-10-08T09:15:00Z'
- user:
    name: Dave Johnson
    role: Legal
  timestamp: '2025-10-07T16:45:00Z'
documents:
- name: contract.pdf
  verified: true
- name: financials.xlsx
  verified: true
- name: legal_review.docx
  verified: true
```

Instead of writing an expression like this:
```javascript
// Complex JavaScript approach
audit_signoffs.filter((signoff) => {
    return signoff.user.role == 'Audit' && new Date(signoff.timestamp) < new Date()
}).length >= 3
&& 'status' in project
&& project.status == 'review'
&& documents.filter((doc) => doc.verified).length === documents.length
```

Your users can express the business rules like this:

```php

// dilemma expression language

    at least 3 of signoffs matches | user.role == 'Audit' and timestamp is $past |
    and project has 'status' and project.status == 'review'
    and all of documents matches | verified == true |
```

For array operations, instead of complex function calls:
```php
count_of(orders, `status == 'pending'`) >= 3 and any_of(orders, `total > 1000`)
```

User can enjoy a more natural language:
```php
at least 3 of orders matches |status == 'pending'| and any of orders matches |total > 1000|
```

## Features

- **Secure evaluation** - No arbitrary code execution, only safe expressions
- **Rich data access** - Navigate nested dictionaries and lists with ease
- **Date/time operations** - Natural language date comparisons
- **Multiple resolvers** - JsonPath, JQ, and basic dictionary lookup
- **Performance optimized** - Compile expressions once, evaluate many times
- **Type safe** - Built-in type checking and validation

## Quick Start

```bash
pip install dilemma
```

```python
from dilemma import evaluate

# Basic arithmetic and logic
result = evaluate("2 * (3 + 4)")  # Returns 14
result = evaluate("age >= 18 and status == 'active'", {"age": 25, "status": "active"})

# Natural language array operations
result = evaluate("at least 2 of users matches | status == 'active' |", context)
result = evaluate("none of orders matches | amount > 1000 |", context)

# Date operations
result = evaluate("user.last_login upcoming within 7 days", context)
result = evaluate("subscription.end_date is $future", context)

# Complex data access
result = evaluate("user.permissions contains 'admin'", context)
result = evaluate("`[.users[] | select(.active == true) | .name] | length` > 0", context)
```

## Language Features

All [Language Features](https://github.com/patrickcd/dilemma/blob/main/docs/language.md).
Extensive [Examples](https://github.com/patrickcd/dilemma/blob/main/docs/examples.md).


### Data Access Patterns

```python
# Dot notation for nested objects
"user.profile.settings.theme == 'dark'"

# Natural possessive syntax
"user's subscription's status == 'premium'"

# Array/list access
"users[0].name == 'Alice'"

# Check membership
"'admin' in user.roles"
"user.permissions contains 'read'"

# Check property existence

" user has 'address' and 'Mesters Vig' in user.address"
```

### Natural Language Array Operations

Dilemma provides intuitive sugar syntax for common array operations:

```python
# Quantity-based checks
"at least 3 of orders matches | status == 'shipped' |"
"at most 2 of users matches | role == 'admin' |"
"exactly 1 of servers matches | status == 'maintenance' |"

# Existence checks
"any of products matches | price > 100 |"
"all of users matches | email_verified == true |"
"none of alerts matches | severity == 'critical' |"

# Combined with other operations
"at least 5 of reviews matches | rating >= 4 | and user.subscription is $active"
"any of files matches |name like '*.pdf'| and all of files matches |size < 10000000|"
```

### Date and Time Operations

```python
# Relative time checks
"user.created_at upcoming within 30 days"
"order.shipped_date older than 1 week"

# State comparisons
"subscription.expires is $future"
"last_backup is $past"
"meeting.date is $today"

# Date comparisons
"start_date before end_date"
"event.date same_day_as $now"
```


### Advanced JQ Integration

For complex data manipulation, use JQ expressions in backticks:

```python
# Filter and transform arrays - working with provided context
evaluate('`[.users[] | select(.active == true) | .name]`', context)

# Mathematical operations on arrays
evaluate('`[.sales[].amount] | add` > 10000', context)

# Complex conditionals
evaluate('`[.products[] | select(.price > 100 and .category == "electronics")] | length` > 1', context)
```

## Performance Optimization

### Same expression, multiple contexts

For repeated evaluations, compile expressions once:

```python
from dilemma import compile_expression

# Compile once - including array sugar syntax
eligibility_check = compile_expression(
    "user.age >= 18 and user.subscription.active and at least 1 of user.orders matches | status == 'completed' |"
)

# Evaluate many times with different contexts
for user_data in users:
    if eligibility_check.evaluate(user_data):
        # send_premium_content(user_data)
        pass
```

### Same data, multiple expressions

If evaluating multiple expressions against the same data, use ProcessedContent instead of passing in
a dictionary of values. This saves the json dump/load cycle that Dilemma uses to sanitize data.

```python
from dilemma import evaluate, ProcessedContext

# Sample data
data = {
    "users": [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
        {"name": "Charlie", "age": 35, "active": True}
    ],
    "threshold": 28
}

# Process the data once for safety and optimization
context = ProcessedContext(data)

# Evaluate multiple expressions efficiently
expressions = [
    "users[0].name == 'Alice'",     # True
    "users[1].age < threshold",     # True
    "users[2].active",              # True
    "any_of(users, `active`)"       # True
]

for expr in expressions:
    result = evaluate(expr, context)
    print(f"{expr} = {result}")
```


## Error Handling

Dilemma provides clear, actionable error messages:

```python
try:
    result = evaluate("user.invalidfield == 'test'", context)
except VariableError as e:
    print(f"Expression error: {e}")
    # Suggests available fields and common fixes
```

## Use Cases

- **Form validation rules** - `"email like '*@*' and age >= 13"`
- **Business logic** - `"order.total > 100 and customer.tier == 'premium'"`
- **Access control** - `"user.roles contains 'admin' or resource.owner == user.id"`
- **Data filtering** - `"created_at upcoming within 24 hours and status == 'pending'"`
- **Workflow conditions** - `"approval.status == 'approved' and budget.remaining >= cost"`
- **Quality assurance** - `"all of tests match |status == 'passed'| and none of builds match |errors > 0|"`
- **Inventory management** - `"at least 10 of products match |stock > 0| and any of suppliers match |delivery_time < 3|"`
- **Security monitoring** - `"none of login_attempts match |failed_count > 5| and all of sessions match |encrypted == true|"`

## Safety & Security

- ✅ No arbitrary Python code execution
- ✅ No access to imports or builtins
- ✅ Sandboxed evaluation environment
- ✅ Input validation and sanitization
- ✅ Memory and complexity limits


## License

MIT License - see [LICENSE](https://github.com/patrickcd/dilemma/blob/main/LICENSE) file for details.
