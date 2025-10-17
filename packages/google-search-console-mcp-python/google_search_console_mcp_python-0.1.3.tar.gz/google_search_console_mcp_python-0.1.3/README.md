# Google Search Console MCP Server

A Model Context Protocol (MCP) server for comprehensive Google Search Console API access, built with FastMCP.

## Features

- **Search Analytics** - Query performance data with clicks, impressions, CTR, and position metrics
- **Site Management** - List, add, remove, and inspect Search Console properties  
- **URL Inspection** - Check index status and crawl information for specific URLs
- **Domain Delegation** - Support for service account impersonation across Google Workspace domains
- **FastMCP Framework** - Built with the fast, Pythonic way to create MCP servers
- **Type Safety** - Full type hints and Pydantic validation
- **Comprehensive Logging** - Structured logging with loguru

## Installation

### Using uv (Recommended)

```bash
# Install globally
uv tool install google-search-console-mcp-python

# Run directly without installation
uvx google-search-console-mcp-python
```

### Using pip

```bash
pip install google-search-console-mcp-python
```

## Authentication Setup

### Service Account Creation

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project and enable "Search Console API"  
3. Create Service Account with JSON key
4. In Search Console, add service account email as property owner

### Domain-Wide Delegation (Optional)

For Google Workspace domains to impersonate users:

1. Enable domain-wide delegation in service account settings
2. In Google Admin Console, authorize the service account
3. Add required scopes:
   - `https://www.googleapis.com/auth/webmasters`
   - `https://www.googleapis.com/auth/webmasters.readonly`

## Configuration

### Environment Variables

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
export GOOGLE_APPLICATION_SUBJECT=admin@yourdomain.com  # Optional: for domain delegation
```

### Running the Server

```bash
# Using uvx (recommended)
uvx google-search-console-mcp-python

# With domain delegation
GOOGLE_APPLICATION_SUBJECT=admin@domain.com uvx google-search-console-mcp-python

# Using pip installation  
google-search-console-mcp-python
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "gsc": {
      "command": "uvx",
      "args": ["google-search-console-mcp-python"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "GOOGLE_APPLICATION_SUBJECT": "admin@domain.com"
      }
    }
  }
}
```

## Available Tools

### search_analytics
Retrieve search performance data with comprehensive metrics and dimensions.

**Parameters:**
- `site_url` (required): Property URL 
- `start_date`, `end_date` (required): Date range (YYYY-MM-DD)
- `dimensions`: Array of dimension strings: `["query", "page", "country", "device", "searchAppearance"]`
- `search_type`: One of: `"web"`, `"image"`, `"video"`, `"news"`, `"discover"`, `"googleNews"`
- `aggregation_type`: One of: `"auto"`, `"byPage"`, `"byProperty"`, `"byNewsShowcasePanel"`
- `row_limit`: Max 25,000 rows (default: 1,000)

**Example:**
```json
{
  "site_url": "https://example.com",
  "start_date": "2024-01-01", 
  "end_date": "2024-01-31",
  "dimensions": ["query", "country"],
  "search_type": "web",
  "row_limit": 5000
}
```

### list_sites
List all Search Console properties accessible to the authenticated account.

### get_site
Get detailed information about a specific Search Console property.

**Parameters:**
- `site_url` (required): Property URL

### add_site  
Add a new property to Search Console.

**Parameters:**
- `site_url` (required): Property URL to add

### delete_site
Remove a property from Search Console.

**Parameters:** 
- `site_url` (required): Property URL to remove

### inspect_url
Inspect URL index status and crawl information.

**Parameters:**
- `site_url` (required): Property containing the URL
- `inspection_url` (required): URL to inspect  
- `language_code` (optional): Language code (e.g., 'en-US')

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/locomotive-agency/google-search-console-mcp-python.git
cd google-search-console-mcp-python

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code  
uv run ruff check

# Type checking
uv run mypy src/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_server.py -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html
```

## Requirements

- Python 3.12+
- Google Cloud project with Search Console API enabled
- Service account with Search Console access
- uv package manager (recommended)

## Architecture

Built with modern Python best practices:

- **FastMCP** - High-performance MCP server framework
- **Pydantic** - Type validation and settings management  
- **Loguru** - Structured logging
- **Google API Client** - Official Google APIs library
- **Async/Await** - Non-blocking I/O operations

### Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires authentication)
uv publish
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following code quality standards
4. Add tests for new functionality  
5. Submit a pull request

## License

MIT

---

Built with ❤️ by [Locomotive Agency](https://locomotive.agency) using the FastMCP framework.

Inspired by and adapted from [guchey/mcp-server-google-search-console](https://github.com/guchey/mcp-server-google-search-console).
