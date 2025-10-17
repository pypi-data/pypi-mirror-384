"""Google Search Console API client."""

from datetime import datetime, date
from pathlib import Path
from typing import Any

from fastmcp.exceptions import McpError
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from loguru import logger

from google_search_console_mcp_python.customtypes import (
    SearchType,
    AggregationType,
    Dimension,
)


class GSCClient:
    """Client for the Google Search Console API."""

    def __init__(self, credentials_path: Path, subject: str | None = None):
        """Initialize the Google Search Console API client.

        Args:
            credentials_path: Path to the Google Cloud credentials file.
            subject: Optional email address to impersonate using domain delegation.
        """
        self.credentials_path = credentials_path
        self.subject = subject
        self.credentials = self._get_credentials()
        self.service: Resource = build(
            "searchconsole", "v1", credentials=self.credentials, cache_discovery=False
        )

    def _get_credentials(self) -> service_account.Credentials:
        """Get the credentials for the Google Search Console API.

        Returns:
            Service account credentials, optionally with delegated subject.

        Raises:
            McpError: If the credentials file does not exist or is invalid.
        """
        if not self.credentials_path.exists():
            raise McpError(f"Credentials file not found: {self.credentials_path}")

        scopes = [
            "https://www.googleapis.com/auth/webmasters",
            "https://www.googleapis.com/auth/webmasters.readonly",
        ]

        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path), scopes=scopes
            )

            # If subject is provided, use domain-wide delegation to impersonate the user
            if self.subject:
                credentials = credentials.with_subject(self.subject)
                logger.debug(f"Applied domain delegation for subject: {self.subject}")

            return credentials
        except Exception as e:
            raise McpError(f"Failed to load credentials: {e}")

    async def get_search_analytics(
        self,
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
            site_url: The URL of the site to get data for.
            start_date: The start date for the data (YYYY-MM-DD).
            end_date: The end date for the data (YYYY-MM-DD).
            dimensions: The dimensions to group the data by.
            search_type: The type of search (web, image, video, news).
            aggregation_type: The type of aggregation to use.
            row_limit: The maximum number of rows to return.

        Returns:
            The search analytics data.

        Raises:
            McpError: If the API call fails or parameters are invalid.
        """
        # Create request body
        request_body = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rowLimit": min(row_limit, 25000),  # API maximum
        }
        if dimensions:
            request_body["dimensions"] = list(dimensions)

        # Add optional fields if provided
        if search_type:
            valid_types = {"web", "image", "video", "news", "discover", "googleNews"}
            if search_type not in valid_types:
                raise McpError(
                    f"Invalid search type: {search_type}. Must be one of {valid_types}"
                )
            request_body["searchType"] = search_type

        if aggregation_type:
            valid_types = {"auto", "byPage", "byProperty", "byNewsShowcasePanel"}
            if aggregation_type not in valid_types:
                raise McpError(
                    f"Invalid aggregation type: {aggregation_type}. Must be one of {valid_types}"
                )
            request_body["aggregationType"] = aggregation_type

        try:
            # Execute request
            response = (
                self.service.searchanalytics()
                .query(siteUrl=site_url, body=request_body)
                .execute()
            )

            # Format the response
            formatted_response = self._format_search_analytics(
                response, dimensions or set()
            )

            logger.debug(
                f"Retrieved {len(formatted_response['rows'])} rows for {site_url}"
            )
            return formatted_response

        except Exception as e:
            raise McpError(f"Search analytics API call failed: {e}")

    def _format_search_analytics(
        self, response: dict[str, Any], dimensions: set[Dimension]
    ) -> dict[str, Any]:
        """Format the search analytics response.

        Args:
            response: The response from the Google Search Console API.
            dimensions: The dimensions used in the request.

        Returns:
            The formatted response.
        """
        rows = response.get("rows", [])
        formatted_rows = []

        for row in rows:
            formatted_row = {}

            # Add dimensions
            for i, dim in enumerate(dimensions):
                if i < len(row.get("keys", [])):
                    formatted_row[dim] = row["keys"][i]

            # Add metrics
            formatted_row["clicks"] = row.get("clicks", 0)
            formatted_row["impressions"] = row.get("impressions", 0)
            formatted_row["ctr"] = row.get("ctr", 0)
            formatted_row["position"] = row.get("position", 0)

            formatted_rows.append(formatted_row)

        return {
            "rows": formatted_rows,
            "responseAggregationType": response.get("responseAggregationType", ""),
        }

    async def list_sites(self) -> list[dict[str, str]]:
        """List all sites in the Search Console account.

        Returns:
            List of sites with their URLs and permission levels.

        Raises:
            McpError: If the API call fails.
        """
        try:
            response = self.service.sites().list().execute()
            sites = response.get("siteEntry", [])

            result = [
                {
                    "siteUrl": site.get("siteUrl", ""),
                    "permissionLevel": site.get("permissionLevel", ""),
                }
                for site in sites
            ]

            logger.debug(f"Found {len(result)} sites")
            return result

        except Exception as e:
            raise McpError(f"List sites API call failed: {e}")

    async def get_site(self, site_url: str) -> dict[str, str]:
        """Get information about a specific site.

        Args:
            site_url: The URL of the site to get information for.

        Returns:
            Site information including URL and permission level.

        Raises:
            McpError: If the API call fails.
        """
        try:
            response = self.service.sites().get(siteUrl=site_url).execute()

            return {
                "siteUrl": response.get("siteUrl", ""),
                "permissionLevel": response.get("permissionLevel", ""),
            }

        except Exception as e:
            raise McpError(f"Get site API call failed for {site_url}: {e}")

    async def add_site(self, site_url: str) -> dict[str, str]:
        """Add a site to the Search Console account.

        Args:
            site_url: The URL of the site to add.

        Returns:
            Confirmation of the added site.

        Raises:
            McpError: If the API call fails.
        """
        try:
            self.service.sites().add(siteUrl=site_url).execute()

            logger.info(f"Successfully added site: {site_url}")
            return {
                "status": "success",
                "message": f"Site {site_url} added successfully",
            }

        except Exception as e:
            raise McpError(f"Add site API call failed for {site_url}: {e}")

    async def delete_site(self, site_url: str) -> dict[str, str]:
        """Remove a site from the Search Console account.

        Args:
            site_url: The URL of the site to remove.

        Returns:
            Confirmation of the removed site.

        Raises:
            McpError: If the API call fails.
        """
        try:
            self.service.sites().delete(siteUrl=site_url).execute()

            logger.info(f"Successfully removed site: {site_url}")
            return {
                "status": "success",
                "message": f"Site {site_url} removed successfully",
            }

        except Exception as e:
            raise McpError(f"Delete site API call failed for {site_url}: {e}")

    async def inspect_url(
        self, site_url: str, inspection_url: str, language_code: str | None = None
    ) -> dict[str, Any]:
        """Inspect a URL to get its Google index status.

        Args:
            site_url: The URL of the property.
            inspection_url: The URL to inspect.
            language_code: Optional language code for the inspection.

        Returns:
            URL inspection results including index status and crawl information.

        Raises:
            McpError: If the API call fails.
        """
        request_body = {"inspectionUrl": inspection_url, "siteUrl": site_url}

        if language_code:
            request_body["languageCode"] = language_code

        try:
            response = (
                self.service.urlInspection()
                .index()
                .inspect(body=request_body)
                .execute()
            )

            # Format the response for easier consumption
            inspection_result = response.get("inspectionResult", {})

            result = {
                "inspectionUrl": inspection_url,
                "siteUrl": site_url,
                "indexStatusResult": inspection_result.get("indexStatusResult", {}),
                "ampResult": inspection_result.get("ampResult", {}),
                "mobileUsabilityResult": inspection_result.get(
                    "mobileUsabilityResult", {}
                ),
                "richResultsResult": inspection_result.get("richResultsResult", {}),
            }

            logger.debug(f"URL inspection completed for: {inspection_url}")
            return result

        except Exception as e:
            raise McpError(f"URL inspection API call failed for {inspection_url}: {e}")
