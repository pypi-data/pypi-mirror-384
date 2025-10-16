"""JsonPath-based resolver implementation."""

from jsonpath_ng import parse

from .interface import ResolverSpec


class JsonPathResolver(ResolverSpec):
    """A resolver using jsonpath_ng (pure Python)."""

    def _convert_path(self, path):
        """Convert dilemma path to jsonpath syntax."""
        # First apply the base class's possessive handling
        path = super()._convert_path(path)

        # Then apply jsonpath-specific conversion
        if not path.startswith("$"):
            return "$." + path
        return path

    def _execute_query(self, jsonpath_expr, context):
        """Execute a jsonpath expression against the context."""
        # Parse the expression
        expr = parse(jsonpath_expr)

        # Find matches
        matches = expr.find(context)

        # Return the first match's value, or None if no matches
        if matches:
            return matches[0].value
        return None

    def _execute_raw_query(self, raw_expr, context):
        """Execute a raw jsonpath expression.

        For jsonpath, we assume raw expressions already have proper syntax.
        """
        # Raw expressions might be in jq format - try to adapt them
        if raw_expr.startswith(".") and not raw_expr.startswith("$."):
            raw_expr = "$" + raw_expr

        return self._execute_query(raw_expr, context)
