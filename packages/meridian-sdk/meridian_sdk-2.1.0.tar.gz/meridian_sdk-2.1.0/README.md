# Meridian SDK for Python

Official Python SDK for the [Meridian AI Search API](https://www.trymeridian.dev) - Enterprise search across connected data sources.

## Features

- **AI-Powered Search** - Natural language search across SharePoint, Google Drive, Gmail, Outlook, Slack, GitHub, and more
- **Multiple Output Formats** - JSON, CSV, strings array, or markdown
- **Async/Await Support** - Built for high-performance applications
- **Automatic Retries** - Exponential backoff for failed requests
- **Usage Tracking** - Monitor API usage and costs
- **Type Hints** - Complete type annotations for better IDE support
- **Rate Limit Handling** - Automatic retry on rate limits

## Installation

```bash
pip install meridian-sdk
```

## Quick Start

```python
import asyncio
from meridian_sdk import MeridianAPI

async def main():
    # Initialize client
    async with MeridianAPI(api_key="kt_your_api_key_here") as client:

        # Search
        response = await client.search("What are our Q4 sales numbers?")

        # Print results
        for result in response.results:
            print(f"   {result.title}")
            print(f"   {result.snippet}")
            print(f"   Relevance: {result.relevance_score:.2%}\n")

asyncio.run(main())
```

## Authentication

Get your API key from the [Meridian Dashboard](https://dashboard.trymeridian.dev) and set it as an environment variable:

```bash
export MERIDIAN_API_KEY="kt_your_api_key_here"
```

Then use it in your code:

```python
import os
from meridian_sdk import MeridianAPI

api_key = os.getenv("MERIDIAN_API_KEY")
client = MeridianAPI(api_key=api_key)
```

## Core Features

### Standard Search

Search across all your connected data sources with natural language:

```python
from meridian_sdk import MeridianAPI, SearchFilters, SearchOptions

async with MeridianAPI(api_key=api_key) as client:
    # Simple search
    response = await client.search("project Apollo status")

    # Search with filters
    filters = SearchFilters(
        sources=["google_drive", "sharepoint"],
        file_types=["PDF", "DOCUMENT"],
        date_range=(30, 0)  # Past 30 days
    )

    options = SearchOptions(
        max_results=20,
        include_sources=True,
        use_entity_filtering=True  # AI-powered entity filtering
    )

    response = await client.search(
        query="Q4 financial reports",
        filters=filters,
        options=options
    )

    print(f"Found {len(response.results)} results from {response.sources_count} sources")
```

### Summaries Search

Search pre-generated daily summaries for emails, messages, or document changes:

```python
# Get email summaries about a specific topic
response = await client.search_summaries(
    query="Deloitte project communications",
    summary_type="EMAIL_SUMMARIES",
    date_range=(7, 0),  # Past week
    use_semantic_search=True
)

for summary in response.summaries:
    print(f"📧 {summary.generated_at}")
    print(f"   {summary.summary_text}")
    print(f"   References {len(summary.referenced_ids)} emails\n")

# Get all message summaries chronologically
response = await client.search_summaries(
    query="",
    summary_type="MESSAGE_SUMMARIES",
    date_range=(7, 0),
    use_semantic_search=False  # Chronological mode
)
```

### Full Document Context

Retrieve complete document text after finding relevant chunks:

```python
# First search for relevant documents
search_response = await client.search("API documentation")

# Get full context for the first result
if search_response.results:
    content_id = search_response.results[0].content_id
    context = await client.get_context(content_id, max_chars=50000)

    print(f"   {context.title}")
    print(f"   Size: {context.size_chars:,} characters")
    print(f"   Truncated: {context.was_truncated}")
    print(f"\n{context.full_text}")
```

### Output Formats

Get results in different formats for various use cases:

```python
# JSON (default) - structured data
response = await client.search("revenue", output_format="json")

# CSV - for spreadsheets
csv_data = await client.search("revenue", output_format="csv")
with open("results.csv", "w") as f:
    f.write(csv_data)

# Strings Array - simple list of snippets
snippets = await client.search("revenue", output_format="strings")
for snippet in snippets:
    print(snippet)

# Markdown - formatted with citations
markdown = await client.search("revenue", output_format="markdown")
print(markdown)
```

### Usage & Analytics

Monitor API usage and costs:

```python
# Get monthly usage
usage = await client.get_usage(period="month")
print(f"Total requests: {usage.total_requests}")
print(f"Total cost: ${usage.total_cost:.4f}")
print(f"Current tier: {usage.current_tier}")

# Daily breakdown
for day in usage.daily_breakdown:
    print(f"{day.date}: {day.requests} requests, ${day.cost:.4f}")

# Check rate limits
limits = await client.get_limits()
print(f"Remaining today: {limits.remaining_day}/{limits.requests_per_day}")
print(f"Remaining this minute: {limits.remaining_minute}/{limits.requests_per_minute}")
```

### Data Sources

List connected data sources:

```python
sources = await client.list_sources()
print(f"Connected sources: {sources.total_connected}")

for source in sources.sources:
    status = "✅" if source.is_connected else "❌"
    print(f"{status} {source.name} ({source.type})")
```

### Health Check

Check API status:

```python
health = await client.health_check()
print(f"API Status: {health.status}")
print(f"Version: {health.version}")

for service_name, service in health.services.items():
    print(f"  {service_name}: {service.status}")
```

## Advanced Examples

### Batch Processing

Process multiple searches efficiently:

```python
queries = [
    "Q4 sales report",
    "Employee handbook",
    "Product roadmap"
]

async with MeridianAPI(api_key=api_key) as client:
    tasks = [client.search(query) for query in queries]
    responses = await asyncio.gather(*tasks)

    for query, response in zip(queries, responses):
        print(f"Query: {query}")
        print(f"Results: {len(response.results)}\n")
```

### Error Handling

Handle errors gracefully:

```python
from meridian_sdk import (
    MeridianAPI, AuthenticationError, RateLimitError,
    ValidationError, ServerError
)

async with MeridianAPI(api_key=api_key) as client:
    try:
        response = await client.search("test query")
    except AuthenticationError:
        print("Invalid API key")
    except RateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after}s")
    except ValidationError as e:
        print(f"Validation error: {e.message}")
    except ServerError as e:
        print(f"Server error: {e.status_code}")
```

### Context Manager vs Manual Management

```python
# Recommended: Use context manager (auto cleanup)
async with MeridianAPI(api_key=api_key) as client:
    response = await client.search("query")

# Manual management (if needed)
client = MeridianAPI(api_key=api_key)
await client.__aenter__()
try:
    response = await client.search("query")
finally:
    await client.__aexit__(None, None, None)
```

## Configuration

### Environment Variables

```bash
# API Key (required)
export MERIDIAN_API_KEY="kt_your_api_key_here"

# Base URL (optional, defaults to production)
export MERIDIAN_BASE_URL="https://dashboard.trymeridian.dev"
```

### Client Options

```python
client = MeridianAPI(
    api_key="kt_...",
    base_url="https://dashboard.trymeridian.dev",  # Custom endpoint
    timeout=60.0,  # Request timeout in seconds
    max_retries=3  # Maximum retry attempts
)
```

## API Reference

### MeridianAPI

Main client class for interacting with the API.

**Methods:**
- `search(query, output_format, filters, options)` - Execute search
- `search_summaries(query, summary_type, date_range, use_semantic_search, output_format)` - Search summaries
- `get_context(content_id, max_chars)` - Get full document
- `get_usage(period, start_date, end_date)` - Get usage stats
- `get_limits()` - Get rate limits
- `health_check()` - Check API health
- `list_sources()` - List data sources

### Models

**SearchFilters:**
- `sources` - List of source names
- `file_types` - List of file types
- `date_range` - (days_back, days_forward) tuple
- `entities` - List of entity names

**SearchOptions:**
- `max_results` - Maximum results (1-100)
- `include_sources` - Include source documents
- `use_entity_filtering` - Enable AI entity filtering
- `search_type` - "standard" or "summaries"

See full API documentation at [trymeridian.dev/docs/api](https://www.trymeridian.dev/docs/api)

## Support

- **Email:** kn@trymeridian.dev
- **Documentation:** [trymeridian.dev/docs/api](https://www.trymeridian.dev/docs/api)

## License

MIT License - see LICENSE file for details

## Built by Meridian

Enterprise AI search that actually works.

[Website](https://www.trymeridian.dev) | [Dashboard](https://dashboard.trymeridian.dev) | [Docs](https://www.trymeridian.dev/docs/api)
