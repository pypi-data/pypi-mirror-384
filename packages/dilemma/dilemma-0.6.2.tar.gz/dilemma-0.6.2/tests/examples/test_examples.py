import yaml
import os
import pytest
from datetime import datetime, timedelta, timezone
from dilemma.lang import evaluate


# Helper function to load all examples and generate IDs
def load_examples():
    """Load all examples from YAML files in the test directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_files = [f for f in os.listdir(current_dir) if f.endswith((".yaml", ".yml"))]

    if not yaml_files:
        pytest.fail("No YAML files found in test directory")

    all_examples = []
    example_ids = []  # Store IDs separately

    # Create times for our tests
    now = datetime.now(timezone.utc)
    time_values = {
        "__NOW__": now,
        "__YESTERDAY__": now - timedelta(days=1),
        "__TOMORROW__": now + timedelta(days=1),
        "__HOUR_AGO__": now + timedelta(hours=1),
        "__HOUR_FROM_NOW__": now + timedelta(hours=1),
        "__IN_TWO_HOURS__": now + timedelta(hours=2),
        "__LAST_WEEK__": now - timedelta(days=7),
        "__NEXT_MONTH__": now + timedelta(days=30),
    }

    for yaml_file in yaml_files:
        file_path = os.path.join(current_dir, yaml_file)
        base_name = os.path.splitext(os.path.basename(yaml_file))[0]

        with open(file_path, "r") as f:
            examples = yaml.safe_load(f)

        for i, example in enumerate(examples):
            # Get or generate a descriptive name
            # Prefer 'name' field, fall back to description + index
            if "name" in example:
                name = example["name"]
            elif "description" in example:
                # Convert description to a valid identifier
                desc = example["description"].lower()
                name = desc.replace(" ", "_")[:30]  # Keep reasonable length
            else:
                name = f"example_{i + 1}"

            # Add the example data
            all_examples.append(
                (
                    yaml_file,
                    name,
                    example.get("expression"),
                    example.get("expected"),
                    example.get("error_message"),
                    example.get("context", {}),
                    time_values,
                )
            )

            # Generate ID with category prefix if available
            category = example.get("category", "")
            if category:
                example_ids.append(f"{base_name}::{category}::{name}")
            else:
                example_ids.append(f"{base_name}::{name}")

    return all_examples, example_ids


# Replace the simple context processing with this recursive function:
def process_time_values(data, time_values):
    """Recursively process a data structure and replace time placeholders."""
    if isinstance(data, dict):
        return {k: process_time_values(v, time_values) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_time_values(item, time_values) for item in data]
    elif isinstance(data, str) and data in time_values:
        return time_values[data]
    else:
        return data


# Create a class for each YAML file to group tests by file
class TestExamples:
    # Load examples and IDs
    examples, example_ids = load_examples()

    @pytest.mark.parametrize(
        "yaml_file,name,expression,expected,error_message,yaml_context,time_values",
        examples,
        ids=example_ids,
    )
    def test_example(
        self, yaml_file, name, expression, expected, error_message, yaml_context, time_values
    ):
        """Test individual examples from YAML files."""
        assert expression is not None, (
            f"Missing 'expression' in example '{name}' of {yaml_file}"
        )
        assert expected is not None or error_message is not None, (
            f"Missing 'expected' or 'error_message' in example '{name}' of {yaml_file}"
        )

        # Process the context to replace special time values
        context = process_time_values(yaml_context, time_values)

        # Test for expected error message if one is defined
        if error_message is not None:
            with pytest.raises(Exception) as excinfo:
                evaluate(expression, context)

            # Get the string representation of the exception
            actual_error = str(excinfo.value)

            # Split both messages by lines and trim each line to avoid whitespace issues
            expected_lines = [line.strip() for line in error_message.strip().split('\n')]
            actual_lines = [line.strip() for line in actual_error.strip().split('\n')]

            # Compare line by line
            assert len(expected_lines) == len(actual_lines), (
                f"Error message line count mismatch in example '{name}' of {yaml_file}:\n"
                f"Expected {len(expected_lines)} lines, got {len(actual_lines)}"
            )

            for i, (expected_line, actual_line) in enumerate(zip(expected_lines, actual_lines)):
                assert expected_line == actual_line, (
                    f"Error message mismatch at line {i+1} in example '{name}' of {yaml_file}:\n"
                    f"Expected: '{expected_line}'\n"
                    f"Got: '{actual_line}'"
                )
        else:
            # Evaluate the expression and check result
            result = evaluate(expression, context)

            # Check if result matches expected
            assert result == expected, (
                f"Example '{name}' in {yaml_file} failed:\n"
                f"Expression: {expression}\n"
                f"Context: {context}\n"
                f"Expected: {expected} ({type(expected)})\n"
                f"Got: {result} ({type(result)})"
            )
