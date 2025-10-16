"""Data models for the GLChat Python client.

This module contains Pydantic models for request and response data structures
used in the GLChat Python client library.

Example:
    >>> request = MessageRequest(
    ...     application_id="your-application-id",
    ...     message="Hello!",
    ...     user_id="user_123"
    ... )
    >>> data = request.model_dump()

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

import warnings

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MessageRequest(BaseModel):
    """Request model for sending messages to the GLChat API."""

    # Disable pydantic's protected namespace "model_"
    model_config = ConfigDict(protected_namespaces=())

    application_id: str | None = None
    chatbot_id: str | None = Field(
        None,
        description="""
            (DEPRECATED) Use application_id instead.
            This parameter will be removed in a future version.
        """,
    )
    message: str
    parent_id: str | None = None
    source: str | None = None
    quote: str | None = None
    user_id: str | None = None
    conversation_id: str | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None
    chat_history: str | None = None
    stream_id: str | None = None
    metadata: str | None = None
    model_name: str | None = None
    anonymize_em: bool | None = None
    anonymize_lm: bool | None = None
    use_cache: bool | None = None
    search_type: str | None = None
    agent_ids: list[str] | None = None

    @model_validator(mode="after")
    def validate_chatbot_id_deprecation(self) -> "MessageRequest":
        """Validate and warn about deprecated chatbot_id parameter."""
        if self.chatbot_id is not None:
            warnings.warn(
                "The 'chatbot_id' parameter is deprecated and will be removed in a future version. "
                "Use 'application_id' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self


class ConversationRequest(BaseModel):
    """Request model for creating conversations with the GLChat API."""

    # Disable pydantic's protected namespace "model_"
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    application_id: str | None = None
    chatbot_id: str | None = Field(
        None,
        description="""
            (DEPRECATED) Use application_id instead.
            This parameter will be removed in a future version.
        """,
    )
    title: str | None = None
    model_name: str | None = None

    @model_validator(mode="after")
    def validate_chatbot_id_deprecation(self) -> "ConversationRequest":
        """Validate and warn about deprecated chatbot_id parameter."""
        if self.chatbot_id is not None:
            warnings.warn(
                "The 'chatbot_id' parameter is deprecated and will be removed in a future version. "
                "Use 'application_id' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self
