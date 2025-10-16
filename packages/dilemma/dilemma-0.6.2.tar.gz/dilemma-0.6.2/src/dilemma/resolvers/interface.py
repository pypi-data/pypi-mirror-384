"""Interface for variable resolvers in dilemma."""

import traceback
from ..errors import VariableError
from ..logconf import get_logger


class ResolverSpec:
    """Base class for variable resolvers."""

    def __init__(self):
        self.logger = get_logger(f"resolvers.{self.__class__.__name__.lower()}")

    def resolve_path(self, path: str, context, raw=False):
        """Main entry point for path resolution with error handling.

        This method handles error reporting and provides a consistent interface.
        Subclasses shouldn't override this method, but instead implement the
        protected methods below.
        """
        original_path = path
        resolver_type = self.__class__.__name__.lower().replace("resolver", "")
        try:
            if raw:
                # For raw expressions, use dedicated method
                self.logger.debug("Resolving raw expression: %s", path)
                result = self._execute_raw_query(path, context)
            else:
                # For standard path expressions, convert then execute
                converted_path = self._convert_path(path)
                self.logger.debug("Converted path '%s' to '%s'", path, converted_path)
                result = self._execute_query(converted_path, context)

            # Handle null/missing results
            if result is None:
                raise VariableError(
                    template_key="unresolved_path",
                    path=original_path,
                    resolver=resolver_type,
                    details="Path resolves to null or is missing",
                )

            return result

        except VariableError:
            # Pass through already-formatted errors
            raise

        except Exception as e:
            # Handle all other errors with useful context
            self.logger.warning(f"Error resolving '{original_path}': {str(e)}")
            self.logger.debug(traceback.format_exc())
            if raw:
                raise VariableError(
                    template_key="invalid_raw_expression",
                    path=original_path,
                    resolver=resolver_type,
                    details=str(e),
                )
            else:
                key = (
                    "undefined_variable"
                    if original_path.isidentifier()
                    else "unresolved_path"
                )
                raise VariableError(
                    template_key=key,
                    path=original_path,
                    resolver=resolver_type,
                    details=str(e),
                )

    # Protected methods to be implemented by subclasses
    def _convert_path(self, path):
        """Convert a dilemma path to resolver-specific syntax."""
        # Handle possessive paths by default
        if "'s" in path:
            import re

            return re.sub(r"'s\s+", ".", path)
        return path

    def _execute_query(self, converted_path, context):
        """Execute the converted path against the context."""
        raise NotImplementedError("Resolver must implement _execute_query method")

    def _execute_raw_query(self, raw_expr, context):
        """Execute a raw expression directly.

        Subclasses must override for different handling of raw expressions.
        """
        raise NotImplementedError("Resolver must implement _execute_raw_query method")
