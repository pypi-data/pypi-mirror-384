"""Chatbot handling for the GLChat Python client.

This module provides the ChatbotAPI class for handling chatbot operations
with the GLChat backend, including getting chatbots with optional user filtering.

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import logging
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx

logger = logging.getLogger(__name__)


class ChatbotsAPI:
    """Handles chatbots API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client

    def _prepare_headers(
        self, extra_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Prepare headers for the API request.

        Args:
            extra_headers (dict[str, str] | None): Additional headers to merge with default headers

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
        self, user_id: str | None = None, extra_headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Get chatbots from the GLChat API.

        Args:
            user_id (str | None): Optional user identifier to filter chatbots
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            dict[str, Any]: Dictionary containing the chatbots response data

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Getting chatbots with user_id: %s", user_id)

        # Prepare request components
        base_url = urljoin(self._client.base_url, "chatbots")

        # Build query parameters
        params = {}
        if user_id is not None:
            params["user_id"] = user_id

        # Construct URL with query parameters
        if params:
            url = f"{base_url}?{urlencode(params)}"
        else:
            url = base_url

        base_headers = self._prepare_headers(extra_headers)

        # Make the request
        timeout = httpx.Timeout(self._client.timeout)

        # Log the request details for debugging
        logger.debug("Request URL: %s", url)
        logger.debug("Request headers: %s", base_headers)

        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=base_headers)
            response.raise_for_status()
            return response.json()
