"""
Tests for the messages module error template system.
"""

import pytest
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from dilemma.errors import messages


# Fixtures
@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global template state before each test."""
    original_default = messages.DEFAULT_TEMPLATES
    original_custom = messages._custom_templates
    
    # Reset to None before test
    messages.DEFAULT_TEMPLATES = None
    messages._custom_templates = None
    
    yield
    
    # Restore original state after test
    messages.DEFAULT_TEMPLATES = original_default
    messages._custom_templates = original_custom


@pytest.fixture
def test_templates():
    """Provide a set of test templates for error formatting tests."""
    return {
        "test_template": "Error: {details}",
        "multi_placeholder": "Type {type} at line {line}",
        "no_placeholder": "Simple error message"
    }


# Tests for load_templates_from_xml functionality
def test_load_templates_from_xml_success():
    """Test successful loading of templates from XML."""
    # This will use the actual XML file
    templates = messages.load_templates_from_xml()
    
    # Should load templates successfully
    assert isinstance(templates, dict)
    assert len(templates) > 0
    
    # Check that some expected templates are present
    assert "syntax_error" in templates
    assert "undefined_variable" in templates


def test_load_templates_from_xml_file_not_found():
    """Test handling when XML file is not found."""
    with patch("dilemma.errors.messages.files") as mock_files:
        # Mock files to raise an exception
        mock_files.side_effect = FileNotFoundError("XML file not found")
        
        templates = messages.load_templates_from_xml()
        
        # Should return empty dict on error
        assert templates == {}


def test_load_templates_from_xml_invalid_xml():
    """Test handling of invalid XML content."""
    invalid_xml = b"<invalid>xml content"
    
    with patch("dilemma.errors.messages.files") as mock_files:
        mock_path = MagicMock()
        mock_path.open.return_value.__enter__.return_value = mock_open(read_data=invalid_xml).return_value
        mock_files.return_value.joinpath.return_value = mock_path
        
        templates = messages.load_templates_from_xml()
        
        # Should return empty dict on XML parsing error
        assert templates == {}


def test_load_templates_from_xml_empty_file():
    """Test handling of empty XML file."""
    empty_xml = b"<errors></errors>"
    
    with patch("dilemma.errors.messages.files") as mock_files:
        mock_path = MagicMock()
        mock_path.open.return_value.__enter__.return_value = mock_open(read_data=empty_xml).return_value
        mock_files.return_value.joinpath.return_value = mock_path
        
        templates = messages.load_templates_from_xml()
        
        # Should return empty dict but not fail
        assert templates == {}


def test_load_templates_from_xml_missing_key_attribute():
    """Test handling of error elements without key attributes."""
    xml_content = b"""<errors>
        <error>Template without key</error>
        <error key="valid_key">Template with key</error>
    </errors>"""
    
    with patch("dilemma.errors.messages.files") as mock_files:
        mock_path = MagicMock()
        mock_path.open.return_value.__enter__.return_value = mock_open(read_data=xml_content).return_value
        mock_files.return_value.joinpath.return_value = mock_path
        
        templates = messages.load_templates_from_xml()
        
        # Should only load the template with a key
        assert len(templates) == 1
        assert "valid_key" in templates
        assert templates["valid_key"] == "Template with key"


def test_load_templates_from_xml_empty_text():
    """Test handling of error elements with empty text."""
    xml_content = b"""<errors>
        <error key="empty_text"></error>
        <error key="valid_text">Valid message</error>
    </errors>"""
    
    with patch("dilemma.errors.messages.files") as mock_files:
        mock_path = MagicMock()
        mock_path.open.return_value.__enter__.return_value = mock_open(read_data=xml_content).return_value
        mock_files.return_value.joinpath.return_value = mock_path
        
        templates = messages.load_templates_from_xml()
        
        # Should load both templates, empty one as empty string
        assert len(templates) == 2
        assert templates["empty_text"] == ""
        assert templates["valid_text"] == "Valid message"


# Tests for get_templates functionality
def test_get_templates_loads_default_when_none_cached():
    """Test that templates are loaded from XML when not cached."""
    # Ensure we start with no cached templates
    assert messages.DEFAULT_TEMPLATES is None
    
    templates = messages.get_templates()
    
    # Should have loaded templates and cached them
    assert messages.DEFAULT_TEMPLATES is not None
    assert templates is messages.DEFAULT_TEMPLATES
    assert len(templates) > 0


def test_get_templates_returns_cached_default():
    """Test that cached default templates are returned."""
    # Pre-populate the cache
    test_templates = {"test_key": "test_message"}
    messages.DEFAULT_TEMPLATES = test_templates
    
    templates = messages.get_templates()
    
    # Should return the cached templates
    assert templates is test_templates


def test_get_templates_returns_custom_when_set():
    """Test that custom templates are returned when configured."""
    custom_templates = {"custom_key": "custom_message"}
    messages._custom_templates = custom_templates
    
    templates = messages.get_templates()
    
    # Should return custom templates, not default
    assert templates is custom_templates


def test_get_templates_custom_overrides_default():
    """Test that custom templates override default templates."""
    default_templates = {"default_key": "default_message"}
    custom_templates = {"custom_key": "custom_message"}
    
    messages.DEFAULT_TEMPLATES = default_templates
    messages._custom_templates = custom_templates
    
    templates = messages.get_templates()
    
    # Should return custom templates
    assert templates is custom_templates
    assert templates != default_templates


# Tests for format_error functionality
def test_format_error_success(test_templates):
    """Test successful error formatting."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("test_template", details="Something went wrong")
    
    assert result == "\nError: Something went wrong"


