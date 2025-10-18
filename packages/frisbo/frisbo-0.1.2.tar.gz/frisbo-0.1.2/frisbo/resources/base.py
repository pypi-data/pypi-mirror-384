"""Base resource class for Frisbo SDK."""

from typing import TYPE_CHECKING, Iterator, Any, Optional, Dict
import logging
import time
import requests
from ..exceptions import APIError, NotFoundError, RateLimitError

if TYPE_CHECKING:
    from ..client import FrisboClient

logger = logging.getLogger(__name__)


class BaseResource:
    """Base class for all API resources."""

    def __init__(self, client: "FrisboClient"):
        self.client = client
        self.base_url = client.base_url

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            json: JSON data for request body
            params: Query parameters
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            APIError: If the API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})

        # Add authentication if token exists
        if self.client.access_token:
            headers["Authorization"] = f"Bearer {self.client.access_token}"

        headers["Content-Type"] = "application/json"

        # Log request
        logger.debug(
            f"API Request: {method} {url}",
            extra={
                "method": method,
                "url": url,
                "params": params,
                "has_json": json is not None,
                "proxy": self.client.proxies.get('https') if self.client.proxies else None
            }
        )

        start_time = time.time()

        response = requests.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=headers,
            proxies=self.client.proxies,
            **kwargs
        )

        elapsed = time.time() - start_time

        # Log response
        logger.info(
            f"API Response: {method} {endpoint} - {response.status_code} ({elapsed:.2f}s)",
            extra={
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "elapsed": elapsed
            }
        )

        # Handle errors
        if response.status_code >= 400:
            self._handle_error(response)

        return response

    def _handle_error(self, response: requests.Response) -> None:
        """Handle API errors.

        Args:
            response: Response object with error

        Raises:
            NotFoundError: For 404 responses
            RateLimitError: For 429 responses
            APIError: For other error responses
        """
        status_code = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("error_description") or error_data.get("message") or str(error_data)
        except Exception:
            message = response.text or f"HTTP {status_code}"

        # Log error
        logger.error(
            f"API Error: {status_code} - {message}",
            extra={
                "status_code": status_code,
                "error_message": message,
                "url": response.url
            }
        )

        if status_code == 404:
            raise NotFoundError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 429:
            logger.warning(f"Rate limit exceeded: {message}")
            raise RateLimitError(message, status_code, error_data if 'error_data' in locals() else None)
        else:
            raise APIError(message, status_code, error_data if 'error_data' in locals() else None)

    def _get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def _post(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a POST request."""
        return self._request("POST", endpoint, json=json, **kwargs)

    def _put(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make a PUT request."""
        return self._request("PUT", endpoint, json=json, **kwargs)

    def _delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page: int = 1
    ) -> Iterator[Any]:
        """Paginate through API results.

        Args:
            endpoint: API endpoint
            params: Query parameters
            page: Starting page number

        Yields:
            Individual items from paginated results
        """
        params = params or {}
        params["page"] = page

        response = self._get(endpoint, params=params)
        data = response.json()

        # Log pagination info
        current_page = data.get("current_page", page)
        last_page = data.get("last_page", page)
        per_page = data.get("per_page", 0)
        total = data.get("total", 0)

        logger.debug(
            f"Paginating {endpoint}: page {current_page}/{last_page} ({per_page} items/page, {total} total)",
            extra={
                "endpoint": endpoint,
                "current_page": current_page,
                "last_page": last_page,
                "per_page": per_page,
                "total": total
            }
        )

        # Yield items from current page
        for item in data.get("data", []):
            yield item

        # Recurse if there are more pages
        if current_page < last_page:
            yield from self._paginate(endpoint, params, page + 1)
