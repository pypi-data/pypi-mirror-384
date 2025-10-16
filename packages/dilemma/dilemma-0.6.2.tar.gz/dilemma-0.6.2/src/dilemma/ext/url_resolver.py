from ..resolvers.interface import AsyncResolverSpec


# Example implementation
class UrlResolver(AsyncResolverSpec):
    """Resolver for URL content using aiohttp."""

    def __init__(self):
        super().__init__()
        self._session = None

    async def _ensure_session(self):
        """Lazily create aiohttp session."""
        if self._session is None:
            import aiohttp

            self._session = aiohttp.ClientSession()
        return self._session

    async def _execute_query_async(self, url, context):
        """Fetch content from a URL asynchronously."""
        import urllib.parse

        # Context could be a base URL
        if context and isinstance(context, str):
            url = urllib.parse.urljoin(context, url)

        session = await self._ensure_session()
        async with session.get(url) as response:
            if response.status == 200:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                else:
                    return await response.text()
            return None

    # Cleanup
    async def close(self):
        """Close the session when done."""
        if self._session:
            await self._session.close()
            self._session = None
