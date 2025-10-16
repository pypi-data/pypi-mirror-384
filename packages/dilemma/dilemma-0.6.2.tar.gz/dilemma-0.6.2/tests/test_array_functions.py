import pytest
from dilemma.lang import evaluate
from dilemma.errors import DilemmaError, ContainerError, TypeMismatchError
from dilemma.errors.exc import UnexpectedTokenError


class TestArrayFunctions:
    """Test array function implementations and grammar handling"""

    def test_count_of_with_condition(self):
        """Test count_of with various conditions"""
        context = {
            "users": [
                {"name": "Alice", "age": 25, "active": True},
                {"name": "Bob", "age": 30, "active": False},
                {"name": "Charlie", "age": 35, "active": True},
                {"name": "David", "age": 20, "active": True},
            ]
        }

        # Numeric conditions
        assert evaluate("count_of(users, `age > 25`)", context) == 2
        assert evaluate("count_of(users, `age >= 25`)", context) == 3
        assert evaluate("count_of(users, `age < 30`)", context) == 2
        assert evaluate("count_of(users, `age == 30`)", context) == 1

        # Boolean conditions
        assert evaluate("count_of(users, `active`)", context) == 3
        assert evaluate("count_of(users, `active == false`)", context) == 1

        # String conditions
        assert evaluate('count_of(users, `name == "Alice"`)', context) == 1
        assert evaluate('count_of(users, `"A" in name`)', context) == 1

    def test_count_of_without_condition(self):
        """Test count_of without condition (just count all items)"""
        context = {
            "numbers": [1, 2, 3, 4, 5],
            "empty": [],
            "mixed": [1, "hello", True, None],
        }

        assert evaluate("count_of(numbers)", context) == 5
        assert evaluate("count_of(empty)", context) == 0
        assert evaluate("count_of(mixed)", context) == 4

    def test_any_of_with_condition(self):
        """Test any_of with various conditions"""
        context = {
            "items": [
                {"status": "active", "priority": 1},
                {"status": "inactive", "priority": 2},
                {"status": "pending", "priority": 3},
            ]
        }

        assert evaluate('any_of(items, `status == "active"`)', context)
        assert evaluate('any_of(items, `status == "deleted"`)', context) is False
        assert evaluate("any_of(items, `priority > 2`)", context)
        assert evaluate("any_of(items, `priority > 5`)", context) is False

    def test_any_of_without_condition(self):
        """Test any_of without condition (check if any item is truthy)"""
        context = {
            "all_true": [True, True, True],
            "mixed_true": [False, True, False],
            "all_false": [False, False, False],
            "mixed_values": [0, "", None, "hello"],
            "empty": [],
        }

        assert evaluate("any_of(all_true)", context)
        assert evaluate("any_of(mixed_true)", context)
        assert evaluate("any_of(all_false)", context) is False
        assert evaluate("any_of(mixed_values)", context)  # "hello" is truthy
        assert evaluate("any_of(empty)", context) is False

    def test_all_of_with_condition(self):
        """Test all_of with various conditions"""
        context = {
            "products": [
                {"price": 10, "in_stock": True},
                {"price": 25, "in_stock": True},
                {"price": 5, "in_stock": False},
            ]
        }

        assert evaluate("all_of(products, `price > 0`)", context)
        assert evaluate("all_of(products, `price > 10`)", context) is False
        assert evaluate("all_of(products, `in_stock`)", context) is False

    def test_all_of_without_condition(self):
        """Test all_of without condition (check if all items are truthy)"""
        context = {
            "all_true": [True, 1, "hello"],
            "with_false": [True, False, True],
            "with_zero": [1, 0, 2],
            "empty": [],
        }

        assert evaluate("all_of(all_true)", context)
        assert evaluate("all_of(with_false)", context) is False
        assert evaluate("all_of(with_zero)", context) is False
        assert evaluate("all_of(empty)", context)  # All of empty is vacuously true

    def test_none_of_with_condition(self):
        """Test none_of with various conditions"""
        context = {
            "employees": [
                {"department": "engineering", "salary": 80000},
                {"department": "marketing", "salary": 60000},
                {"department": "sales", "salary": 70000},
            ]
        }

        assert evaluate("none_of(employees, `salary > 100000`)", context)
        assert evaluate("none_of(employees, `salary > 50000`)", context) is False
        assert evaluate('none_of(employees, `department == "hr"`)', context)

    def test_none_of_without_condition(self):
        """Test none_of without condition (check if no items are truthy)"""
        context = {
            "all_false": [False, 0, "", None],
            "with_true": [False, True, False],
            "empty": [],
        }

        assert evaluate("none_of(all_false)", context)
        assert evaluate("none_of(with_true)", context) is False
        assert evaluate("none_of(empty)", context)  # None of empty is vacuously true

    def test_function_with_non_list_arguments(self):
        """Test that functions properly handle non-list arguments"""
        context = {"not_a_list": "hello", "number": 42, "dict_obj": {"key": "value"}}

        # Should raise ContainerError for non-list/tuple types
        with pytest.raises(ContainerError) as exc_info:
            evaluate("count_of(not_a_list)", context)
        assert "count_of (expects list/tuple)" in str(exc_info.value)

        with pytest.raises(ContainerError):
            evaluate("any_of(number)", context)

        with pytest.raises(ContainerError):
            evaluate("all_of(dict_obj)", context)

        with pytest.raises(ContainerError):
            evaluate("none_of(not_a_list)", context)

    def test_function_with_tuple_arguments(self):
        """Test that functions work with tuples as well as lists"""
        context = {
            "tuple_data": (1, 2, 3, 4, 5),
            "tuple_objects": ({"value": 1}, {"value": 4}, {"value": 7}),
        }

        assert evaluate("count_of(tuple_data)", context) == 5
        assert evaluate("any_of(tuple_objects, `value > 3`)", context)
        assert evaluate("all_of(tuple_objects, `value > 0`)", context)
        assert evaluate("none_of(tuple_objects, `value > 10`)", context)

    def test_complex_conditions(self):
        """Test functions with complex nested conditions"""
        context = {
            "orders": [
                {
                    "customer": {"type": "premium"},
                    "items": ["laptop", "mouse"],
                    "total": 1500,
                },
                {"customer": {"type": "regular"}, "items": ["book"], "total": 20},
                {
                    "customer": {"type": "premium"},
                    "items": ["phone", "case"],
                    "total": 800,
                },
            ]
        }

        # Nested property access
        assert evaluate('count_of(orders, `customer.type == "premium"`)', context) == 2

        # Array containment in condition
        assert evaluate('any_of(orders, `"laptop" in items`)', context)
        assert evaluate('none_of(orders, `"tablet" in items`)', context)

        # Complex boolean conditions
        assert (
            evaluate(
                'count_of(orders, `customer.type == "premium" and total > 1000`)', context
            )
            == 1
        )

    def test_grammar_edge_cases(self):
        """Test grammar parsing edge cases"""
        context = {"data": [1, 2, 3], "users": [{"name": "test", "score": 5}]}

        # Function calls in arithmetic expressions
        assert evaluate("count_of(data) + 5", context) == 8
        assert evaluate("count_of(data) * 2", context) == 6
        assert evaluate("10 - count_of(data)", context) == 7

        # Function calls in comparisons
        assert evaluate("count_of(data) == 3", context)
        assert evaluate("count_of(data) > 2", context)
        assert evaluate("count_of(data) <= 5", context)

        # Function calls in logical expressions
        assert evaluate("count_of(data) > 0 and any_of(users, `score > 0`)", context)
        assert evaluate("count_of(data) == 0 or all_of(users, `score > 0`)", context)

    def test_parentheses_and_precedence(self):
        """Test function calls with parentheses and operator precedence"""
        context = {"numbers": [1, 2, 3, 4, 5]}

        # Parentheses around function calls
        assert evaluate("(count_of(numbers)) == 5", context)
        assert evaluate("(count_of(numbers) + 1) * 2", context) == 12

        # Mixed with other parenthetical expressions
        assert evaluate("count_of(numbers) + (2 * 3)", context) == 11
        assert evaluate("(count_of(numbers) + 2) * (3 - 1)", context) == 14

    def test_function_name_collision_prevention(self):
        """Test that function names don't interfere with variable names"""
        context = {
            "count_of_items": 10,  # Variable that starts with function name
            "any_of_these": True,
            "data": [1, 2, 3],
        }

        # Variable access should still work
        assert evaluate("count_of_items == 10", context)
        assert evaluate("any_of_these", context)

        # Function calls should still work
        assert evaluate("count_of(data)", context) == 3

    def test_invalid_function_calls(self):
        """Test various invalid function call scenarios"""
        context = {"data": [1, 2, 3]}

        # Unknown function name should not parse as function call
        with pytest.raises(UnexpectedTokenError):
            evaluate("unknown_func(data)", context)

    def test_condition_evaluation_errors(self):
        """Test error handling in condition evaluation"""
        context = {
            "items": [
                {"value": 10},
                {"other": 20},  # Missing 'value' key
                {"value": 30},
            ]
        }

        # Condition that might fail for some items should handle gracefully
        # The _eval_predicate_on_item method should catch exceptions and return False
        result = evaluate("count_of(items, `value > 15`)", context)
        assert result == 1  # Only the item with value=30 should match

    def test_empty_conditions(self):
        """Test functions with empty or whitespace-only conditions"""
        context = {"data": [1, 2, 3]}

        # Empty condition evaluates to 0 (count of all items that match empty expression)
        # The empty backticks `` actually resolve to an empty string, which is falsy
        result = evaluate("count_of(data, ``)", context)
        assert result == 0  # Empty string is falsy, so no items match

    def test_nested_function_calls(self):
        """Test that nested function calls in conditions are handled appropriately"""
        context = {
            "groups": [{"items": [1, 2, 3]}, {"items": [4, 5]}, {"items": [6, 7, 8, 9]}]
        }

        # This actually works because the condition is evaluated per item
        # and each item has an 'items' field that we can count
        result = evaluate("count_of(groups, `count_of(items) > 2`)", context)
        assert result == 2  # Two groups have more than 2 items

    def test_function_calls_with_string_literals(self):
        """Test function calls mixed with string operations"""
        context = {"names": ["Alice", "Bob", "Charlie"]}

        # Functions in string comparisons
        result = evaluate('count_of(names) == 3 and "Alice" in names[0]', context)
        assert result

    def test_function_error_messages(self):
        """Test that function errors provide clear messages"""
        context = {"not_list": "string"}

        with pytest.raises(ContainerError) as exc_info:
            evaluate("count_of(not_list)", context)

        error_msg = str(exc_info.value)
        assert "count_of" in error_msg
        assert "list/tuple" in error_msg

    def test_function_with_variable_paths(self):
        """Test functions with complex variable path expressions"""
        context = {
            "project": {
                "teams": [
                    {"name": "Frontend", "members": [{"role": "lead"}, {"role": "dev"}]},
                    {"name": "Backend", "members": [{"role": "dev"}, {"role": "dev"}]},
                    {"name": "QA", "members": [{"role": "lead"}]},
                ]
            }
        }

        # Test nested property access in conditions
        assert evaluate('count_of(project.teams, `name == "Frontend"`)', context) == 1
        assert evaluate('any_of(project.teams, `"Backend" in name`)', context)

    def test_functions_with_float_values(self):
        """Test functions with floating point values"""
        context = {
            "prices": [
                {"item": "A", "price": 10.5},
                {"item": "B", "price": 25.99},
                {"item": "C", "price": 5.0},
            ]
        }

        assert evaluate("count_of(prices, `price > 10.0`)", context) == 2
        assert evaluate("any_of(prices, `price == 25.99`)", context)
        assert evaluate("all_of(prices, `price >= 5.0`)", context)

    def test_functions_with_boolean_logic(self):
        """Test functions with complex boolean conditions"""
        context = {
            "tasks": [
                {"priority": "high", "completed": True, "days": 5},
                {"priority": "low", "completed": False, "days": 2},
                {"priority": "high", "completed": False, "days": 10},
            ]
        }

        # Complex AND conditions
        assert (
            evaluate('count_of(tasks, `priority == "high" and completed`)', context) == 1
        )
        assert (
            evaluate(
                'count_of(tasks, `priority == "high" and completed == false`)', context
            )
            == 1
        )

        # Complex OR conditions
        assert evaluate("any_of(tasks, `completed or days > 8`)", context)
        assert evaluate('all_of(tasks, `priority == "high" or days > 0`)', context)

    def test_function_precedence_with_operators(self):
        """Test function call precedence with various operators"""
        context = {"items": [1, 2, 3, 4]}

        # Test precedence with arithmetic
        assert evaluate("count_of(items) + 1 * 2", context) == 6  # 4 + (1 * 2) = 6
        assert evaluate("(count_of(items) + 1) * 2", context) == 10  # (4 + 1) * 2 = 10

        # Test precedence with comparisons
        assert evaluate("count_of(items) > 2 and count_of(items) < 10", context)

    def test_functions_with_special_characters(self):
        """Test functions with strings containing special characters"""
        context = {
            "messages": [
                {"text": "Hello, world!"},
                {"text": "Test@example.com"},
                {"text": "Price: $19.99"},
            ]
        }

        assert evaluate('count_of(messages, `"@" in text`)', context) == 1
        assert evaluate('any_of(messages, `"$" in text`)', context)
        assert evaluate('count_of(messages, `"," in text`)', context) == 1

    def test_functions_with_null_and_undefined_values(self):
        """Test functions handling null and undefined values gracefully"""
        context = {
            "records": [
                {"name": "Alice", "age": 25},
                {"name": "Bob"},  # Missing age
                {"name": None, "age": 30},  # Null name
                {"age": 35},  # Missing name
            ]
        }

        # These should handle missing/null values gracefully
        # The condition evaluation catches exceptions and returns False for failed evaluations
        result = evaluate("count_of(records, `age > 20`)", context)
        assert result == 3  # Alice (25), null-name person (30), and unnamed person (35)

        result = evaluate('count_of(records, `name == "Alice"`)', context)
        assert result == 1
