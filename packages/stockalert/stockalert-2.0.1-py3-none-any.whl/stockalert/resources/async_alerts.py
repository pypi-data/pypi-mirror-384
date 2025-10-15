"""Async alerts resource."""
from typing import Any, AsyncGenerator, Dict, Optional

from ..exceptions import ValidationError
from ..types import Alert
from .alerts_base import AlertsResourceBase


class AsyncAlertsResource(AlertsResourceBase):
    """Async alerts resource."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self.client: Any = None  # Set by AsyncStockAlert

    async def list(self, **params: Any) -> Dict[str, Any]:
        """
        List alerts with optional filtering.

        Returns full response including data and meta with pagination info.
        """
        if "symbol" in params:
            params["symbol"] = str(params["symbol"]).upper()

        response = await self.client._request("GET", "/api/v1/alerts", params=params, return_full_response=True)
        return response  # type: ignore[no-any-return]

    async def create(self, **data: Any) -> Alert:
        """Create a new alert."""
        if "notification" not in data:
            data["notification"] = "email"

        self._validate_create_request(data)
        response = await self.client._request("POST", "/api/v1/alerts", json=data)
        return Alert(response)

    async def get(self, alert_id: str) -> Alert:
        """Get alert by ID."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        response = await self.client._request("GET", f"/api/v1/alerts/{alert_id}")
        return Alert(response)

    async def update(
        self,
        alert_id: str,
        condition: Optional[str] = None,
        threshold: Optional[float] = None,
        notification: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Update alert (partial update).

        Args:
            alert_id: Alert ID
            condition: New alert condition
            threshold: New threshold value
            notification: New notification channel (email, sms)
            parameters: Additional parameters
        """
        if not alert_id:
            raise ValidationError("Alert ID is required")

        update_data: Dict[str, Any] = {}
        if condition is not None:
            update_data["condition"] = condition
        if threshold is not None:
            update_data["threshold"] = threshold
        if notification is not None:
            update_data["notification"] = notification
        if parameters is not None:
            update_data["parameters"] = parameters

        if not update_data:
            raise ValidationError("At least one field must be provided for update")

        response = await self.client._request("PUT", f"/api/v1/alerts/{alert_id}", json=update_data)
        return Alert(response)

    async def pause(self, alert_id: str) -> Alert:
        """Pause an alert."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        response = await self.client._request("POST", f"/api/v1/alerts/{alert_id}/pause")
        return Alert(response)

    async def activate(self, alert_id: str) -> Alert:
        """Activate/reactivate an alert."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        response = await self.client._request("POST", f"/api/v1/alerts/{alert_id}/activate")
        return Alert(response)

    async def delete(self, alert_id: str) -> Dict[str, Any]:
        """Delete an alert."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        return await self.client._request("DELETE", f"/api/v1/alerts/{alert_id}")

    async def history(self, alert_id: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get alert history.

        Returns full response including data and meta with pagination info.
        """
        if not alert_id:
            raise ValidationError("Alert ID is required")

        params = {"page": page, "limit": limit}
        return await self.client._request(
            "GET",
            f"/api/v1/alerts/{alert_id}/history",
            params=params,
            return_full_response=True
        )

    async def stats(self) -> Dict[str, Any]:
        """
        Get alert statistics.

        Returns full response with data containing statusCounts and total.
        """
        return await self.client._request("GET", "/api/v1/alerts/stats", return_full_response=True)

    async def verify(self, token: str) -> Alert:
        """Verify alert via token (for guest alerts)."""
        if not token:
            raise ValidationError("Token is required")

        response = await self.client._request("POST", "/api/v1/alerts/verify", json={"token": token})
        return Alert(response)

    async def iterate(self, **params: Any) -> AsyncGenerator[Alert, None]:
        """Iterate through all alerts with automatic pagination."""
        page = params.get("page", 1)
        limit = min(params.get("limit", 50), 100)

        base_params = {k: v for k, v in params.items() if k not in ["limit", "page"]}

        while True:
            result = await self.list(**base_params, limit=limit, page=page)

            if "data" in result:
                for alert_data in result["data"]:
                    yield Alert(alert_data)

                # Check if we have more pages
                meta = result.get("meta", {})
                pagination = meta.get("pagination", {})
                if page >= pagination.get("totalPages", 1):
                    break
            else:
                break

            page += 1
