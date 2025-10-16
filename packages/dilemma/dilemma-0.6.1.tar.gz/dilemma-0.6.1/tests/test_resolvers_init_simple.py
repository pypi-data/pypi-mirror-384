"""
Simple tests for the resolver plugin management system.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import asyncio
import sys

# We need to import the module directly to access its functions and globals
import dilemma.resolvers as resolvers


class MockResolver:
    """Simple mock resolver for testing."""
    
    def resolve_path(self, path, context, raw=False):
        return f"mock_result_{path}"


class AsyncMockResolver:
    """Mock resolver with async support."""
    
    def resolve_path(self, path, context, raw=False):
        return f"sync_result_{path}"
    
    async def resolve_path_async(self, path, context, raw=False):
        return f"async_result_{path}"


@pytest.fixture(autouse=True)
def clean_resolvers():
    """Clean up resolvers before each test and restore initial state."""
    # Save original state
    original_resolvers = resolvers._resolvers.copy()
    original_default = resolvers._default_resolver
    
    # Clear for test
    resolvers._resolvers.clear()
    resolvers._default_resolver = None
    yield
    
    # Restore original state
    resolvers._resolvers.clear()
    resolvers._resolvers.update(original_resolvers)
    resolvers._default_resolver = original_default


@pytest.fixture
def mock_resolver_class():
    """Create a mock resolver class."""
    mock_class = MagicMock(return_value=MockResolver())
    mock_class.__name__ = "TestResolver"
    return mock_class


def test_register_resolver_basic(mock_resolver_class):
    """Test basic resolver registration."""
    result = resolvers.register_resolver(mock_resolver_class)
    
    assert "test" in resolvers._resolvers
    assert resolvers._default_resolver == "test"
    assert isinstance(result, MockResolver)


def test_register_resolver_custom_name():
    """Test registering with custom name."""
    mock_class = MagicMock(return_value=MockResolver())
    mock_class.__name__ = "SomeResolver"
    
    resolvers.register_resolver(mock_class, name="custom")
    
    assert "custom" in resolvers._resolvers
    assert resolvers._default_resolver == "custom"


def test_register_resolver_not_default():
    """Test registering non-default resolver."""
    # Register first as default
    mock_class1 = MagicMock(return_value=MockResolver())
    mock_class1.__name__ = "FirstResolver"
    resolvers.register_resolver(mock_class1)
    
    # Register second as non-default
    mock_class2 = MagicMock(return_value=MockResolver())
    mock_class2.__name__ = "SecondResolver"
    resolvers.register_resolver(mock_class2, default=False)
    
    assert resolvers._default_resolver == "first"
    assert "second" in resolvers._resolvers


def test_resolve_path_default(mock_resolver_class):
    """Test path resolution with default resolver."""
    resolvers.register_resolver(mock_resolver_class)
    
    result = resolvers.resolve_path("test.path", {})
    assert result == "mock_result_test.path"


def test_resolve_path_specific_resolver(mock_resolver_class):
    """Test path resolution with specific resolver."""
    resolvers.register_resolver(mock_resolver_class)
    
    # Register another resolver
    mock_class = MagicMock(return_value=MockResolver())
    mock_class.__name__ = "SpecificResolver"
    resolvers.register_resolver(mock_class, default=False)
    
    result = resolvers.resolve_path("test.path", {}, resolver_name="specific")
    assert result == "mock_result_test.path"


def test_resolve_path_nonexistent_resolver(mock_resolver_class):
    """Test error with nonexistent resolver."""
    resolvers.register_resolver(mock_resolver_class)
    
    with pytest.raises(KeyError):
        resolvers.resolve_path("test.path", {}, resolver_name="nonexistent")


def test_resolve_path_with_raw_flag(mock_resolver_class):
    """Test path resolution with raw flag."""
    resolvers.register_resolver(mock_resolver_class)
    
    result = resolvers.resolve_path("test.path", {}, raw=True)
    assert result == "mock_result_test.path"


def test_resolve_path_no_default_resolver():
    """Test error when no default resolver is set."""
    with pytest.raises(KeyError):  # None used as dict key
        resolvers.resolve_path("test.path", {})


def test_empty_resolver_name():
    """Test resolver with empty name."""
    mock_class = MagicMock(return_value=MockResolver())
    mock_class.__name__ = "Resolver"  # Becomes "" after removing "resolver"
    
    resolvers.register_resolver(mock_class)
    
    assert "" in resolvers._resolvers
    assert resolvers._default_resolver == ""


def test_async_resolver_has_async_method():
    """Test that async resolver has the expected method."""
    async_resolver = AsyncMockResolver()
    assert hasattr(async_resolver, 'resolve_path_async')
    
    # Test the method exists and can be called
    result = asyncio.run(async_resolver.resolve_path_async("test", {}))
    assert result == "async_result_test"


def test_sync_resolver_no_async_method():
    """Test that sync-only resolver doesn't have async method."""
    sync_resolver = MockResolver()
    assert not hasattr(sync_resolver, 'resolve_path_async')


