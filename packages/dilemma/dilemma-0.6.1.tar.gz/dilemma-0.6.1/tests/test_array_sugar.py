import pytest
from dilemma.lang import evaluate
from dilemma.errors import DilemmaError, ContainerError, TypeMismatchError


class TestArraySugar:
    """Test natural language sugar for array functions"""

    def test_at_least_of_sugar(self):
        """Test 'at least N of X has predicate' sugar"""
        context = {
            "users": [
                {"name": "Alice", "age": 25, "active": True},
                {"name": "Bob", "age": 30, "active": False},
                {"name": "Charlie", "age": 35, "active": True},
                {"name": "David", "age": 20, "active": True},
            ]
        }

        # Test various "at least" conditions
        assert (
            evaluate("at least 2 of users matches |age > 25|", context) == True
        )  # 2 users (Bob, Charlie)
        assert (
            evaluate("at least 3 of users matches |age > 25|", context) == False
        )  # Only 2 users
        assert (
            evaluate("at least 3 of users matches |active|", context) == True
        )  # 3 active users
        assert evaluate('at least 1 of users matches |name == "Alice"|', context) == True
        assert evaluate('at least 2 of users matches |name == "Alice"|', context) is False

    def test_at_most_of_sugar(self):
        """Test 'at most N of X has predicate' sugar"""
        context = {
            "products": [
                {"name": "Widget A", "price": 10.50, "in_stock": True},
                {"name": "Widget B", "price": 25.00, "in_stock": True},
                {"name": "Widget C", "price": 5.99, "in_stock": False},
                {"name": "Widget D", "price": 30.00, "in_stock": True},
            ]
        }

        # Test various "at most" conditions
        assert (
            evaluate("at most 2 of products matches |price > 20|", context) == True
        )  # 2 products (B, D)
        assert (
            evaluate("at most 1 of products matches |price > 20|", context) == False
        )  # 2 products
        assert (
            evaluate("at most 3 of products matches |in_stock|", context) == True
        )  # 3 in stock
        assert (
            evaluate("at most 4 of products matches |in_stock|", context) == True
        )  # 3 in stock
        assert (
            evaluate("at most 0 of products matches |price > 100|", context) == True
        )  # None over 100

    def test_exactly_of_sugar(self):
        """Test 'exactly N of X has predicate' sugar"""
        context = {
            "employees": [
                {"name": "Alice", "department": "Engineering", "salary": 80000},
                {"name": "Bob", "department": "Marketing", "salary": 60000},
                {"name": "Charlie", "department": "Engineering", "salary": 85000},
                {"name": "David", "department": "Sales", "salary": 70000},
            ]
        }

        # Test various "exactly" conditions
        assert (
            evaluate(
                'exactly 2 of employees matches |department == "Engineering"|', context
            )
            == True
        )
        assert (
            evaluate(
                'exactly 1 of employees matches |department == "Engineering"|', context
            )
            is False
        )
        assert (
            evaluate(
                'exactly 1 of employees matches |department == "Marketing"|', context
            )
            == True
        )
        assert evaluate("exactly 4 of employees matches |salary > 0|", context) == True
        assert (
            evaluate("exactly 0 of employees matches |salary > 100000|", context) == True
        )

    def test_any_of_sugar(self):
        """Test 'any of X has predicate' sugar"""
        context = {
            "tasks": [
                {"status": "active", "priority": 1, "completed": False},
                {"status": "inactive", "priority": 2, "completed": True},
                {"status": "pending", "priority": 3, "completed": False},
            ]
        }

        # Test various "any of" conditions
        assert evaluate('any of tasks matches |status == "active"|', context) == True
        assert evaluate('any of tasks matches |status == "deleted"|', context) is False
        assert evaluate("any of tasks matches |completed|", context) == True
        assert evaluate("any of tasks matches |priority > 2|", context) == True
        assert evaluate("any of tasks matches |priority > 5|", context) is False

    def test_all_of_sugar(self):
        """Test 'all of X has predicate' sugar"""
        context = {
            "orders": [
                {"id": 1, "total": 100, "paid": True},
                {"id": 2, "total": 50, "paid": True},
                {"id": 3, "total": 75, "paid": True},
            ]
        }

        # Test various "all of" conditions
        assert evaluate("all of orders matches |paid|", context) == True
        assert evaluate("all of orders matches |total > 0|", context) == True
        assert evaluate("all of orders matches |total > 60|", context) is False

        # Test with one false case
        context["orders"][1]["paid"] = False
        assert evaluate("all of orders matches |paid|", context) is False

    def test_none_of_sugar(self):
        """Test 'none of X has predicate' sugar"""
        context = {
            "items": [
                {"category": "electronics", "defective": False},
                {"category": "clothing", "defective": False},
                {"category": "books", "defective": False},
            ]
        }

        # Test various "none of" conditions
        assert evaluate("none of items matches |defective|", context) == True
        assert (
            evaluate('none of items matches |category == "furniture"|', context) == True
        )
        assert (
            evaluate('none of items matches |category == "electronics"|', context)
            is False
        )

        # Test with one true case
        context["items"][0]["defective"] = True
        assert evaluate("none of items matches |defective|", context) is False

    def test_sugar_in_complex_expressions(self):
        """Test sugar syntax in complex boolean expressions"""
        context = {
            "team_members": [
                {"name": "Alice", "role": "lead", "experience": 5},
                {"name": "Bob", "role": "developer", "experience": 3},
                {"name": "Charlie", "role": "developer", "experience": 2},
                {"name": "David", "role": "designer", "experience": 4},
            ]
        }

        # Combine sugar with logical operators
        assert (
            evaluate(
                'at least 2 of team_members matches |experience > 2| and any of team_members matches |role == "lead"|',
                context,
            )
            == True
        )

        assert (
            evaluate(
                'exactly 1 of team_members matches |role == "lead"| or all of team_members matches |experience > 10|',
                context,
            )
            == True
        )

        assert (
            evaluate(
                'none of team_members matches |experience > 10| and at most 3 of team_members matches |role == "developer"|',
                context,
            )
            == True
        )

    def test_sugar_with_arithmetic(self):
        """Test sugar syntax in arithmetic expressions"""
        context = {
            "scores": [
                {"player": "Alice", "points": 95},
                {"player": "Bob", "points": 72},
                {"player": "Charlie", "points": 88},
            ]
        }

        # Use sugar results in arithmetic
        assert (
            evaluate("exactly 1 of scores matches |points > 90| + 2", context) == 3
        )  # 1 + 2 = 3
        # There are 3 scores > 70 (Alice: 95, Bob: 72, Charlie: 88)
        result = evaluate("exactly 3 of scores matches |points > 70|", context)
        assert result == True  # 3 scores (Alice: 95, Bob: 72, Charlie: 88) > 70

    def test_sugar_with_comparisons(self):
        """Test sugar syntax in comparison expressions"""
        context = {
            "items": [
                {"value": 1},
                {"value": 2},
                {"value": 3},
                {"value": 4},
                {"value": 5},
            ],
            "users": [{"active": True}, {"active": False}, {"active": True}],
        }

        # Compare sugar results
        assert evaluate("exactly 5 of items matches |value > 0| == true", context) == True
        assert evaluate("at least 2 of users matches |active| != false", context) == True
        assert (
            evaluate('none of users matches |active == "maybe"| == true', context) == True
        )

    def test_sugar_edge_cases(self):
        """Test edge cases and error conditions"""
        context = {
            "empty_list": [],
            "not_a_list": "string",
            "mixed_types": [1, "hello", True, None],
        }

        # Empty list cases
        assert evaluate("exactly 0 of empty_list matches |value > 0|", context) == True
        assert evaluate("at least 1 of empty_list matches |value > 0|", context) is False
        assert evaluate("at most 0 of empty_list matches |value > 0|", context) == True
        assert evaluate("any of empty_list matches |value > 0|", context) is False
        assert (
            evaluate("all of empty_list matches |value > 0|", context) == True
        )  # Vacuously true
        assert evaluate("none of empty_list matches |value > 0|", context) == True

        # Non-list should raise error
        with pytest.raises(ContainerError):
            evaluate("any of not_a_list matches |length > 0|", context)

    def test_sugar_with_nested_properties(self):
        """Test sugar with complex nested object predicates"""
        context = {
            "projects": [
                {"name": "Project A", "team": {"size": 5, "lead": "Alice"}},
                {"name": "Project B", "team": {"size": 3, "lead": "Bob"}},
                {"name": "Project C", "team": {"size": 8, "lead": "Charlie"}},
            ]
        }

        # Test nested property access in predicates
        assert (
            evaluate("exactly 1 of projects matches | team.size > 7 |", context) == True
        )
        assert (
            evaluate('any of projects matches | team.lead == "Alice" |', context) == True
        )
        assert (
            evaluate("at least 2 of projects matches | team.size >= 3 |", context) == True
        )

    def test_sugar_with_string_operations(self):
        """Test sugar with string matching predicates"""
        context = {
            "files": [
                {"name": "document.pdf", "size": 1024},
                {"name": "image.jpg", "size": 2048},
                {"name": "archive.zip", "size": 4096},
                {"name": "text.txt", "size": 512},
            ]
        }

        # Test string containment and patterns
        assert evaluate('exactly 1 of files matches | ".pdf" in name |', context) == True
        assert evaluate('any of files matches | name like "*.jpg" |', context) == True
        assert evaluate('none of files matches | name like "*.exe" |', context) == True
        assert (
            evaluate("at most 2 of files matches | size > 1000 |", context) == False
        )  # 3 files > 1000

    def test_precedence_and_parentheses(self):
        """Test operator precedence with sugar expressions"""
        context = {
            "data": [{"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}, {"value": 5}]
        }

        # Test precedence with parentheses
        assert (
            evaluate("(exactly 5 of data matches | value > 0 |) and true", context)
            == True
        )
        assert (
            evaluate("exactly 5 of data matches | value > 0 | and true", context) == True
        )

        # Test in more complex expressions
        result = evaluate("(at least 3 of data matches | value > 2 |) or false", context)
        assert result == True  # 3 values (3,4,5) > 2

    def test_variable_name_conflicts(self):
        """Test that sugar keywords don't conflict with variable names in practice"""
        context = {
            "my_at": "test_value",  # Use different variable names to avoid conflicts
            "least_count": 123,
            "exactly_match": True,
            "data": [1, 2, 3],
        }

        # Variable access should still work with non-conflicting names
        assert evaluate('my_at == "test_value"', context) == True
        assert evaluate("least_count == 123", context) == True
        assert evaluate("exactly_match == true", context) == True

        # Sugar should still work
        assert (
            evaluate("exactly 3 of data matches | True |", context) == False
        )  # Numbers can't access True property

    def test_float_numbers_in_counts(self):
        """Test that integer numbers are properly handled in count expressions"""
        context = {"items": [{"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}]}

        # Should handle integer tokens properly - Lark should parse these as INTEGER tokens
        assert evaluate("exactly 4 of items matches | value > 0 |", context) == True
        assert evaluate("at least 2 of items matches | value > 1 |", context) == True
        assert evaluate("at most 3 of items matches | value < 4 |", context) == True
