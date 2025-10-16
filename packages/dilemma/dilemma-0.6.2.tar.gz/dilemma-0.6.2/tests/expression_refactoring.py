#!/usr/bin/env python
"""
Expression Migration Template

A reusable script for migrating/refactoring patterns in Dilemma expression strings.
This template is designed to be adaptable for various expression language migrations.

Original use case: Migrating boolean literals from uppercase (True/False) to lowercase (true/false).

Usage:
    python expression_migration.py [OPTIONS] DIRECTORY

Options:
    --dry-run       Show changes without applying them
    --verbose, -v   Show detailed output of changes
"""
import click
from bowler import Query # type: ignore
from fissix.fixer_util import String # type: ignore
from pathlib import Path
import re
import os


@click.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help="Show changes without applying them")
@click.option('--verbose', '-v', is_flag=True, help="Show detailed output")
def migrate_expressions(directory, dry_run, verbose):
    """
    Migrate patterns in expression strings.

    This script safely transforms only string literals that match specified patterns,
    making it ideal for expression language migrations.
    """
    # =====================================================================
    # CONFIGURATION - Modify these settings for different migration needs
    # =====================================================================

    # 1. Set descriptive names for this migration
    migration_name = "Boolean Literal Migration"
    migration_description = "Converting uppercase True/False to lowercase true/false"

    # 2. Configure detection patterns
    # These patterns are used to identify strings that should be excluded from migration
    exclude_patterns = [
        '"""',              # Multi-line docstrings
        "'''",              # Alternative multi-line docstrings
        "Test ",            # Test descriptions
        "test ",            # Test descriptions (lowercase)
        "boolean literals", # Documentation about boolean literals
        "/True",            # References like "True/False" in documentation
        "/False"            # References like "True/False" in documentation
    ]

    # 3. Configure target patterns
    # These patterns indicate that a string contains expressions that should be migrated
    target_patterns = [
        " == True",        # Equality comparison with True
        " == False",       # Equality comparison with False
        " is True",        # Identity comparison with True
        " is False",       # Identity comparison with False
        "True and ",       # Logical AND with True
        "False and ",      # Logical AND with False
        "True or ",        # Logical OR with True
        "False or ",       # Logical OR with False
        ") == True",       # Parenthesized comparison with True
        ") == False"       # Parenthesized comparison with False
    ]

    # 4. Configure the transformation function
    # This function is applied to strings that match target patterns
    def transform_function(text):
        """Transform strings that match target patterns."""
        # Boolean literal migration: True/False -> true/false
        return text.replace("True", "true").replace("False", "false")

    # 5. (Optional) Additional conditions for identifying expression strings
    def is_standalone_boolean(text):
        """Check if text is a standalone boolean literal."""
        return text.strip() in ["True", "False"]

    # =====================================================================
    # MIGRATION ENGINE - Generally shouldn't need modification
    # =====================================================================

    # Track changes for reporting
    changes = {}

    # Function to process string literals
    def process_string(node, capture=None, filename=None):
        # Skip nodes without a value attribute (defensive)
        if not hasattr(node, 'value') or not isinstance(node.value, str):
            return None

        # Get the string value
        string_value = node.value

        # Check for exclude patterns - skip strings matching these
        if any(pattern in string_value for pattern in exclude_patterns):
            return None

        # Check if the string contains potential targets for migration
        if "True" in string_value or "False" in string_value:  # Adapt this for your use case
            # Look for patterns indicating it's an expression
            is_expression = (
                any(pattern in string_value for pattern in target_patterns) or
                is_standalone_boolean(string_value)
            )

            if is_expression:
                # Apply the transformation
                modified = transform_function(string_value)

                # Skip if no changes were made
                if modified == string_value:
                    return None

                # Record the change for reporting
                if filename not in changes:
                    changes[filename] = []
                changes[filename].append((string_value, modified))

                # Only return the modified string if we're not in dry run mode
                if not dry_run:
                    return String(modified)

        return None  # No modification

    # Create the query to target string literals
    query = Query(directory)

    # Target all string literals and let process_string do the filtering
    query.select("STRING").modify(process_string)

    # Execute the query without interactivity and respect the dry-run flag
    query.execute(interactive=False, write=not dry_run)

    # Show report of changes
    if changes:
        print(f"\n{migration_name} - {migration_description}")
        print("\nChanges that would be made:" if dry_run else "\nChanges made:")

        for file_path, file_changes in changes.items():
            rel_path = os.path.relpath(file_path, directory)
            print(f"\n{rel_path} ({len(file_changes)} changes):")

            for i, (old, new) in enumerate(file_changes, 1):
                if verbose:
                    print(f"  {i}. '{old}' -> '{new}'")
                else:
                    # Shorter output if not verbose
                    old_short = old[:40] + "..." if len(old) > 40 else old
                    new_short = new[:40] + "..." if len(new) > 40 else new
                    print(f"  {i}. '{old_short}' -> '{new_short}'")

        print(f"\nTotal: {sum(len(c) for c in changes.values())} changes in {len(changes)} files")
    else:
        print(f"\n{migration_name}: No changes would be made." if dry_run
              else f"{migration_name}: No changes were made.")

    # Return success
    return 0


if __name__ == '__main__':
    migrate_expressions()