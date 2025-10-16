"""Basic resolver implementation for minimal dictionary access."""

from .interface import ResolverSpec


class BasicResolver(ResolverSpec):
    """A minimal resolver that only supports top-level dictionary keys.

    This resolver is intended as a fallback when more sophisticated resolvers
    like JsonPathResolver or JqResolver are not available. It only supports:

    - Top-level dictionary keys
    - Direct item access (no nested paths)
    - No attribute access
    """

    def __init__(self):
        super().__init__()

    def _convert_path(self, path: str):
        """
        No conversion performed. The path is used as-is for top level lookup
        """
        return path

    def _execute_query(self, converted_path, context):
        """Execute simple key lookup in the context.

        Only returns values for top-level keys.
        """
        if not isinstance(context, dict):
            # Can only resolve keys in dictionaries
            return None

        # Direct key lookup in the dictionary
        return context.get(converted_path)

    def _execute_raw_query(self, raw_expr, context):
        """Execute a raw expression.

        For the basic resolver, raw expressions are treated the same as paths.
        """
        return self._execute_query(raw_expr, context)
