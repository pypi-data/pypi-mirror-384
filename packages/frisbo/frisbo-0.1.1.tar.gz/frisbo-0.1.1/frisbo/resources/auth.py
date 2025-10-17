"""Authentication resource."""

from typing import Dict
from .base import BaseResource
from ..models import Authorization, User


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
        response = self._post(
            "/v1/auth/login",
            json={"email": email, "password": password}
        )
        return Authorization(**response.json())

    def logout(self) -> None:
        """Logout and invalidate current session.

        Example:
            >>> client.auth.logout()
        """
        self._get("/v1/auth/logout")

    def me(self) -> User:
        """Get current user data.

        Returns:
            Current user information

        Example:
            >>> user = client.auth.me()
            >>> print(user.email)
        """
        response = self._get("/v1/me")
        return User(**response.json())
