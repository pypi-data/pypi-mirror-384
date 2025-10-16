"""GLChat Python client library for interacting with the GLChat Backend API.

This library provides a simple interface to interact with the GLChat backend,
supporting message sending and file uploads with streaming responses.

Example:
    >>> client = GLChat(api_key="your-api-key")
    >>> for chunk in client.message.create(
    ...     application_id="your-application-id",
    ...     message="Hello!",
    ...     parent_id="msg_123",
    ...     user_id="user_456"
    ... ):
    ...     print(chunk.decode("utf-8"), end="")

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import os

from glchat_sdk.auth import AuthAPI
from glchat_sdk.chatbots import ChatbotsAPI
from glchat_sdk.conversation import ConversationAPI
from glchat_sdk.message import MessageAPI
from glchat_sdk.users import UsersAPI

# Ensure the URL ends with a slash; without the trailing slash, the base path will be incorrect.
DEFAULT_BASE_URL = "https://chat.gdplabs.id/api/proxy/"


class GLChat:
    """GLChat Backend API Client.

    Attributes:
        api_key (str): API key for authentication
        base_url (str): Base URL for the GLChat API
        timeout (float): Request timeout in seconds
        default_headers (dict[str, str]): Default headers to include in all requests
        message (MessageAPI): MessageAPI instance for message operations
        conversation (ConversationAPI): ConversationAPI instance for conversation operations
        chatbots (ChatbotsAPI): ChatbotsAPI instance for chatbot operations
        users (UsersAPI): UsersAPI instance for user operations
        auth (AuthAPI): AuthAPI instance for authentication operations
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        default_headers: dict[str, str] | None = None,
    ):
        """
        Initialize GLChat client

        Args:
            api_key (str | None): API key for authentication. If not provided,
                will try to get from GLCHAT_API_KEY environment variable
            base_url (str | None): Base URL for the GLChat API. If not provided,
                will try to get from GLCHAT_BASE_URL environment variable,
                otherwise uses default
            timeout (float): Request timeout in seconds
            default_headers (dict[str, str] | None): Default headers to include in all requests.
                These will be merged with any extra_headers provided to individual methods.
        """
        self.api_key = api_key or os.getenv("GLCHAT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it via 'api_key' parameter or "
                "'GLCHAT_API_KEY' environment variable."
            )

        self.base_url = base_url or os.getenv("GLCHAT_BASE_URL") or DEFAULT_BASE_URL
        self.timeout = timeout
        self.default_headers = default_headers or {}
        self.message = MessageAPI(self)
        self.conversation = ConversationAPI(self)
        self.chatbots = ChatbotsAPI(self)
        self.users = UsersAPI(self)
        self.auth = AuthAPI(self)
