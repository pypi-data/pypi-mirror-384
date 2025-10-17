"""Exceptions for the ScrapingBee service."""


class ScrapingBeeError(Exception):
    """Base class for Semrush errors."""

    pass


class MissingKeyError(ScrapingBeeError):
    """Raised when no API key is provided for the ScrapingBee client."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__(
            "No API key provided for ScrapingBee client. You must set the "
            "`SCRAPINGBEE_API_KEY` environment variable or pass the `api_key` argument "
            "to the constructor."
        )


class ResponseError(ScrapingBeeError):
    """Raised when an error occurs during a request to the ScrapingBee API."""

    pass


class PaymentRequiredError(ResponseError):
    """Raised when payment is required to access the ScrapingBee API."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__("No more credit available. Upgrade plan and try again.")


class NotFoundError(ResponseError):
    """Raised when the requested URL is not found."""

    def __init__(self, url: str) -> None:
        """Initializes the error."""
        self.url = url
        super().__init__("The requested URL was not found.")


class TooManyRequestsError(ResponseError):
    """Raised when the ScrapingBee API limits requests."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__("Too many concurrent requests.")


class ServerError(ResponseError):
    """Raised when the ScrapingBee API returns a server error."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__("The requested URL responded with an error.")


class RequestTimeoutError(ResponseError):
    """Raised when the ScrapingBee API request times out."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__("The requested URL took too long to respond.")


class ResponseUnreadableError(ResponseError):
    """Raised when the response from the ScrapingBee is not readable."""

    def __init__(self) -> None:
        """Initializes the error."""
        super().__init__("ScrapingBee response not readable.")


class ScrapeError(ScrapingBeeError):
    """Raised when an error occurs during scraping."""

    pass


class ResponseNotHTMLError(ScrapeError):
    """Raised when the response from the scraped URL is not HTML."""

    def __init__(self, url: str, response_type: str) -> None:
        """Initializes the error."""
        self.url = url
        self.response_type = response_type
        super().__init__("The response from the scraped URL is not HTML.")
