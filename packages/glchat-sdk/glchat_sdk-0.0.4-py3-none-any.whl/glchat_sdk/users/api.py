"""User API classes for the GLChat Python client.

This module provides the UsersAPI class for handling user-related operations
with the GLChat backend, including verification and other user management features.

Authors:
    Vincent Chuardi (vincent.chuardi@gdplabs.id)

References:
    None
"""

from .verification import UsersVerificationAPI


class UsersAPI:
    """Handles user API operations for the GLChat API."""

    def __init__(self, client):
        self._client = client
        self.verification = UsersVerificationAPI(client)
