"""JQ-based resolver implementation."""

import re

try:
    import jq
except ImportError:
    # This will be caught when trying to import JqResolver
    raise ImportError(
        "The jq library is not available. "
        "Please install it with 'pip install jq' or use a different resolver."
    )

from .interface import ResolverSpec

JQ_KEYWORDS = re.compile(r"^\s*(if|map|reduce|foreach|while|until|label|break)\b")


class JqResolver(ResolverSpec):
    """A resolver using jq (C extension)."""

    def __init__(self):
        super().__init__()

    def _execute_query(self, path: str, context):
        """Execute a jq expression against the context."""
        # Compile and execute the expression

        if path.isidentifier() and isinstance(context, dict):
            return context[path]

        if path.startswith("."):
            jq_expr = path
        else:
            jq_expr = "." + path
        results = jq.compile(jq_expr).input(context).all()

        # Return the first result, or None if no results
        if results:
            return results[0]
        return None

    def _execute_raw_query(self, raw_expr, context):
        """Execute a raw jq expression.

        For jq, we need special handling of control flow expressions.
        """
        res = jq.compile(raw_expr).input(context).all()

        if res:
            return res[0]
        else:
            return None
