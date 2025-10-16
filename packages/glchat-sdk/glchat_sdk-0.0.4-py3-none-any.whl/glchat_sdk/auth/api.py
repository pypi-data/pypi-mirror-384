"""Authentication API classes for the GLChat Python client.

This module provides the AuthAPI class for handling authentication operations
with the GLChat backend, including WhatsApp user registration and other auth-related features.

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import logging

from .whatsapp import WhatsAppAPI

logger = logging.getLogger(__name__)

# Constants
REQUEST_URL_LOG = "Request URL: %s"
REQUEST_HEADERS_LOG = "Request headers: %s"
REQUEST_DATA_LOG = "Request data: %s"
CONTENT_TYPE_JSON = "application/json"


class AuthAPI:
    """Handles authentication API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client
        self.whatsapp = WhatsAppAPI(client)

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