def test_format_error_multiple_placeholders(test_templates):
    """Test formatting with multiple placeholders."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("multi_placeholder", type="string", line=42)
    
    assert result == "\nType string at line 42"


def test_format_error_no_placeholders(test_templates):
    """Test formatting template with no placeholders."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("no_placeholder")
    
    assert result == "\nSimple error message"


def test_format_error_template_not_found(test_templates):
    """Test handling when template is not found."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("nonexistent_template", details="Some error")
    
    # Should return fallback message
    assert result == "Error: Some error"


def test_format_error_template_not_found_no_details(test_templates):
    """Test handling when template is not found and no details provided."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("nonexistent_template")
    
    # Should return fallback message with default
    assert result == "Error: Unknown error"


def test_format_error_missing_placeholder(test_templates):
    """Test handling when required placeholder is missing."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("test_template")  # Missing 'details' argument
    
    # Should return error message about missing placeholder
    assert "Error formatting message" in result
    assert "missing: 'details'" in result
    assert "Error: {details}" in result


def test_format_error_missing_multiple_placeholders(test_templates):
    """Test handling when multiple placeholders are missing."""
    messages._custom_templates = test_templates
    
    result = messages.format_error("multi_placeholder", type="string")  # Missing 'line'
    
    # Should return error message about missing placeholder
    assert "Error formatting message" in result
    assert "missing: 'line'" in result


def test_format_error_no_templates_loaded():
    """Test handling when no templates are loaded."""
    # Set templates to empty dict
    messages._custom_templates = {}
    
    result = messages.format_error("any_template", details="Some error")
    
    # Should return fallback message
    assert result == "Error: Some error"


def test_format_error_templates_is_none():
    """Test handling when templates is None."""
    # Mock get_templates to return None
    with patch.object(messages, 'get_templates', return_value=None):
        result = messages.format_error("any_template", details="Some error")
        
        # Should return fallback message
        assert result == "Error: Some error"


# Tests for configure_templates functionality
def test_configure_templates():
    """Test configuring custom templates."""
    custom_templates = {
        "custom_error": "Custom error: {message}",
        "another_error": "Another error occurred"
    }
    
    messages.configure_templates(custom_templates)
    
    # Should set the custom templates
    assert messages._custom_templates is custom_templates


def test_configure_templates_empty_dict():
    """Test configuring with empty template dictionary."""
    messages.configure_templates({})
    
    # Should set custom templates to empty dict
    assert messages._custom_templates == {}


def test_configure_templates_overrides_previous():
    """Test that new configuration overrides previous custom templates."""
    # Set initial custom templates
    initial_templates = {"initial": "Initial template"}
    messages.configure_templates(initial_templates)
    
    # Configure new templates
    new_templates = {"new": "New template"}
    messages.configure_templates(new_templates)
    
    # Should replace previous templates
    assert messages._custom_templates is new_templates
    assert messages._custom_templates != initial_templates


# Tests for get_default_templates functionality
def test_get_default_templates_loads_when_none():
    """Test that default templates are loaded when not cached."""
    # Ensure we start with no cached templates
    assert messages.DEFAULT_TEMPLATES is None
    
    result = messages.get_default_templates()
    
    # Should have loaded and cached templates
    assert messages.DEFAULT_TEMPLATES is not None
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_default_templates_returns_copy():
    """Test that a copy of default templates is returned."""
    # Pre-populate the cache
    test_templates = {"test_key": "test_message"}
    messages.DEFAULT_TEMPLATES = test_templates
    
    result = messages.get_default_templates()
    
    # Should return a copy, not the original
    assert result == test_templates
    assert result is not test_templates


def test_get_default_templates_modification_safe():
    """Test that modifying returned templates doesn't affect cached ones."""
    # Pre-populate the cache
    test_templates = {"test_key": "test_message"}
    messages.DEFAULT_TEMPLATES = test_templates
    
    result = messages.get_default_templates()
    result["new_key"] = "new_message"
    
    # Original should be unchanged
    assert "new_key" not in messages.DEFAULT_TEMPLATES
    assert messages.DEFAULT_TEMPLATES == test_templates


