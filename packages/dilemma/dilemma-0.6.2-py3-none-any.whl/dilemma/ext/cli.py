import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import yaml
import click
import cmd
import re
from xml.etree import ElementTree as ET


@click.group()
def cli():
    """Dilemma Expression Engine CLI."""
    pass


class DilemmaREPL(cmd.Cmd):
    intro = (
        "Entering REPL mode. Type 'help' or '?' for a list of commands."
        " Type 'exit' or 'quit' to leave."
    )
    prompt = ">>> "

    def __init__(self, context, verbose):
        super().__init__()
        self.context = context
        self.verbose = verbose
        from dilemma.lang import evaluate

        self.evaluate = evaluate

    def do_exit(self, arg):
        """Exit the REPL."""
        return True

    def do_quit(self, arg):
        """Exit the REPL."""
        return True

    def do_constants(self, arg):
        """List available constants."""
        print("Available constants:")
        print("  $now - Current datetime in UTC")
        print("  $past - Check if a date is in the past")
        print("  $future - Check if a date is in the future")
        print("  $today - Check if a date is today")
        print("  $empty - Check if a container is empty")

    def default(self, line):
        """Evaluate an expression."""
        try:
            result = self.evaluate(line, self.context)
            if self.verbose:
                print(f"Expression: {line}")
                print(f"Result: {result}")
                print(f"Type: {type(result).__name__}")
            else:
                print(result)
        except ZeroDivisionError:
            print("Error evaluating expression: Division by zero")
        except Exception as e:
            print(f"Error evaluating expression: {e}")