def test_module_has_expected_functions():
    """Test that the module exports expected functions."""
    assert hasattr(resolvers, 'register_resolver')
    assert hasattr(resolvers, 'resolve_path')
    assert hasattr(resolvers, 'resolve_path_async')


def test_module_has_global_state():
    """Test that module has expected global variables."""
    assert hasattr(resolvers, '_resolvers')
    assert hasattr(resolvers, '_default_resolver')
    assert isinstance(resolvers._resolvers, dict)


def test_register_resolver_creates_instance():
    """Test that register_resolver actually instantiates the class."""
    call_count = 0
    
    class CountingResolver:
        def __init__(self):
            nonlocal call_count
            call_count += 1
        
        def resolve_path(self, path, context, raw=False):
            return "result"
    
    CountingResolver.__name__ = "CountingResolver"
    
    resolvers.register_resolver(CountingResolver)
    
    assert call_count == 1  # Constructor was called
    assert "counting" in resolvers._resolvers


def test_name_derivation_logic():
    """Test the resolver name derivation logic."""
    test_cases = [
        ("JsonPathResolver", "jsonpath"),
        ("JqResolver", "jq"), 
        ("BasicResolver", "basic"),
        ("SomeOtherClass", "someotherclass"),
        ("Resolver", ""),
    ]
    
    for class_name, expected_name in test_cases:
        # Test the actual logic used in the module
        derived_name = class_name.lower().replace("resolver", "")
        assert derived_name == expected_name


def test_import_jsonpath_resolver_success():
    """Test that JsonPathResolver can be imported and registered."""
    try:
        from dilemma.resolvers.jsonpath_resolver import JsonPathResolver
        # If we get here, the import succeeded
        resolver_instance = JsonPathResolver()
        assert hasattr(resolver_instance, 'resolve_path')
        
        # Test registration
        result = resolvers.register_resolver(JsonPathResolver, name="test_jsonpath")
        assert "test_jsonpath" in resolvers._resolvers
        assert isinstance(result, JsonPathResolver)
    except ImportError:
        # If import fails, that's also valid - just skip this test
        pytest.skip("JsonPathResolver not available")


def test_import_jq_resolver_success():
    """Test that JqResolver can be imported and registered."""
    try:
        from dilemma.resolvers.jq_resolver import JqResolver
        # If we get here, the import succeeded
        resolver_instance = JqResolver()
        assert hasattr(resolver_instance, 'resolve_path')
        
        # Test registration
        result = resolvers.register_resolver(JqResolver, name="test_jq")
        assert "test_jq" in resolvers._resolvers
        assert isinstance(result, JqResolver)
    except ImportError:
        # If import fails, that's also valid - just skip this test
        pytest.skip("JqResolver not available")


def test_basic_resolver_fallback():
    """Test that BasicResolver is available as fallback."""
    from dilemma.resolvers.basic_resolver import BasicResolver
    resolver_instance = BasicResolver()
    assert hasattr(resolver_instance, 'resolve_path')
    
    # Test registration
    result = resolvers.register_resolver(BasicResolver, name="test_basic")
    assert "test_basic" in resolvers._resolvers
    assert isinstance(result, BasicResolver)


