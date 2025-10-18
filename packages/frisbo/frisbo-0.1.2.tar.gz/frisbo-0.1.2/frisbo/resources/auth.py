"""Authentication resource."""

from typing import Dict
import logging
from .base import BaseResource
from ..models import Authorization, User

logger = logging.getLogger(__name__)


class AuthResource(BaseResource):
    """Handle authentication operations."""

    def login(self, email: str, password: str) -> Authorization:
        """Login and generate access token.

        Args:
            email: User email
            password: User password

        Returns:
            Authorization object with access token

        Example:
            >>> auth = client.auth.login("user@example.com", "password")
            >>> print(auth.access_token)
        """
        logger.debug(f"Attempting login for email: {email}")
        response = self._post(
            "/v1/auth/login",
            json={"email": email, "password": password}
        )
        auth_data = Authorization(**response.json())
        logger.debug(f"Login successful, token type: {auth_data.token_type}")
        return auth_data

    def logout(self) -> None:
        """Logout and invalidate current session.

        Example:
            >>> client.auth.logout()
        """
        logger.debug("Logging out and invalidating session")
        self._get("/v1/auth/logout")
        logger.debug("Logout API call completed")

    def me(self) -> User:
        """Get current user data.

        Returns:
            Current user information

        Example:
            >>> user = client.auth.me()
            >>> print(user.email)
        """
        logger.debug("Fetching current user information")
        response = self._get("/v1/me")
        user = User(**response.json())
        logger.debug(f"Retrieved user info: {user.email}")
        return user
