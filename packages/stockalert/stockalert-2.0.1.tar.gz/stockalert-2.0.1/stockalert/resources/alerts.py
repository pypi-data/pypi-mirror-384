"""Alerts resource for StockAlert SDK."""
from typing import Any, Dict, Generator, Optional

from ..exceptions import ValidationError
from ..types import Alert
from .alerts_base import AlertsResourceBase


class AlertsResource(AlertsResourceBase):
    """Alerts resource."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def list(self, **params: Any) -> Dict[str, Any]:
        """
        List alerts with optional filtering.

        Returns full response including data and meta with pagination info.
        """
        # Normalize symbol to uppercase
        if "symbol" in params:
            params["symbol"] = str(params["symbol"]).upper()

        response = self.client._request("GET", "/alerts", params=params, return_full_response=True)
        return response  # type: ignore[no-any-return]

    def create(self, **data: Any) -> Alert:
        """Create a new alert."""
        # Default to email notification
        if "notification" not in data:
            data["notification"] = "email"

        self._validate_create_request(data)
        response = self.client._request("POST", "/alerts", json=data)
        return Alert(response)

    def get(self, alert_id: str) -> Alert:
        """Get alert by ID."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        response = self.client._request("GET", f"/alerts/{alert_id}")
        return Alert(response)

    def update(
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

        response = self.client._request("PUT", f"/alerts/{alert_id}", json=update_data)
        return Alert(response)

    def pause(self, alert_id: str) -> Dict[str, Any]:
        """
        Pause an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Dictionary with alertId and status
        """
        if not alert_id:
            raise ValidationError("Alert ID is required")

        return self.client._request("POST", f"/alerts/{alert_id}/pause")

    def activate(self, alert_id: str) -> Dict[str, Any]:
        """
        Activate/reactivate an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Dictionary with alertId and status
        """
        if not alert_id:
            raise ValidationError("Alert ID is required")

        return self.client._request("POST", f"/alerts/{alert_id}/activate")

    def delete(self, alert_id: str) -> Dict[str, Any]:
        """Delete an alert."""
        if not alert_id:
            raise ValidationError("Alert ID is required")

        return self.client._request("DELETE", f"/alerts/{alert_id}")

    def history(self, alert_id: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Get alert history.

        Args:
            alert_id: Alert ID
            page: Page number (default: 1)
            limit: Items per page (default: 50, max: 200)

        Returns full response including data and meta with pagination info.
        """
        if not alert_id:
            raise ValidationError("Alert ID is required")

        params = {"page": page, "limit": limit}
        return self.client._request(
            "GET",
            f"/alerts/{alert_id}/history",
            params=params,
            return_full_response=True
        )

    def stats(self) -> Dict[str, Any]:
        """
        Get alert statistics.

        Returns full response with data containing statusCounts and total.
        """
        return self.client._request("GET", "/alerts/stats", return_full_response=True)

    def verify(self, token: str) -> Alert:
        """
        Verify alert via token (for guest alerts).

        Args:
            token: Verification token
        """
        if not token:
            raise ValidationError("Token is required")

        response = self.client._request("POST", "/alerts/verify", json={"token": token})
        return Alert(response)

    def iterate(self, **params: Any) -> Generator[Alert, None, None]:
        """Iterate through all alerts with automatic pagination."""
        page = params.get("page", 1)
        limit = min(params.get("limit", 50), 100)

        # Remove pagination params from base params
        base_params = {k: v for k, v in params.items() if k not in ["limit", "page"]}

        while True:
            result = self.list(**base_params, limit=limit, page=page)

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
