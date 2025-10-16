"""Username verification API for the GLChat Python client.

This module provides the UsernameAPI class for handling username-related verification operations
with the GLChat backend, including getting usernames by phone number.

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

# Constants
REQUEST_URL_LOG = "Request URL: %s"
REQUEST_HEADERS_LOG = "Request headers: %s"


class UsernameAPI:
    """Handles username API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client

    def _prepare_headers(
        self, extra_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Prepare headers for the API request.

        Args:
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            dict[str, str]: Dictionary containing the request headers
        """
        # Start with default headers from client
        headers = self._client.default_headers.copy()

        if self._client.api_key:
            headers["Authorization"] = f"Bearer {self._client.api_key}"

        # Merge with extra headers if provided
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def list(
        self,
        phone_number: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Get username by phone number.

        Args:
            phone_number (str): Phone number in international format
                (e.g., +62812345678 or 62812345678)
            extra_headers (dict[str, str] | None): Additional headers to include in the request.
                Use this to pass X-API-Key for WhatsApp authentication, and
                    X-Tenant-ID for multi-tenancy.

        Returns:
            dict[str, Any]: Dictionary containing the username response data

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Getting username for phone number: %s", phone_number)

        # Prepare request components
        url = urljoin(
            self._client.base_url, f"users/verification/username/{phone_number}"
        )
        base_headers = self._prepare_headers(extra_headers)

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=base_headers)
            response.raise_for_status()
            return response.json()
