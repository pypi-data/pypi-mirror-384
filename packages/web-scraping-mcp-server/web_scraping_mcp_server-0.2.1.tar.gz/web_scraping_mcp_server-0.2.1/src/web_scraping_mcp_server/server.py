"""Web scraping MCP server using FastMCP and ScrapingBee."""

from collections.abc import Callable
from typing import Annotated, Any

from fastmcp import FastMCP
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl

from . import extractors, logconfig
from .scraper import ScrapingService
from .scrapingbee.exceptions import ScrapingBeeError

logconfig.setup()

# Initialize FastMCP server
mcp = FastMCP("Web Scraping Server")


# Response models
class ErrorDetail(BaseModel):
    """Error detail information."""

    type: Annotated[str, Field(description="Error categorization")]
    message: Annotated[str, Field(description="Human readable error message")]


class ScrapeResponse(BaseModel):
    """Response model for scraping operations."""

    url: Annotated[HttpUrl, Field(description="The URL that was processed")]
    success: Annotated[bool, Field(description="Whether the operation succeeded")]
    data: Annotated[
        str | dict[str, Any] | list[str] | None,
        Field(description="The extracted data if successful"),
    ]
    error: Annotated[
        ErrorDetail | None,
        Field(description="Error details if the operation failed"),
    ]


def create_error_response(
    url: Annotated[str, "The URL that was processed"],
    error: Annotated[Exception, "The exception that occurred"],
) -> ScrapeResponse:
    """Create a standardized error response."""
    # Categorize the error
    if isinstance(error, ScrapingBeeError):
        if "timeout" in str(error).lower():
            error_type = "TIMEOUT_ERROR"
        elif "network" in str(error).lower():
            error_type = "NETWORK_ERROR"
        elif "404" in str(error) or "not found" in str(error).lower():
            error_type = "NOT_FOUND_ERROR"
        else:
            error_type = "API_ERROR"
    else:
        error_type = "PARSING_ERROR"

    return ScrapeResponse(
        url=url,
        success=False,
        data=None,
        error=ErrorDetail(type=error_type, message=str(error)),
    )


def create_success_response(
    url: Annotated[str, "The URL that was processed"],
    data: Annotated[str | dict[str, Any] | list[str] | None, "The extracted data"],
) -> ScrapeResponse:
    """Create a standardized success response."""
    return ScrapeResponse(url=url, success=True, data=data, error=None)


async def process_batch_urls(
    urls: Annotated[list[str], "List of URLs to process"],
    extraction_func: Annotated[
        Callable[[str], Any] | None, "Function to extract data from HTML"
    ] = None,
    render_js: Annotated[bool, "Whether to render JavaScript"] = True,
    user_agent: Annotated[str | None, "Custom user agent string"] = None,
    custom_headers: Annotated[
        dict[str, str] | None, "Additional headers to send"
    ] = None,
) -> list[ScrapeResponse]:
    """Process multiple URLs with the given extraction function."""
    results = []
    try:
        # Fetch HTML content for all URLs
        async with ScrapingService() as scraping_service:
            batch_results = await scraping_service.fetch_html_batch(
                urls=urls,
                render_js=render_js,
                user_agent=user_agent,
                custom_headers=custom_headers,
            )

        # Process each result
        for result in batch_results:
            url = result["url"]
            if not result["success"]:
                # Create error from the scraping failure
                error_msg = result.get("error", "Unknown scraping error")
                error = Exception(error_msg)
                results.append(create_error_response(url, error))
                continue

            try:
                if extraction_func is None:
                    # Return raw HTML content
                    data = result["content"]
                else:
                    # Apply extraction function
                    data = extraction_func(result["content"])
                results.append(create_success_response(url, data))
            except Exception as e:
                logger.exception("Error extracting data from URL: {}", url)
                results.append(create_error_response(url, e))

    except Exception as e:
        logger.exception("Error processing batch URLs")
        # Return error responses for all URLs
        results = [create_error_response(url, e) for url in urls]

    return results


# MCP Tools
@mcp.tool()
async def fetch_html(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Fetch raw HTML content from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with HTML content
    """
    return await process_batch_urls(
        urls,
        render_js=render_js,
        user_agent=user_agent,
        custom_headers=custom_headers,
    )


@mcp.tool()
async def extract_page_title(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract page titles from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with page titles
    """
    return await process_batch_urls(
        urls,
        extractors.extract_page_title,
        render_js,
        user_agent,
        custom_headers,
    )


@mcp.tool()
async def extract_meta_description(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract meta descriptions from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with meta descriptions
    """
    return await process_batch_urls(
        urls,
        extractors.extract_meta_description,
        render_js,
        user_agent,
        custom_headers,
    )


@mcp.tool()
async def extract_open_graph_metadata(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract Open Graph metadata from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with Open Graph metadata
    """
    return await process_batch_urls(
        urls,
        extractors.extract_open_graph_metadata,
        render_js,
        user_agent,
        custom_headers,
    )


@mcp.tool()
async def extract_h1_headers(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract H1 headers from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with H1 headers
    """
    return await process_batch_urls(
        urls,
        extractors.extract_h1_headers,
        render_js,
        user_agent,
        custom_headers,
    )


@mcp.tool()
async def extract_h2_headers(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract H2 headers from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with H2 headers
    """
    return await process_batch_urls(
        urls,
        extractors.extract_h2_headers,
        render_js,
        user_agent,
        custom_headers,
    )


@mcp.tool()
async def extract_h3_headers(
    urls: Annotated[
        list[HttpUrl], Field(min_length=1, description="List of URLs to process")
    ],
    render_js: Annotated[
        bool, Field(description="Whether to render JavaScript")
    ] = False,
    user_agent: Annotated[
        str | None, Field(description="Custom user agent string")
    ] = None,
    custom_headers: Annotated[
        dict[str, str] | None, Field(description="Additional headers to send")
    ] = None,
) -> list[ScrapeResponse]:
    """Extract H3 headers from URLs.

    Args:
        urls: List of URLs to process
        render_js: Whether to render JavaScript
        user_agent: Custom user agent string
        custom_headers: Additional headers to send

    Returns:
        List of result dicts with H3 headers
    """
    return await process_batch_urls(
        urls,
        extractors.extract_h3_headers,
        render_js,
        user_agent,
        custom_headers,
    )