@cli.command(name="x")
@click.argument("expression", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option(
    "--context-file",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a YAML or JSON file to load as context for evaluation",
)
def evaluate_expression(expression: str, verbose: bool, context_file: str) -> None:
    """Evaluate a mathematical or logical expression.

    EXPRESSION: The expression to evaluate, e.g. "2 + 3 * 4" or "5 > 3 and 2 < 4".
    If omitted, a REPL loop will be started.
    """
    from dilemma.lang import evaluate

    # Load context from the provided file
    context = {}
    if context_file:
        try:
            with open(context_file, "r") as f:
                if context_file.endswith(".yaml") or context_file.endswith(".yml"):
                    context = yaml.safe_load(f)
                elif context_file.endswith(".json"):
                    context = json.load(f)
                else:
                    click.echo("Unsupported file format. Use YAML or JSON.", err=True)
                    raise click.Abort()
        except Exception as e:
            click.echo(f"Error loading context file: {e}", err=True)
            raise click.Abort()

    if expression:
        # Evaluate a single expression
        try:
            result = evaluate(expression, context)
            if verbose:
                click.echo(f"Expression: {expression}")
                click.echo(f"Result: {result}")
                click.echo(f"Type: {type(result).__name__}")
            else:
                click.echo(result)
        except ZeroDivisionError:
            click.echo("Error evaluating expression: Division by zero", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error evaluating expression: {e}", err=True)
            sys.exit(1)
    else:
        # Start the REPL
        DilemmaREPL(context, verbose).cmdloop()


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="docs/examples.md",
    help="Output markdown file path",
)
def gendocs(output):
    """Generate documentation from test examples."""
    try:
        tests_dir = Path(__file__).parents[3] / "tests" / "examples"
        if not tests_dir.exists():
            click.echo(f"Error: Examples directory not found at {tests_dir}", err=True)
            raise click.Abort()

        # Ensure the output directory exists
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        examples_by_category = {}
        time_values = create_time_values()

        yaml_files = list(tests_dir.glob("*.y*ml"))
        if not yaml_files:
            click.echo("No YAML files found in the examples directory", err=True)
            raise click.Abort()

        for yaml_file in sorted(yaml_files, key=lambda x: x.stem):
            with open(yaml_file, "r") as f:
                examples = yaml.safe_load(f)

            for example in examples:
                category = example.get("category", "Uncategorized")
                if category not in examples_by_category:
                    examples_by_category[category] = []
                examples_by_category[category].append(example)

        generate_markdown_docs(examples_by_category, time_values, output_path)

        click.echo(f"Documentation generated successfully: {output_path.absolute()}")

    except Exception as e:
        click.echo(f"Error generating documentation: {e}", err=True)
        raise click.Abort() from e


def create_time_values():
    """Create a dictionary of time values for documentation."""
    now = datetime.now(timezone.utc)
    return {
        "__NOW__": now,
        "__YESTERDAY__": now - timedelta(days=1),
        "__TOMORROW__": now + timedelta(days=1),
        "__HOUR_AGO__": now - timedelta(hours=1),
        "__IN_TWO_HOURS__": now + timedelta(hours=2),
        "__LAST_WEEK__": now - timedelta(days=7),
        "__NEXT_MONTH__": now + timedelta(days=30),
    }


def generate_markdown_docs(examples_by_category, time_values, output_path):
    """Generate formatted markdown documentation from examples."""
    from markdowngenerator import MarkdownGenerator

    with MarkdownGenerator(
        filename=output_path, enable_write=True, enable_TOC=False
    ) as doc:
        doc.addHeader(1, "Dilemma Expression Examples")
        doc.writeTextLine(
            "This document contains examples of using the Dilemma expression language."
        )
        doc.writeTextLine("")  # Instead of writeNewLine, use an empty string

        # Sort categories
        categories = list(examples_by_category.keys())

        for category in categories:
            # Format category name - convert snake_case to Title Case
            formatted_category = category.replace("_", " ").title()
            doc.addHeader(3, formatted_category)

            examples = examples_by_category[category]
            for i, example in enumerate(examples):
                # Add heading for each example
                title = example.get(
                    "name", example.get("description", f"Example {i + 1}")
                )
                ft = title.replace("_", " ").title()

                # Add description if available
                if "description" in example and example["name"] != example["description"]:
                    doc.writeTextLine(example["description"])
                else:
                    doc.writeTextLine(ft)
                doc.writeTextLine("")  # Empty line instead of writeNewLine

                expression = example["expression"]
                doc.writeTextLine("```")
                doc.writeTextLine(expression, html_escape=False)
                doc.writeTextLine("```")

                if example.get("context"):
                    # Process context to replace time placeholders with real dates
                    context = process_time_values_for_docs(
                        example["context"], time_values
                    )

                    # Format context as JSON
                    context_json = json.dumps(context, indent=2, default=str)
                    doc.addCodeBlock(context_json, "json")

                # Show result or error message
                if "expected" in example:
                    doc.writeTextLine(f"`Result: {example['expected']}` ")
                elif "error_message" in example:
                    doc.writeTextLine("**Expected Error:**")
                    doc.writeTextLine("```")
                    doc.writeTextLine(example["error_message"].strip())
                    doc.writeTextLine("```")

                doc.addHorizontalRule()


def process_time_values_for_docs(data, time_values):
    """
    Recursively process a data structure and replace time placeholders
    with readable dates.
    """
    if isinstance(data, dict):
        return {k: process_time_values_for_docs(v, time_values) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_time_values_for_docs(item, time_values) for item in data]
    elif isinstance(data, str) and data in time_values:
        # Format the datetime for documentation
        dt = time_values[data]
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        return data


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
def validate_exceptions(directory):
    """
    Validate that all exceptions raised in the codebase provide the required
    context variables for their respective templates.

    Args:
        directory: The root directory of the codebase to analyze.
    """
    # Parse the msg_templates.xml file to extract placeholders for each template_key
    templates_path = Path(directory) / "errors" / "msg_templates.xml"
    if not templates_path.exists():
        click.echo(f"Error: Template file not found at {templates_path}")
        return

    # Extract placeholders from the XML file
    template_placeholders = {}
    try:
        tree = ET.parse(templates_path)
        root = tree.getroot()
        for error in root.findall("error"):
            key = error.get("key")
            if key:
                placeholders = re.findall(r"\{(\w+)\}", error.text or "")
                template_placeholders[key] = set(placeholders)
    except Exception as e:
        click.echo(f"Error parsing template file: {e}")
        return

    # Traverse the codebase to find exceptions raised
    exceptions_report = []
    for py_file in Path(directory).rglob("*.py"):
        if "ext" in py_file.parts:
            continue  # Skip the 'ext' directory

        with open(py_file, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if "raise " in line:
                match = re.search(r"raise (\w+)\((.*)\)", line)
                if match:
                    exception_name = match.group(1)
                    args = match.group(2)

                    # Check if the exception is a DilemmaError or subclass
                    if exception_name.endswith("Error"):
                        # Extract the template_key and context variables
                        template_key_match = re.search(
                            r"template_key=['\"](\w+)['\"]", args
                        )

                        # Extract keyword arguments passed as context
                        context_match = re.findall(r"(\w+)\s*=\s*", args)

                        template_key = (
                            template_key_match.group(1) if template_key_match else None
                        )
                        context = set(context_match) if context_match else set()

                        if template_key and template_key in template_placeholders:
                            missing_placeholders = (
                                template_placeholders[template_key] - context
                            )
                            if missing_placeholders:
                                exceptions_report.append(
                                    {
                                        "file": py_file,
                                        "line": i + 1,
                                        "exception": exception_name,
                                        "template_key": template_key,
                                        "missing_placeholders": missing_placeholders,
                                    }
                                )

    # Report the results
    if exceptions_report:
        click.echo("Validation Report:\n")
        for report in exceptions_report:
            click.echo(f"File: {report['file']} (Line {report['line']})")
            click.echo(f"  Exception: {report['exception']}")
            click.echo(f"  Template Key: {report['template_key']}")
            click.echo(
                f"  Missing Placeholders: {', '.join(report['missing_placeholders'])}\n"
            )
    else:
        click.echo("All exceptions are properly configured.")


if __name__ == "__main__":
    cli()
