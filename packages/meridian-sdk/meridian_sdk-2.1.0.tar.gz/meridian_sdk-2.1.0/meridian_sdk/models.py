"""
Meridian SDK Models

Data models for API requests and responses.
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field


# Request Models

class SearchFilters(BaseModel):
    """Filters for search requests"""
    sources: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    date_range: Optional[Tuple[int, int]] = None
    entities: Optional[List[str]] = None


class SearchOptions(BaseModel):
    """Options for search requests"""
    max_results: int = 10
    include_sources: bool = True
    use_entity_filtering: bool = False
    search_type: str = "standard"
    use_semantic_search: bool = True


# Response Models

class SourceDocument(BaseModel):
    """Source document from search results"""
    content_id: Optional[str] = None
    uri: Optional[str] = None
    title: Optional[str] = None
    snippet: str
    relevance_score: float
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    source_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchMetadata(BaseModel):
    """Metadata about search operation"""
    request_id: str
    user_id: str
    query: str
    processing_time_ms: int
    timestamp: str
    search_type: str
    total_results: int


class SearchResponse(BaseModel):
    """Search response"""
    answer: Optional[str] = Field(None, description="LLM-generated answer with inline citations [1], [2], etc.")
    results: List[SourceDocument]
    metadata: SearchMetadata
    sources_count: int


class SummaryResult(BaseModel):
    """Summary search result"""
    summary_text: str
    referenced_ids: List[str]
    generated_at: str
    total_items: int
    relevance_score: float


class SummariesSearchResponse(BaseModel):
    """Summaries search response"""
    summaries: List[SummaryResult]
    metadata: SearchMetadata
    total_summaries: int


class ContextResponse(BaseModel):
    """Full document context response"""
    content_id: str
    title: str
    full_text: str
    content_type: str
    size_chars: int
    was_truncated: bool
    metadata: Dict[str, Any]


class UsageDay(BaseModel):
    """Usage statistics for a single day"""
    date: str
    requests: int
    tokens_used: int
    cost: float


class UsageResponse(BaseModel):
    """Usage statistics response"""
    period: str
    total_requests: int
    total_tokens: int
    total_cost: float
    daily_breakdown: List[UsageDay]
    current_tier: str


class RateLimitsResponse(BaseModel):
    """Rate limits response"""
    tier: str
    requests_per_minute: int
    requests_per_day: int
    remaining_minute: int
    remaining_day: int
    reset_minute: int
    reset_day: int


class DataSource(BaseModel):
    """Data source information"""
    name: str
    type: str
    is_connected: bool
    last_synced: Optional[str] = None
    item_count: Optional[int] = None


class DataSourcesResponse(BaseModel):
    """Data sources list response"""
    sources: List[DataSource]
    total_connected: int
    total_items: int


class HealthStatus(BaseModel):
    """Individual service health status"""
    status: str
    response_time_ms: Optional[int] = None
    last_checked: str
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    version: str
    timestamp: str
    services: Dict[str, HealthStatus]
