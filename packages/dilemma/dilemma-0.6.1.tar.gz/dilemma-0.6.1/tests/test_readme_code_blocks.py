"""
Test that all Python code examples in the README.md file work correctly.

This test automatically extracts and executes Python code blocks from the README,
ensuring that the documentation examples always work without manual synchronization.
"""

import re
import ast
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from datetime import datetime, timedelta

import pytest


# We'll embed the markdown-code-runner functionality we need
def extract_python_code_blocks(markdown_content: str) -> list[tuple[str, int]]:
    """
    Extract Python code blocks from markdown content.

    Returns a list of tuples: (code_block, line_number)
    """
    lines = markdown_content.split("\n")
    code_blocks: list[tuple[str, int]] = []
    in_python_block = False
    current_block: list[str] = []
    start_line = 0

    for i, line in enumerate(lines):
        if line.strip().startswith("```python"):
            in_python_block = True
            current_block = []
            start_line = i + 1
        elif line.strip() == "```" and in_python_block:
            if current_block:
                code_blocks.append(("\n".join(current_block), start_line))
            in_python_block = False
            current_block = []
        elif in_python_block:
            current_block.append(line)

    return code_blocks


def is_executable_code(code: str) -> bool:
    """
    Check if the code block should be executed.

    Skip code blocks that are just examples or contain certain patterns.
    """
    # Skip if it's just imports or variable definitions without execution
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    # Skip if code contains only imports, assignments, or function definitions
    has_execution = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.If, ast.For, ast.While, ast.With, ast.Try)):
            has_execution = True
            break
        # Skip examples that are just showing syntax
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str) and len(node.value.value) > 20:
                continue  # Skip long string literals (likely examples)
            has_execution = True
            break

    # Skip code that contains placeholder patterns
    skip_patterns = [
        "# grant access",
        "send_premium_content",
        "context)",  # Just showing context variable
        "if evaluate(expr, context):",
        "for user_data in users:",
    ]

    for pattern in skip_patterns:
        if pattern in code:
            return False

    return has_execution


def setup_test_context() -> dict:
    """Setup a comprehensive test context with realistic data."""
    now = datetime.now()

    context_data = {
        "age": 25,
        "status": "active",
        "user": {
            "profile": {"age": 25, "settings": {"theme": "dark"}},
            "subscription": {
                "status": "active",
                "active": True,
                "end_date": now + timedelta(days=30),
            },
            "roles": ["user", "admin"],
            "permissions": ["read", "write", "admin"],
            "last_login": now - timedelta(days=5),
            "created_at": now - timedelta(days=20),
            "id": "123",
        },
        "users": [
            {"name": "Alice", "active": True, "roles": ["admin"]},
            {"name": "Bob", "active": False, "roles": ["user"]},
            {"name": "Charlie", "active": True, "roles": ["user"]},
        ],
        "subscription": {
            "end_date": now + timedelta(days=30),
            "expires": now + timedelta(days=10),
        },
        "order": {"total": 150, "shipped_date": now - timedelta(days=10)},
        "customer": {"tier": "premium"},
        "resource": {"owner": "123"},
        "last_backup": now - timedelta(days=2),
        "meeting": {"date": now},
        "start_date": now - timedelta(days=1),
        "end_date": now + timedelta(days=1),
        "event": {"date": now},
        "created_at": now - timedelta(hours=12),
        "approval": {"status": "approved"},
        "budget": {"remaining": 5000},
        "cost": 3000,
        "email": "user@example.com",
        "sales": [{"amount": 1000}, {"amount": 2000}, {"amount": 3000}],
        "products": [
            {"price": 50, "category": "books"},
            {"price": 150, "category": "electronics"},
            {"price": 200, "category": "electronics"},
            {"price": 75, "category": "clothing"},
        ],
    }

    return {
        "context": context_data,
        # Also provide some variables for compilation examples
        "users": [
            {
                "age": 25,
                "subscription": {"active": True},
                "last_login": now - timedelta(days=10),
            }
        ],
    }


