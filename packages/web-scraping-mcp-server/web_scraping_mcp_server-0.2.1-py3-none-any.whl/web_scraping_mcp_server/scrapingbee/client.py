"""Client for the ScrapingBee API."""

import json
import os
from collections.abc import Mapping, MutableMapping
from types import TracebackType
from typing import Any, Never, Self

import httpx
import tenacity
from loguru import logger

from .exceptions import (
    MissingKeyError,
    NotFoundError,
    PaymentRequiredError,
    RequestTimeoutError,
    ResponseNotHTMLError,
    ResponseUnreadableError,
    ServerError,
    TooManyRequestsError,
)


def process_headers(
    headers: Mapping[str, Any], prefix: str = "Spb-"
) -> Mapping[str, Any]:
    """Processes headers for the ScrapingBee API."""
    return {f"{prefix}{k}": v for k, v in headers.items()}


def handle_status_error(e: httpx.HTTPStatusError, request_url: str) -> Never:
    """Handles status errors for the ScrapingBee API."""
    if e.response.status_code in {404, 410}:
        raise NotFoundError(request_url) from e
    elif e.response.status_code == 429:
        raise TooManyRequestsError() from e
    elif e.response.status_code == 401:
        raise PaymentRequiredError() from e
    elif 500 <= e.response.status_code < 600:
        raise ServerError() from e
    else:
        raise


class ScrapingBeeClient:
    """Client for the ScrapingBee API."""

    ENDPOINT = "https://app.scrapingbee.com/api/v1/"

    def __init__(self, api_key: str | None = None, concurrency: int = 5) -> None:
        """Initializes the client."""
        try:
            self.api_key = api_key or os.environ["SCRAPINGBEE_API_KEY"]
        except KeyError as e:
            raise MissingKeyError() from e
        concurrency = max(concurrency, 1)
        limits = httpx.Limits(
            max_keepalive_connections=concurrency, max_connections=concurrency
        )
        self._client = httpx.AsyncClient(
            http2=True,
            base_url=self.ENDPOINT,
            params={"api_key": self.api_key, "json_response": True},
            timeout=90.0,
            limits=limits,
        )

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(
            (httpx.TransportError, RequestTimeoutError, ServerError)
        ),
        wait=tenacity.wait_exponential(multiplier=2, max=20),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=tenacity.before_sleep_log(logger, "DEBUG"),
        reraise=True,
    )
    async def _request(self, params: MutableMapping[str, Any]) -> Mapping[str, Any]:
        """Makes a request to the ScrapingBee API."""
        try:
            headers = process_headers(params.pop("headers"))
            params["forward_headers"] = True
        except KeyError:
            headers = None

        with logger.contextualize(scrape_params=params, scrape_headers=headers):
            logger.debug("Fetching response from ScrapingBee API: {}", params["url"])
            try:
                response = await self._client.get("/", params=params, headers=headers)
                response.raise_for_status()
            except httpx.TimeoutException as e:
                raise RequestTimeoutError() from e
            except httpx.HTTPStatusError as e:
                handle_status_error(e, params["url"])
            logger.debug("Received response from ScrapingBee API: {}", params["url"])

        try:
            return response.json()
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.debug("Response text:\n{}", response.text)
            raise ResponseUnreadableError() from e

    async def get(self, url: str, **kwargs) -> Mapping[str, Any]:
        """Fetches a response from the ScrapingBee API."""
        params = {"url": url}
        valid_kwargs = {k: v for k, v in kwargs.items() if k not in {"url", "api_key"}}
        params.update(valid_kwargs)
        return await self._request(params=params)

    async def get_html(self, url: str, **kwargs) -> str:
        """Fetches HTML content from the ScrapingBee API, otherwise raises an error."""
        response = await self.get(url, **kwargs)
        if response["type"] != "html":
            raise ResponseNotHTMLError(url=url, response_type=response["type"])
        return response["body"]

    async def close(self) -> None:
        """Closes the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enters the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exits the async context manager."""
        await self.close()
