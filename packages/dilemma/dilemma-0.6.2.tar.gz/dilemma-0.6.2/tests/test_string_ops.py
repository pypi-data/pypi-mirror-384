import pytest

from dilemma.lang import evaluate
from dilemma.errors import TypeMismatchError, ContainerError


def test_string_equality():
    test_cases = [
        ("'hello' == 'hello'", True),
        ("'hello' == 'world'", False),
        ("'test' == 'test'", True),
        ("'Test' == 'test'", False),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_string_inequality():
    test_cases = [
        ("'hello' != 'world'", True),
        ("'hello' != 'hello'", False),
        ("'test' != 'Test'", True),
        ("'Test' != 'Test'", False),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_string_contains():
    test_cases = [
        ("'hello' in 'hello world'", True),
        ("'world' in 'hello world'", True),
        ("'test' in 'testing'", True),
        ("'Test' in 'testing'", False),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected


def test_string_comparison_with_arithmetic():
    with pytest.raises(TypeMismatchError):
        evaluate("'hello' + 5")
    with pytest.raises(TypeMismatchError):
        evaluate("5 + 'hello'")


def test_invalid_contains_operation():
    with pytest.raises(ContainerError):
        evaluate("5 in 10")
    with pytest.raises(ContainerError):
        evaluate("5 in 'hello'")


def test_string_pattern_matching():
    """Test wildcard pattern matching with the 'like' operator."""
    test_cases = [
        # Basic wildcard patterns
        ("'file.txt' like '*.txt'", True),
        ("'image.jpg' like '*.png'", False),
        ("'hello.py' like '*.py'", True),
        # Question mark wildcard
        ("'file1.txt' like 'file?.txt'", True),
        ("'file10.txt' like 'file?.txt'", False),
        # Multiple wildcards
        ("'hello_world.py' like '*_*.py'", True),
        ("'helloworld.py' like '*_*.py'", False),
        # Beginning and end matches
        ("'test_string.py' like 'test_*'", True),
        ("'string_test.py' like 'test_*'", False),
        # Character classes
        ("'file1.txt' like 'file[0-9].txt'", True),
        ("'fileA.txt' like 'file[0-9].txt'", False),
        # Mixed patterns
        ("'user123' like 'user???'", True),
        ("'user1' like 'user???'", False),
        ("'document-2023.pdf' like 'document-*.pdf'", True),
    ]

    for expr, expected in test_cases:
        assert evaluate(expr) == expected, f"Failed on: {expr}"

    # Test case insensitivity (fnmatch is case-sensitive by default)
    assert evaluate("'Hello.txt' like '*hello.txt'")
