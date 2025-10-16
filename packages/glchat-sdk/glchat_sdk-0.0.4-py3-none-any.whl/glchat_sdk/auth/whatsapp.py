"""WhatsApp authentication API for the GLChat Python client.

This module provides the WhatsAppAPI class for handling WhatsApp-specific authentication operations
with the GLChat backend, including user registration.

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
REQUEST_DATA_LOG = "Request data: %s"
CONTENT_TYPE_JSON = "application/json"


class WhatsAppAPI:
    """Handles WhatsApp authentication API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client

    def _prepare_headers(
        self, extra_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Prepare headers for API requests.

        Args:
            extra_headers (dict[str, str] | None): Additional headers to include in the request.
                These will override any existing keys in default_headers.

        Returns:
            dict[str, str]: Dictionary containing the request headers
        """
        # Start with default headers from client
        headers = self._client.default_headers.copy()

        # Include API key if available
        if self._client.api_key:
            headers["Authorization"] = f"Bearer {self._client.api_key}"

        # Merge with extra headers if provided (extra_headers will override existing keys)
        if extra_headers:
            headers.update(extra_headers)

        return headers

    def register(
        self,
        whatsapp_id: str,
        email: str,
        profile_name: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Register new users with WhatsApp.

        Args:
            whatsapp_id (str): WhatsApp ID of the user
            email (str): Email address of the user
            profile_name (str | None): Profile name of the user (optional)
            extra_headers (dict[str, str] | None): Additional headers to include in the request.
                Use this to pass X-API-Key for WhatsApp authentication,
                X-Tenant-ID for multi-tenancy.

        Returns:
            dict[str, Any]: Dictionary containing the registration response data

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug(
            "Registering WhatsApp user: whatsapp_id=%s, email=%s, profile_name=%s",
            whatsapp_id,
            email,
            profile_name,
        )

        # Prepare request components
        url = urljoin(self._client.base_url, "auth/whatsapp/register")
        base_headers = self._prepare_headers(extra_headers)
        base_headers["Content-Type"] = CONTENT_TYPE_JSON

        # Prepare request body
        data = {
            "whatsapp_id": whatsapp_id,
            "email": email,
        }
        if profile_name is not None:
            data["profile_name"] = profile_name

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)
        logger.debug(REQUEST_DATA_LOG, data)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=base_headers, json=data)
            response.raise_for_status()
            return response.json()