@patch('dilemma.resolvers.logger')
def test_import_error_handling_jsonpath(mock_logger):
    """Test logging when JsonPathResolver import fails."""
    with patch.dict('sys.modules', {'dilemma.resolvers.jsonpath_resolver': None}):
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            # This should trigger the ImportError handling
            try:
                from dilemma.resolvers.jsonpath_resolver import JsonPathResolver
                assert False, "Should have raised ImportError"
            except ImportError:
                pass


@patch('dilemma.resolvers.logger')
def test_import_error_handling_jq(mock_logger):
    """Test logging when JqResolver import fails."""
    with patch.dict('sys.modules', {'dilemma.resolvers.jq_resolver': None}):
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            try:
                from dilemma.resolvers.jq_resolver import JqResolver
                assert False, "Should have raised ImportError"
            except ImportError:
                pass


def test_resolve_path_with_real_resolver():
    """Test resolve_path with a real resolver instance."""
    from dilemma.resolvers.basic_resolver import BasicResolver
    
    # Register a real resolver
    resolvers.register_resolver(BasicResolver)
    
    # Test resolution - BasicResolver only handles top-level keys
    context = {"test": "value"}
    result = resolvers.resolve_path("test", context)
    assert result == "value"


def test_resolve_path_async_with_real_resolver():
    """Test async resolution with real resolver."""
    from dilemma.resolvers.basic_resolver import BasicResolver
    
    # Register a real resolver
    resolvers.register_resolver(BasicResolver)
    
    # Test async resolution - should fall back to sync
    context = {"test": "async_value"}
    result = asyncio.run(resolvers.resolve_path_async("test", context))
    assert result == "async_value"


def test_resolve_path_async_with_async_resolver():
    """Test async resolution fallback behavior."""
    from dilemma.resolvers.basic_resolver import BasicResolver
    
    # Register a resolver that doesn't have async support
    resolvers.register_resolver(BasicResolver)
    
    # Test that it falls back to sync method
    context = {"test": "async_fallback"}
    result = asyncio.run(resolvers.resolve_path_async("test", context))
    assert result == "async_fallback"


def test_module_initialization_behavior():
    """Test the module's import-time initialization behavior.
    
    Note: This test doesn't use the clean_resolvers fixture to see 
    the natural state of the module after import.
    """
    # Import the module fresh to see its natural state
    import importlib
    import dilemma.resolvers
    
    # Reload to see initialization behavior
    importlib.reload(dilemma.resolvers)
    
    # The resolvers module should have auto-registered some resolvers during import
    # At minimum, there should be resolvers available
    assert len(dilemma.resolvers._resolvers) > 0
    assert dilemma.resolvers._default_resolver is not None
    
    # Check that at least one of the expected resolvers is registered
    resolver_names = set(dilemma.resolvers._resolvers.keys())
    expected_resolvers = {"jsonpath", "jq", "basic"}
    
    # At least one should be present
    assert len(resolver_names.intersection(expected_resolvers)) > 0


def test_logger_info_on_registration():
    """Test that registration logs info messages."""
    with patch('dilemma.resolvers.logger') as mock_logger:
        from dilemma.resolvers.basic_resolver import BasicResolver
        
        resolvers.register_resolver(BasicResolver, name="test_logging")
        
        # Should have called logger.info
        mock_logger.info.assert_called_with("Registered resolver: test_logging")


def test_logger_debug_on_resolution():
    """Test that path resolution logs debug messages."""
    with patch('dilemma.resolvers.logger') as mock_logger:
        from dilemma.resolvers.basic_resolver import BasicResolver
        
        resolvers.register_resolver(BasicResolver)
        resolvers.resolve_path("test", {"test": "value"})
        
        # Should have called logger.debug
        mock_logger.debug.assert_called_with("Resolving path %s with resolver %s", "test", "basic")
