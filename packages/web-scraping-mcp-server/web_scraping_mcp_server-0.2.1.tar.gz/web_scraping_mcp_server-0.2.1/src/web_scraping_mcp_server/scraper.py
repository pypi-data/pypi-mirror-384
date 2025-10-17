"""Scraping service using ScrapingBee."""

import asyncio
from types import TracebackType
from typing import Any, Self

from loguru import logger

from .scrapingbee import ScrapingBeeClient
from .scrapingbee.exceptions import ScrapingBeeError
from .settings import settings


class ScrapingService:
    """Service for scraping HTML content using ScrapingBee."""

    def __init__(self) -> None:
        """Initialize the scraping service."""
        self._client: ScrapingBeeClient | None = None

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

    async def _get_client(self) -> ScrapingBeeClient:
        """Get or create the ScrapingBee client."""
        if isinstance(self._client, ScrapingBeeClient):
            return self._client
        if not settings.scrapingbee_api_key:
            msg = "SCRAPINGBEE_API_KEY is required. Please set it as an environment variable."
            raise ValueError(msg)
        self._client = ScrapingBeeClient(
            api_key=settings.scrapingbee_api_key,
            concurrency=settings.default_concurrency,
        )
        return self._client

    async def close(self) -> None:
        """Close the scraping service and cleanup resources."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _fetch_single_url(
        self,
        client: ScrapingBeeClient,
        url: str,
        render_js: bool,
        user_agent: str | None,
        custom_headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Fetch a single URL and return standardized result."""
        try:
            params = {}
            if render_js:
                params["render_js"] = render_js
            if custom_headers:
                params["headers"] = custom_headers
            if user_agent:
                if params.get("headers"):
                    params["headers"]["User-Agent"] = user_agent
                else:
                    params["headers"] = {"User-Agent": user_agent}

            response = await client.get(url=url, **params)
            return {
                "url": url,
                "success": True,
                "content": response.get("body", ""),
                "error": None,
            }
        except ScrapingBeeError as e:
            logger.exception("Failed to scrape {}", url)
            return {
                "url": url,
                "success": False,
                "content": None,
                "error": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error scraping {}", url)
            return {
                "url": url,
                "success": False,
                "content": None,
                "error": f"Unexpected error: {str(e)}",
            }

    async def fetch_html_batch(
        self,
        urls: list[str],
        render_js: bool = True,
        user_agent: str | None = None,
        custom_headers: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch HTML content from multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            render_js: Whether to render JavaScript
            user_agent: Custom user agent string
            custom_headers: Additional headers to send

        Returns:
            List of results with 'url', 'success', 'content', and 'error' keys
        """
        client = await self._get_client()

        # Use default user agent if none provided
        if user_agent is None:
            user_agent = settings.default_user_agent

        logger.info("Fetching HTML from {} URLs", len(urls))

        # Execute all requests concurrently
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self._fetch_single_url(
                        client=client,
                        url=url,
                        render_js=render_js,
                        user_agent=user_agent,
                        custom_headers=custom_headers,
                    )
                )
                for url in urls
            ]
        return [task.result() for task in tasks if task.done()]
