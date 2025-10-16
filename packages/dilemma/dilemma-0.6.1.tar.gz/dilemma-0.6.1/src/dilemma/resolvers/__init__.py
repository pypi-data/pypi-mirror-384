"""Resolver plugin management for dilemma."""

from ..logconf import get_logger

logger = get_logger("resolvers")

# Dictionary to store instantiated resolvers by name
_resolvers: dict[str, type] = {}
_default_resolver: str | None = None


def register_resolver(
    resolver_class: type, name: str | None = None, default: bool = True
):
    """Register a resolver with the system.

    Args:
        resolver_class: The resolver class to register
        name: Optional name for the resolver (defaults to class name)
        default: Whether this should be the default resolver
    """
    global _default_resolver

    # Create an instance of the resolver
    resolver = resolver_class()

    resolver_name = name or resolver_class.__name__.lower().replace("resolver", "")

    # Store in our resolver dictionary
    _resolvers[resolver_name] = resolver

    # Set as default if requested or if it's the first one
    if default or _default_resolver is None:
        _default_resolver = resolver_name

    logger.info(f"Registered resolver: {resolver_name}")
    return resolver


def resolve_path(path, context, resolver_name=None, raw=False):
    """Resolve a path using the appropriate resolver.

    Args:
        path: The path to resolve
        context: The context object
        resolver_name: Optional name of specific resolver to use
        raw: If True, the path is a raw expression in the resolver's native syntax

    Returns:
        The resolved value
    """

    res_name = resolver_name or _default_resolver
    resolver = _resolvers[res_name]
    logger.debug("Resolving path %s with resolver %s", path, res_name)
    return resolver.resolve_path(path, context, raw=raw)


async def resolve_path_async(path, context, resolver_name=None, raw=False):
    """Asynchronous version of resolve_path."""
    res_name = resolver_name or _default_resolver
    resolver = _resolvers[res_name]

    # Check if resolver supports async operations
    if hasattr(resolver, "resolve_path_async"):  # pragma: no cover
        return await resolver.resolve_path_async(path, context, raw=raw)
    else:
        # Fall back to sync version for backward compatibility
        return resolver.resolve_path(path, context, raw=raw)


# Try to register available resolvers
try:
    from .jsonpath_resolver import JsonPathResolver

    register_resolver(JsonPathResolver)
except ImportError:
    logger.info("JsonPath resolver not available")

try:
    from .jq_resolver import JqResolver

    register_resolver(JqResolver)
except ImportError:
    logger.info("JQ resolver not available")

if not _resolvers:  # pragma: no cover
    from .basic_resolver import BasicResolver

    register_resolver(BasicResolver)
    logger.warning("Using BasicResolver as fallback")


__all__ = ["register_resolver", "resolve_path"]
