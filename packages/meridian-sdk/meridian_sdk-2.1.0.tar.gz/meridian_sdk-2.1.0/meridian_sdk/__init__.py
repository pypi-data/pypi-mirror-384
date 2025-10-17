"""
Meridian SDK

Python SDK for the Meridian AI Search API.
"""

from .version import __version__, __api_version__
from .client import MeridianAPI
from .models import (
    SearchFilters,
    SearchOptions,
    SearchResponse,
    SummariesSearchResponse,
    ContextResponse,
    UsageResponse,
    RateLimitsResponse,
    HealthResponse,
    DataSourcesResponse,
    SourceDocument,
    SummaryResult,
    DataSource
)
from .exceptions import (
    MeridianError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
    MeridianTimeoutError,
    MeridianConnectionError
)

__all__ = [
    # Version
    "__version__",
    "__api_version__",

    # Client
    "MeridianAPI",

    # Models
    "SearchFilters",
    "SearchOptions",
    "SearchResponse",
    "SummariesSearchResponse",
    "ContextResponse",
    "UsageResponse",
    "RateLimitsResponse",
    "HealthResponse",
    "DataSourcesResponse",
    "SourceDocument",
    "SummaryResult",
    "DataSource",

    # Exceptions
    "MeridianError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "MeridianTimeoutError",
    "MeridianConnectionError",
]
