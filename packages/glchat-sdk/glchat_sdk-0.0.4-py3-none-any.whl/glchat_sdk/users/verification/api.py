"""User verification API classes for the GLChat Python client.

This module provides the UsersVerificationAPI class for handling verification operations
with the GLChat backend, including phone number verification, OTP handling, and
challenge management.

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from .username import UsernameAPI

logger = logging.getLogger(__name__)

# Constants
REQUEST_URL_LOG = "Request URL: %s"
REQUEST_HEADERS_LOG = "Request headers: %s"
REQUEST_DATA_LOG = "Request data: %s"
CONTENT_TYPE_JSON = "application/json"


class UsersVerificationAPI:
    """Handles users verification API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client
        self.username = UsernameAPI(client)

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

    def resend(
        self,
        challenge_id: str,
        channel: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Resend verification code.

        Args:
            challenge_id (str): Challenge ID
            channel (str): Verification channel ("SMS", "WHATSAPP", or "EMAIL")
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            dict[str, Any]: Dictionary containing the resend verification response data

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug(
            "Resending verification for challenge_id: %s, channel: %s",
            challenge_id,
            channel,
        )

        # Prepare request components
        url = urljoin(
            self._client.base_url, f"users/verification/{challenge_id}/resend"
        )
        base_headers = self._prepare_headers()
        base_headers["Content-Type"] = CONTENT_TYPE_JSON
        if extra_headers:
            base_headers.update(extra_headers)

        # Prepare request body
        data = {"channel": channel}

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)
        logger.debug(REQUEST_DATA_LOG, data)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=base_headers, json=data)
            response.raise_for_status()
            return response.json()

    def cancel(
        self, challenge_id: str, extra_headers: dict[str, str] | None = None
    ) -> None:
        """
        Cancel verification challenge.

        Args:
            challenge_id (str): Challenge ID
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            None: No return value

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Canceling verification for challenge_id: %s", challenge_id)

        # Prepare request components
        url = urljoin(
            self._client.base_url, f"users/verification/{challenge_id}/cancel"
        )
        base_headers = self._prepare_headers()
        if extra_headers:
            base_headers.update(extra_headers)

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=base_headers)
            response.raise_for_status()

    def verify_and_bind(
        self, challenge_id: str, code: str, extra_headers: dict[str, str] | None = None
    ) -> None:
        """
        Verify OTP code and bind phone or email to user.

        Args:
            challenge_id (str): Challenge ID
            code (str): OTP code to verify
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            None: No return value

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug("Verifying and binding for challenge_id: %s", challenge_id)

        # Prepare request components
        url = urljoin(
            self._client.base_url, f"users/verification/{challenge_id}/verify-and-bind"
        )
        base_headers = self._prepare_headers()
        base_headers["Content-Type"] = CONTENT_TYPE_JSON
        if extra_headers:
            base_headers.update(extra_headers)

        # Prepare request body
        data = {"code": code}

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)
        logger.debug(REQUEST_DATA_LOG, data)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=base_headers, json=data)
            response.raise_for_status()

    def request_verification(
        self,
        username: str,
        contact: str,
        channel: str,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Request phone number or email verification.

        Args:
            username (str): Username to bind with phone number
            contact (str): Phone number in international format or email address
            channel (str): Verification channel ("SMS", "WHATSAPP", or "EMAIL")
            extra_headers (dict[str, str] | None): Additional headers to include in the request

        Returns:
            dict[str, Any]: Dictionary containing the request verification response data

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        logger.debug(
            "Requesting verification for username: %s, contact: %s, channel: %s",
            username,
            contact,
            channel,
        )

        # Prepare request components
        url = urljoin(self._client.base_url, "users/verification/request-verification")
        base_headers = self._prepare_headers()
        base_headers["Content-Type"] = CONTENT_TYPE_JSON
        if extra_headers:
            base_headers.update(extra_headers)

        # Prepare request body
        data = {"username": username, "contact": contact, "channel": channel}

        # Log the request details for debugging
        logger.debug(REQUEST_URL_LOG, url)
        logger.debug(REQUEST_HEADERS_LOG, base_headers)
        logger.debug(REQUEST_DATA_LOG, data)

        timeout = httpx.Timeout(self._client.timeout)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=base_headers, json=data)
            response.raise_for_status()
            return response.json()