def test_get_default_templates_empty_when_none_loaded():
    """Test handling when no templates can be loaded."""
    # Mock load_templates_from_xml to return empty dict
    with patch.object(messages, 'load_templates_from_xml', return_value={}):
        result = messages.get_default_templates()
        
        # Should return empty dict
        assert result == {}


def test_get_default_templates_with_custom_set():
    """Test that default templates are still returned even when custom are set."""
    # Set custom templates
    messages._custom_templates = {"custom": "custom_template"}
    
    # Pre-populate default templates
    default_templates = {"default": "default_template"}
    messages.DEFAULT_TEMPLATES = default_templates
    
    result = messages.get_default_templates()
    
    # Should return default templates, not custom
    assert result == default_templates
    assert "custom" not in result


# Integration tests for the complete workflow
def test_full_workflow_with_xml_loading():
    """Test the complete workflow from XML loading to error formatting."""
    # This uses the actual XML file and tests the full integration
    result = messages.format_error("syntax_error", details="Invalid token")
    
    assert "Invalid expression syntax: Invalid token" in result


def test_custom_templates_override_default():
    """Test that custom templates properly override defaults."""
    # Configure custom templates
    custom_templates = {
        "syntax_error": "Custom syntax error: {details}",
        "new_error": "New error type: {message}"
    }
    messages.configure_templates(custom_templates)
    
    # Test that custom template is used
    result = messages.format_error("syntax_error", details="Bad syntax")
    assert result == "\nCustom syntax error: Bad syntax"
    
    # Test that new custom template works
    result = messages.format_error("new_error", message="Something wrong")
    assert result == "\nNew error type: Something wrong"
    
    # Test that fallback still works for non-existent templates
    result = messages.format_error("unknown_error", details="Unknown issue")
    assert result == "Error: Unknown issue"


def test_default_templates_not_affected_by_custom():
    """Test that default templates are preserved when custom are set."""
    # Set custom templates
    messages.configure_templates({"custom": "Custom template"})
    
    # Get default templates
    defaults = messages.get_default_templates()
    
    # Should contain original templates from XML, not custom ones
    assert "syntax_error" in defaults
    assert "custom" not in defaults
