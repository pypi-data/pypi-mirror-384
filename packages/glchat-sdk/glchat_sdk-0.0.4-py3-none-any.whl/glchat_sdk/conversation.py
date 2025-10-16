"""Conversation handling for the GLChat Python client.

This module provides the ConversationAPI class for handling conversation operations
with the GLChat backend, including creating new conversations.

Authors:
    Hermes Vincentius Gani (hermes.v.gani@gdplabs.id)

References:
    None
"""

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from glchat_sdk.models import ConversationRequest

logger = logging.getLogger(__name__)


class ConversationAPI:
    """Handles conversation API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client

    def _validate_inputs(self, user_id: str, chatbot_id: str) -> None:
        """Validate input parameters.

        Args:
            user_id (str): User identifier
            chatbot_id (str): Chatbot identifier

        Raises:
            ValueError: If user_id or chatbot_id is empty
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not chatbot_id:
            raise ValueError("chatbot_id cannot be empty")

    def _prepare_request_data(
        self,
        user_id: str,
        chatbot_id: str,
        title: str | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """Prepare request data for the API call.

        Args:
            user_id (str): Required user identifier
            chatbot_id (str): Required chatbot identifier
            title (str | None): Optional conversation title
            model_name (str | None): Optional model name to use

        Returns:
            dict[str, Any]: Dictionary containing the prepared request data
        """
        request = ConversationRequest(
            user_id=user_id,
            chatbot_id=chatbot_id,
            title=title,
            model_name=model_name,
        )
        return request.model_dump(exclude_none=True)

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

    def create(
        self,
        user_id: str,
        application_id: str | None = None,
        chatbot_id: str | None = None,
        title: str | None = None,
        model_name: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new conversation with the GLChat API.

        Args:
            user_id (str): Required user identifier
            application_id (str | None): Application identifier
            chatbot_id (str | None): (DEPRECATED) Use application_id instead
            title (str | None): Optional conversation title
            model_name (str | None): Optional model name to use
            extra_headers (dict[str, str] | None): Additional headers to include in the request
        Returns:
            dict[str, Any]: Dictionary containing the conversation response data

        Raises:
            ValueError: If input validation fails or if both chatbot_id and
                application_id are provided
            httpx.HTTPStatusError: If the API request fails
        """
        # Validate that the provided parameters are not empty strings first
        if chatbot_id == "":
            raise ValueError("chatbot_id cannot be empty")
        if application_id == "":
            raise ValueError("application_id cannot be empty")

        # Validate that exactly one of application_id or chatbot_id is provided
        if chatbot_id and application_id:
            raise ValueError("Cannot provide both application_id and chatbot_id")
        if not chatbot_id and not application_id:
            raise ValueError("Must provide either application_id or chatbot_id")

        # Use chatbot_id for backward compatibility (application_id is treated as chatbot_id)
        actual_chatbot_id = chatbot_id or application_id

        # Validate inputs
        self._validate_inputs(user_id, actual_chatbot_id)

        logger.debug(
            "Creating conversation for user %s with application %s",
            user_id,
            actual_chatbot_id,
        )

        # Prepare request components
        url = urljoin(self._client.base_url, "conversations")
        data = self._prepare_request_data(
            user_id=user_id,
            chatbot_id=actual_chatbot_id,
            title=title,
            model_name=model_name,
        )
        headers = self._prepare_headers()
        if extra_headers:
            headers.update(extra_headers)

        # Make the request
        timeout = httpx.Timeout(self._client.timeout)

        # Log the request details for debugging
        logger.debug("Request URL: %s", url)
        logger.debug("Request data: %s", data)
        logger.debug("Request headers: %s", headers)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
