"""Google Search Console MCP Server using FastMCP."""
from datetime import date
from typing import Any

from fastmcp import FastMCP
from loguru import logger

from google_search_console_mcp_python.customtypes import (
    SearchType,
    AggregationType,
    Dimension,
)
from .gsc_client import GSCClient
from .settings import load_settings

# Initialize settings
settings = load_settings()

# Initialize MCP server
mcp = FastMCP("Google Search Console")

# Initialize GSC client if credentials are available
gsc_client = GSCClient(settings.google_credentials, subject=settings.subject)
logger.info("Google Search Console client initialized")
if settings.subject:
    logger.info(f"Using domain delegation with subject: {settings.subject}")


@mcp.tool()
async def search_analytics(
    site_url: str,
    start_date: date,
    end_date: date,
    dimensions: set[Dimension] | None = None,
    search_type: SearchType | None = None,
    aggregation_type: AggregationType | None = None,
    row_limit: int = 1000,
) -> dict[str, Any]:
    """Get search analytics data from Google Search Console.

    Args:
        site_url: The URL of the site to get data for
        start_date: The start date for the data (YYYY-MM-DD)
        end_date: The end date for the data (YYYY-MM-DD)
        dimensions: Set of dimensions to group data by (query, page, country, device, searchAppearance)
        search_type: The type of search (web, image, video, news, discover, googleNews)
        aggregation_type: The type of aggregation (auto, byPage, byProperty, byNewsShowcasePanel)
        row_limit: The maximum number of rows to return (default: 1000, max: 25000)

    Returns:
        Dictionary containing search analytics data with metrics and dimensions
    """
    logger.info(
        f"Fetching search analytics for {site_url} from {start_date} to {end_date}"
    )

    result = await gsc_client.get_search_analytics(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
        search_type=search_type,
        aggregation_type=aggregation_type,
        row_limit=row_limit,
    )

    logger.info(f"Retrieved {len(result['rows'])} rows of search analytics data")
    return result


@mcp.tool()
async def list_sites() -> dict[str, list[dict[str, str]]]:
    """List all sites in your Google Search Console account.

    Returns:
        Dictionary containing a list of sites with their URLs and permission levels
    """
    logger.info("Fetching list of Search Console sites")

    sites = await gsc_client.list_sites()

    logger.info(f"Found {len(sites)} sites in Search Console account")
    return {"sites": sites}


@mcp.tool()
async def get_site(site_url: str) -> dict[str, str]:
    """Get information about a specific site in Google Search Console.

    Args:
        site_url: The URL of the site to get information for

    Returns:
        Dictionary containing site information including URL and permission level
    """
    logger.info(f"Fetching site information for: {site_url}")

    site_info = await gsc_client.get_site(site_url)

    logger.debug(f"Retrieved site info for {site_url}: {site_info['permissionLevel']}")
    return site_info


@mcp.tool()
async def add_site(site_url: str) -> dict[str, str]:
    """Add a new site to your Google Search Console account.

    Args:
        site_url: The URL of the site to add

    Returns:
        Dictionary containing the status and confirmation message
    """
    logger.info(f"Adding site to Search Console: {site_url}")

    result = await gsc_client.add_site(site_url)

    logger.info(f"Successfully added site: {site_url}")
    return result


@mcp.tool()
async def delete_site(site_url: str) -> dict[str, str]:
    """Remove a site from your Google Search Console account.

    Args:
        site_url: The URL of the site to remove

    Returns:
        Dictionary containing the status and confirmation message
    """
    logger.info(f"Removing site from Search Console: {site_url}")

    result = await gsc_client.delete_site(site_url)

    logger.info(f"Successfully removed site: {site_url}")
    return result


@mcp.tool()
async def inspect_url(
    site_url: str, inspection_url: str, language_code: str | None = None
) -> dict[str, Any]:
    """Inspect a URL to get its Google index status and other information.

    Args:
        site_url: The URL of the property that contains the URL to inspect
        inspection_url: The specific URL to inspect
        language_code: Optional language code for the inspection (e.g., 'en-US')

    Returns:
        Dictionary containing URL inspection results including index status and crawl information
    """
    logger.info(f"Inspecting URL: {inspection_url} in property: {site_url}")

    result = await gsc_client.inspect_url(
        site_url=site_url, inspection_url=inspection_url, language_code=language_code
    )

    logger.debug(f"URL inspection completed for: {inspection_url}")
    return result


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Google Search Console MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
