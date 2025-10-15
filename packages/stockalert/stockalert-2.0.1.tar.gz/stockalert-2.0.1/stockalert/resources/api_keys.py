"""API Keys resource for StockAlert SDK."""
from ..types import ApiResponse
from .base import BaseResource


class ApiKeysResource(BaseResource):
    """Manage API keys"""

    def list(self) -> ApiResponse:
        """
        List all API keys

        Returns:
            List of API keys
        """
        return self._request("GET", "/api-keys")

    def create(self, name: str) -> ApiResponse:
        """
        Create a new API key

        Args:
            name: Name for the API key

        Returns:
            Created API key (includes full key - save it!)
        """
        data = {"name": name}
        return self._request("POST", "/api-keys", json_data=data)

    def delete(self, key_id: str) -> ApiResponse:
        """
        Delete an API key

        Args:
            key_id: API key ID

        Returns:
            Success message
        """
        return self._request("DELETE", f"/api-keys?id={key_id}")
