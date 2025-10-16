"""Main Frisbo API client."""

from typing import Optional
import requests
from datetime import datetime, timedelta

from .exceptions import AuthenticationError
from .resources.auth import AuthResource
from .resources.organizations import OrganizationsResource
from .resources.products import ProductsResource
from .resources.orders import OrdersResource
from .resources.invoices import InvoicesResource
from .resources.inbound import InboundResource


class FrisboClient:
    """Main client for interacting with the Frisbo API.

    Example:
        >>> client = FrisboClient(email="user@example.com", password="secret")
        >>> # List organizations
        >>> for org in client.organizations.list():
        ...     print(org)
        >>> # Get orders for an organization
        >>> for order in client.orders.list(organization_id=921):
        ...     print(order)
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://api.frisbo.ro",
        auto_authenticate: bool = True
    ):
        """Initialize the Frisbo client.

        Args:
            email: User email for authentication
            password: User password for authentication
            access_token: Pre-existing access token (optional)
            base_url: Base URL for the API
            auto_authenticate: Automatically authenticate on initialization
        """
        self.email = email
        self.password = password
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.token_expires_at: Optional[datetime] = None

        # Initialize resources
        self.auth = AuthResource(self)
        self.organizations = OrganizationsResource(self)
        self.products = ProductsResource(self)
        self.orders = OrdersResource(self)
        self.invoices = InvoicesResource(self)
        self.inbound = InboundResource(self)

        # Auto-authenticate if credentials provided
        if auto_authenticate and email and password and not access_token:
            self.authenticate()

    def authenticate(self) -> str:
        """Authenticate with the API and store the access token.

        Returns:
            Access token

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.email or not self.password:
            raise AuthenticationError("Email and password are required for authentication")

        try:
            auth_response = self.auth.login(self.email, self.password)
            self.access_token = auth_response.access_token

            # Calculate token expiry
            if auth_response.expires_in:
                self.token_expires_at = datetime.now() + timedelta(seconds=auth_response.expires_in)

            return self.access_token
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if the client has a valid access token.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.access_token:
            return False

        # Check if token is expired
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            return False

        return True

    def ensure_authenticated(self) -> None:
        """Ensure the client is authenticated, re-authenticate if needed."""
        if not self.is_authenticated():
            if self.email and self.password:
                self.authenticate()
            else:
                raise AuthenticationError("Not authenticated and no credentials available")

    def logout(self) -> None:
        """Logout and invalidate the current session."""
        if self.access_token:
            try:
                self.auth.logout()
            finally:
                self.access_token = None
                self.token_expires_at = None