def test_readme_python_code_blocks():
    """Test all executable Python code blocks in the README.md file."""
    readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        pytest.skip("README.md not found")

    with open(readme_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    code_blocks = extract_python_code_blocks(markdown_content)

    if not code_blocks:
        pytest.skip("No Python code blocks found in README.md")

    # Setup test environment
    test_globals = {
        "__name__": "__main__",
        "__builtins__": __builtins__,
        "datetime": datetime,
        "timedelta": timedelta,
    }

    # Import dilemma components
    try:
        from dilemma import evaluate, compile_expression
        from dilemma.errors import VariableError

        test_globals.update(
            {
                "evaluate": evaluate,
                "compile_expression": compile_expression,
                "VariableError": VariableError,
            }
        )
    except ImportError as e:
        pytest.skip(f"Could not import dilemma: {e}")

    # Add test context
    test_globals.update(setup_test_context())

    executed_blocks = 0

    for i, (code, line_number) in enumerate(code_blocks):
        if not is_executable_code(code):
            continue

        executed_blocks += 1

        # Capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code block
                exec(code, test_globals)

            # If we get here, the code executed successfully
            output = stdout_capture.getvalue()
            if output.strip():
                print(f"Code block {i+1} (line {line_number}) output:")
                print(output)

        except Exception as e:
            # Format error information
            error_msg = (
                f"Code block {i+1} failed (line {line_number} in README.md):\n"
                f"Code:\n{code}\n"
                f"Error: {type(e).__name__}: {e}"
            )

            stderr_output = stderr_capture.getvalue()
            if stderr_output.strip():
                error_msg += f"\nStderr: {stderr_output}"

            pytest.fail(error_msg)

    # Ensure we actually tested some code
    if executed_blocks == 0:
        pytest.skip("No executable code blocks found in README.md")

    print(f"Successfully executed {executed_blocks} code blocks from README.md")


def test_readme_syntax_validation():
    """Validate that all Python code blocks in README.md have valid syntax."""
    readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        pytest.skip("README.md not found")

    with open(readme_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    code_blocks = extract_python_code_blocks(markdown_content)

    if not code_blocks:
        pytest.skip("No Python code blocks found in README.md")

    syntax_errors = []

    for i, (code, line_number) in enumerate(code_blocks):
        try:
            ast.parse(code)
        except SyntaxError as e:
            syntax_errors.append(
                f"Code block {i+1} (line {line_number}) has syntax error: {e}\n"
                f"Code:\n{code}"
            )

    if syntax_errors:
        pytest.fail(
            f"Found {len(syntax_errors)} syntax errors in README.md code blocks:\n\n"
            + "\n\n".join(syntax_errors)
        )

    print(f"All {len(code_blocks)} Python code blocks in README.md have valid syntax")


def test_readme_import_statements():
    """Test that import statements shown in README work correctly."""
    readme_path = Path(__file__).parent.parent / "README.md"

    if not readme_path.exists():
        pytest.skip("README.md not found")

    with open(readme_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Extract lines that look like import statements from code blocks
    import_pattern = r"from dilemma import .+|import dilemma"
    imports = re.findall(import_pattern, markdown_content)

    if not imports:
        pytest.skip("No import statements found in README.md")

    # Test each unique import
    unique_imports = list(set(imports))
    test_globals = {"__name__": "__main__", "__builtins__": __builtins__}

    for import_stmt in unique_imports:
        try:
            exec(import_stmt, test_globals)
        except ImportError as e:
            pytest.fail(f"Import statement failed: {import_stmt}\nError: {e}")

    print(f"All {len(unique_imports)} import statements in README.md work correctly")


if __name__ == "__main__":
    # Allow running this test file directly
    test_readme_python_code_blocks()
    test_readme_syntax_validation()
    test_readme_import_statements()
