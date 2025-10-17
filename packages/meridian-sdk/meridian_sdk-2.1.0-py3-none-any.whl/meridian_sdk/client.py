"""
Meridian SDK Client

Main client for interacting with the Meridian API.
"""

import asyncio
from typing import Optional, Dict, Any, List, Union, Tuple
from urllib.parse import urljoin
import httpx

from .version import __version__, __api_version__
from .models import (
    SearchFilters, SearchOptions, SearchResponse,
    SummariesSearchResponse, ContextResponse, UsageResponse,
    RateLimitsResponse, HealthResponse, DataSourcesResponse
)
from .exceptions import (
    MeridianError, AuthenticationError, RateLimitError,
    ValidationError, NotFoundError, ServerError,
    MeridianTimeoutError, MeridianConnectionError
)


class MeridianAPI:
    """
    Meridian API Client

    Async client for interacting with the Meridian AI Search API.

    Example:
        ```python
        import asyncio
        from meridian_sdk import MeridianAPI

        async def main():
            async with MeridianAPI(api_key="kt_...") as client:
                response = await client.search("Q4 sales numbers")
                print(response.results)

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashboard.trymeridian.dev",
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize the Meridian API client.

        Args:
            api_key: Your Meridian API key (starts with 'kt_')
            base_url: API base URL (default: production)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        if not api_key or not api_key.startswith("kt_"):
            raise ValueError("Invalid API key format. Keys must start with 'kt_'")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client (will be created in __aenter__)
        self._client: Optional[httpx.AsyncClient] = None
        self._owned_client = False

    async def __aenter__(self) -> "MeridianAPI":
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": f"meridian-sdk-python/{__version__}",
                "Content-Type": "application/json"
            }
        )
        self._owned_client = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._owned_client and self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client, raise if not initialized"""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with MeridianAPI(...) as client:' "
                "or call 'await client.__aenter__()'"
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data as dict

        Raises:
            MeridianError: On API errors
        """
        client = self._get_client()
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, url, **kwargs)

                # Handle rate limiting with retry
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                        retry_after=retry_after,
                        response=response.json() if response.content else None
                    )

                # Handle auth errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Invalid or expired API key",
                        status_code=401,
                        response=response.json() if response.content else None
                    )

                # Handle validation errors (400 and 422)
                if response.status_code in [400, 422]:
                    error_data = response.json() if response.content else {}
                    # Extract error message from Pydantic validation errors
                    detail = error_data.get("detail", "Validation error")
                    if isinstance(detail, list) and len(detail) > 0:
                        # Pydantic validation error format
                        first_error = detail[0]
                        error_msg = first_error.get("msg", "Validation error")
                    else:
                        error_msg = detail if isinstance(detail, str) else "Validation error"

                    raise ValidationError(
                        error_msg,
                        status_code=response.status_code,
                        response=error_data
                    )

                # Handle not found
                if response.status_code == 404:
                    raise NotFoundError(
                        "Resource not found",
                        status_code=404,
                        response=response.json() if response.content else None
                    )

                # Handle server errors with retry
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise ServerError(
                        f"Server error: {response.status_code}",
                        status_code=response.status_code,
                        response=response.json() if response.content else None
                    )

                # Success
                response.raise_for_status()

                # Return response based on content type
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    return response.json()
                else:
                    # For non-JSON responses (CSV, markdown, etc.)
                    return {"content": response.text, "content_type": response.headers.get("Content-Type")}

            except httpx.TimeoutException as e:
                last_exception = MeridianTimeoutError(
                    f"Request timeout after {self.timeout}s",
                    response=None
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except httpx.ConnectError as e:
                last_exception = MeridianConnectionError(
                    f"Connection failed: {str(e)}",
                    response=None
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except (AuthenticationError, RateLimitError, ValidationError, NotFoundError, ServerError):
                raise

            except Exception as e:
                last_exception = MeridianError(f"Unexpected error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        raise MeridianError("Request failed after all retries")

    # API Methods

    async def search(
        self,
        query: str,
        output_format: str = "json",
        filters: Optional[SearchFilters] = None,
        options: Optional[SearchOptions] = None
    ) -> Union[SearchResponse, str, List[str]]:
        """
        Execute a search across connected data sources.

        Args:
            query: Search query (natural language or structured)
            output_format: Output format - "json", "csv", "strings", "markdown"
            filters: Search filters (sources, file types, date range, entities)
            options: Search options (max results, entity filtering, etc.)

        Returns:
            SearchResponse (for JSON) or formatted string/list

        Example:
            ```python
            # Simple search
            response = await client.search("Q4 sales numbers")

            # With filters
            filters = SearchFilters(
                sources=["google_drive", "sharepoint"],
                date_range=(30, 0)  # Past 30 days
            )
            response = await client.search("project status", filters=filters)

            # CSV output
            csv_data = await client.search("revenue", output_format="csv")
            ```
        """
        payload = {
            "query": query,
            "output_format": output_format,
            "filters": filters.model_dump() if filters else {},
            "options": options.model_dump() if options else {}
        }

        result = await self._request("POST", f"/api/{__api_version__}/search", json=payload)

        # Return based on format
        if output_format == "json":
            return SearchResponse(**result)
        elif output_format == "strings":
            return result if isinstance(result, list) else [result]
        else:
            return result.get("content", result) if isinstance(result, dict) else result

    async def search_summaries(
        self,
        query: str,
        summary_type: str,
        date_range: Optional[Tuple[int, int]] = None,
        use_semantic_search: bool = True,
        output_format: str = "json"
    ) -> Union[SummariesSearchResponse, str, List[str]]:
        """
        Search pre-generated daily summaries.

        Args:
            query: Search query (can be empty for chronological retrieval)
            summary_type: "EMAIL_SUMMARIES", "MESSAGE_SUMMARIES", or "DIFF_SUMMARIES"
            date_range: Optional (days_back, days_forward) tuple
            use_semantic_search: True for semantic search, False for chronological
            output_format: Output format

        Returns:
            SummariesSearchResponse or formatted output

        Example:
            ```python
            # Get email summaries about a topic
            response = await client.search_summaries(
                query="project X discussions",
                summary_type="EMAIL_SUMMARIES",
                date_range=(7, 0)
            )

            # Get all summaries chronologically
            response = await client.search_summaries(
                query="",
                summary_type="MESSAGE_SUMMARIES",
                date_range=(7, 0),
                use_semantic_search=False
            )
            ```
        """
        payload = {
            "query": query,
            "summary_type": summary_type,
            "date_range": list(date_range) if date_range else None,
            "use_semantic_search": use_semantic_search,
            "output_format": output_format
        }

        result = await self._request("POST", f"/api/{__api_version__}/search/summaries", json=payload)

        if output_format == "json":
            return SummariesSearchResponse(**result)
        elif output_format == "strings":
            return result if isinstance(result, list) else [result]
        else:
            return result.get("content", result) if isinstance(result, dict) else result

    async def get_context(
        self,
        content_id: str,
        max_chars: int = 50000
    ) -> ContextResponse:
        """
        Retrieve full document context.

        Args:
            content_id: Content ID from search results
            max_chars: Maximum characters to return (with smart truncation)

        Returns:
            ContextResponse with full document text

        Example:
            ```python
            # Get full document
            context = await client.get_context("content_id_123")
            print(context.full_text)
            ```
        """
        payload = {
            "content_id": content_id,
            "max_chars": max_chars
        }

        result = await self._request("POST", f"/api/{__api_version__}/context", json=payload)
        return ContextResponse(**result)

    async def get_usage(
        self,
        period: str = "month",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> UsageResponse:
        """
        Get API usage statistics.

        Args:
            period: Time period - "day", "week", "month", "year"
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            UsageResponse with statistics

        Example:
            ```python
            usage = await client.get_usage(period="month")
            print(f"Total requests: {usage.total_requests}")
            print(f"Total cost: ${usage.total_cost}")
            ```
        """
        params = {"period": period}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        result = await self._request("GET", f"/api/{__api_version__}/usage", params=params)
        return UsageResponse(**result)

    async def get_limits(self) -> RateLimitsResponse:
        """
        Get current rate limits and quotas.

        Returns:
            RateLimitsResponse with limits

        Example:
            ```python
            limits = await client.get_limits()
            print(f"Remaining today: {limits.remaining_day}")
            ```
        """
        result = await self._request("GET", f"/api/{__api_version__}/limits")
        return RateLimitsResponse(**result)

    async def health_check(self) -> HealthResponse:
        """
        Check API health status.

        Returns:
            HealthResponse with status

        Example:
            ```python
            health = await client.health_check()
            print(f"API Status: {health.status}")
            ```
        """
        result = await self._request("GET", f"/api/{__api_version__}/health")
        return HealthResponse(**result)

    async def list_sources(self) -> DataSourcesResponse:
        """
        List all connected data sources.

        Returns:
            DataSourcesResponse with source information

        Example:
            ```python
            sources = await client.list_sources()
            for source in sources.sources:
                print(f"{source.name}: {source.is_connected}")
            ```
        """
        result = await self._request("GET", f"/api/{__api_version__}/sources")
        return DataSourcesResponse(**result)

    # Utility methods

    def get_rate_limit_info(self, response: SearchResponse) -> Dict[str, Any]:
        """
        Extract rate limit information from search response headers.

        Note: This requires accessing response headers, which are not directly
        available in the response model. Use the httpx response object directly
        for this information.

        Args:
            response: Search response

        Returns:
            Dict with rate limit info
        """
        # This is a helper for when users need rate limit info
        # They should check the HTTP headers directly
        return {
            "note": "Rate limit headers are available in HTTP response headers",
            "headers": [
                "X-RateLimit-Limit-Minute",
                "X-RateLimit-Remaining-Minute",
                "X-RateLimit-Reset-Minute",
                "X-RateLimit-Limit-Day",
                "X-RateLimit-Remaining-Day",
                "X-RateLimit-Reset-Day"
            ]
        }
