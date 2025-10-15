"""Async client for StockAlert SDK."""
from typing import Any, Optional, cast

# Import httpx at runtime to make it optional
try:
    import httpx
except ImportError as e:
    raise ImportError(
        "The async client requires httpx. "
        "Install it with: pip install stockalert[async]"
    ) from e

from .exceptions import APIError, AuthenticationError
from .resources.async_alerts import AsyncAlertsResource
from .resources.async_api_keys import AsyncApiKeysResource
from .resources.async_webhooks import AsyncWebhooksResource

DEFAULT_BASE_URL = "https://stockalert.pro/api/v1"
DEFAULT_TIMEOUT = 30


class AsyncStockAlert:
    """
    Async StockAlert.pro API Client

    Example:
        >>> async with AsyncStockAlert(api_key="sk_your_api_key") as client:
        ...     alerts = await client.alerts.list()
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ):
        if not api_key:
            raise AuthenticationError("API key is required")

        self._config = {
            "api_key": api_key,
            "base_url": base_url or DEFAULT_BASE_URL,
            "timeout": timeout or DEFAULT_TIMEOUT,
            "max_retries": max_retries,
        }

        self._client: Optional[httpx.AsyncClient] = None

        # Initialize resources
        self.alerts = AsyncAlertsResource(self._config)
        self.webhooks = AsyncWebhooksResource(self._config)
        self.api_keys = AsyncApiKeysResource(self._config)

    async def __aenter__(self) -> "AsyncStockAlert":
        # Cast config values to proper types
        base_url = cast(str, self._config["base_url"])
        timeout = cast(float, self._config["timeout"])
        api_key = cast(str, self._config["api_key"])

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "User-Agent": "stockalert-python/1.0.0",
                "Content-Type": "application/json",
            },
        )

        # Set client reference for resources
        self.alerts.client = self
        self.webhooks.client = self
        self.api_keys.client = self

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError(
                "Client not initialized. "
                "Use: async with AsyncStockAlert(...) as client:"
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        params: Any = None,
        json: Any = None,
        return_full_response: bool = False,
    ) -> Any:
        """Make an HTTP request to the API."""
        response = await self.client.request(method, path, params=params, json=json)

        # Parse response
        try:
            result = response.json()
        except Exception as e:
            raise APIError(f"Invalid JSON response: {response.text}", response.status_code) from e

        # Handle errors
        if response.status_code == 401:
            error_data = result.get("error", {})
            if isinstance(error_data, dict):
                error_msg = error_data.get("message", "Authentication failed")
            else:
                error_msg = str(error_data) if error_data else "Authentication failed"
            raise AuthenticationError(error_msg)

        if not response.is_success:
            error_data = result.get("error", {})
            if isinstance(error_data, dict):
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
            else:
                error_msg = str(error_data) if error_data else f"HTTP {response.status_code}"
            raise APIError(error_msg, response.status_code, result)

        # Check success field (v1 API format)
        if not result.get("success", True):
            error_data = result.get("error", {})
            if isinstance(error_data, dict):
                error_msg = error_data.get("message", "Request failed")
            else:
                error_msg = str(error_data) if error_data else "Request failed"
            raise APIError(error_msg, response.status_code, result)

        # Return full response if requested (for list/history/stats with meta)
        if return_full_response:
            return result

        # Return data field for v1 envelope format
        if "data" in result:
            return result["data"]
        return result
