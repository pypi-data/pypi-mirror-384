"""
Error message templates for the Dilemma expression language.

This module provides a configurable template system for error messages.
Users can supply their own templates with placeholders for error context.
"""

from typing import Dict
import xml.etree.ElementTree as ET
from importlib.resources import files

from ..logconf import get_logger

log = get_logger(__name__)


# Global templates storage
DEFAULT_TEMPLATES: Dict[str, str] | None = None
_custom_templates: Dict[str, str] | None = None


XML_FILENAME = "msg_templates.xml"


def load_templates_from_xml() -> Dict[str, str]:
    """
    Load error message templates from the errors.xml file.

    Uses importlib to locate the file and ElementTree to parse it.

    Returns:
        Dictionary of template keys to message templates
    """
    log.debug("Loading error templates from XML file")
    try:
        # Use the current module name to find the XML file in the same directory
        xml_path = files(__name__).joinpath(XML_FILENAME)

        # Convert Traversable to string path for ElementTree.parse
        with xml_path.open("rb") as xml_file:
            tree = ET.parse(xml_file)
        root = tree.getroot()

        # Extract templates from error elements
        templates = {}
        for error in root.findall("error"):
            key = error.get("key")
            if key:
                # Get the text content and preserve formatting, but strip leading/trailing
                # whitespace
                message = error.text.strip() if error.text else ""
                templates[key] = message
                log.debug(f"Loaded template '{key}' from XML")

        # Log results
        if templates:
            log.info(f"Loaded {len(templates)} templates from {XML_FILENAME}")
        else:
            log.warning("No templates found in %s", XML_FILENAME)

        return templates

    except Exception as e:
        log.error(f"Failed to load templates from XML: {e}")
        return {}


def get_templates() -> Dict[str, str]:
    """
    Get the current templates, loading from XML if necessary.

    Returns:
        Current set of error message templates
    """
    global DEFAULT_TEMPLATES, _custom_templates

    # Use custom templates if set
    if _custom_templates is not None:
        return _custom_templates

    # Load templates from XML if not already loaded
    if DEFAULT_TEMPLATES is None:
        DEFAULT_TEMPLATES = load_templates_from_xml()

    return DEFAULT_TEMPLATES


def format_error(template_name: str, **kwargs) -> str:
    """
    Format an error message using a template and context variables.

    Args:
        template_name: Name of the template to use
        **kwargs: Context variables to inject into the template

    Returns:
        Formatted error message string
    """
    templates = get_templates()

    log.debug(f"Looking for template '{template_name}'")
    if not templates or template_name not in templates:
        # Fallback to a generic message if template not found
        log.warning(f"Template '{template_name}' not found in templates")
        return f"Error: {kwargs.get('details', 'Unknown error')}"

    template = templates[template_name]
    log.debug(f"Found template: '{template}'")

    # Process template to preserve line breaks but strip leading whitespace
    template_lines = template.split("\n")
    processed_lines = []
    for line in template_lines:
        processed_lines.append(line.strip())
    # Join lines back together, removing empty lines at start/end
    processed_template = "\n" + "\n".join(processed_lines).strip()

    try:
        # Handle special formatting for lists in suggestions
        if "suggestions" in kwargs and isinstance(kwargs["suggestions"], list):
            # Create a copy of kwargs with formatted suggestions
            formatted_kwargs = kwargs.copy()
            suggestions = kwargs["suggestions"]
            if suggestions:
                # Format suggestions with line breaks for better readability
                formatted_lines = []
                for suggestion in suggestions:
                    if suggestion.startswith("Expected: "):
                        # Split the expected tokens and format each on its own line
                        expected_part = suggestion[10:]  # Remove "Expected: " prefix
                        # Split more carefully to handle descriptions with commas
                        tokens = []
                        current_token = ""
                        paren_count = 0

                        for char in expected_part:
                            if char == "(":
                                paren_count += 1
                            elif char == ")":
                                paren_count -= 1
                            elif char == "," and paren_count == 0:
                                tokens.append(current_token.strip())
                                current_token = ""
                                continue
                            current_token += char

                        if current_token.strip():
                            tokens.append(current_token.strip())

                        for token in tokens:
                            formatted_lines.append(f"  - {token}")
                    else:
                        # Other suggestions (like keyword warnings) stay as-is
                        formatted_lines.append(f"  - {suggestion}")
                formatted_kwargs["suggestions"] = "\n" + "\n".join(formatted_lines)
            else:
                formatted_kwargs["suggestions"] = "None available"
            return processed_template.format(**formatted_kwargs)
        else:
            return processed_template.format(**kwargs)
    except KeyError as e:
        # If formatting fails due to missing placeholder, return a helpful message
        log.error(f"Missing placeholder '{e}' in template '{template}'")
        return f"Error formatting message (missing: {e}): {template}"


def configure_templates(templates: Dict[str, str]) -> None:
    """
    Configure custom templates.

    Args:
        templates: Dictionary of template names to template strings
    """
    global _custom_templates
    _custom_templates = templates
    log.info(f"Configured {len(templates)} custom templates")


def get_default_templates() -> Dict[str, str]:
    """
    Return a copy of the default templates.

    Useful for users who want to customize only some templates.
    """
    # Ensure templates are loaded if they haven't been already
    global DEFAULT_TEMPLATES
    if DEFAULT_TEMPLATES is None:
        DEFAULT_TEMPLATES = load_templates_from_xml()

    return DEFAULT_TEMPLATES.copy() if DEFAULT_TEMPLATES else {}
