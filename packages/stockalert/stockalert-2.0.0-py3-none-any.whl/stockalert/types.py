"""Type definitions for StockAlert SDK."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

AlertCondition = Literal[
    "price_above",
    "price_below",
    "price_change_up",
    "price_change_down",
    "new_high",
    "new_low",
    "reminder",
    "daily_reminder",
    "ma_crossover_golden",
    "ma_crossover_death",
    "ma_touch_above",
    "ma_touch_below",
    "volume_change",
    "rsi_limit",
    "pe_ratio_below",
    "pe_ratio_above",
    "forward_pe_below",
    "forward_pe_above",
    "earnings_announcement",
    "dividend_ex_date",
    "dividend_payment"
]

# Notification channels - NO WhatsApp!
NotificationChannel = Literal["email", "sms"]

# Alert status
AlertStatus = Literal["active", "paused", "triggered"]

class Alert:
    """Alert object."""
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.symbol: str = data["symbol"]
        self.condition: AlertCondition = data["condition"]
        self.threshold: Optional[float] = data.get("threshold")
        self.notification: NotificationChannel = data["notification"]
        self.status: AlertStatus = data["status"]
        self.created_at: datetime = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))

        # triggered_at instead of updated_at (v1 API change)
        self.triggered_at: Optional[datetime] = None
        if data.get("triggered_at"):
            self.triggered_at = datetime.fromisoformat(data["triggered_at"].replace('Z', '+00:00'))

        # Keep backward compatibility
        self.updated_at: datetime = self.triggered_at or self.created_at
        self.last_triggered: Optional[datetime] = self.triggered_at

        self.initial_price: Optional[float] = data.get("initial_price")
        self.parameters: Optional[Dict[str, Any]] = data.get("parameters")

        # New fields from v1 API
        self.user_id: Optional[str] = data.get("user_id")
        self.email: Optional[str] = data.get("email")
        self.verified: Optional[bool] = data.get("verified")
        self.verification_token: Optional[str] = data.get("verification_token")
        self.last_evaluated_at: Optional[datetime] = None
        if data.get("last_evaluated_at"):
            self.last_evaluated_at = datetime.fromisoformat(data["last_evaluated_at"].replace('Z', '+00:00'))
        self.last_metric_value: Optional[float] = data.get("last_metric_value")
        self.stock: Optional[Dict[str, Any]] = data.get("stock")

        self._raw_data = data

    def __repr__(self) -> str:
        return f"<Alert {self.id}: {self.symbol} {self.condition}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._raw_data

class PaginatedResponse:
    """Paginated response for v1 API."""
    def __init__(self, data: List[Dict[str, Any]], meta: Dict[str, Any]):
        self.data = data
        self.meta = meta

        # v1 API pagination structure: meta.pagination
        pagination = meta.get("pagination", {})
        self.page = pagination.get("page", 1)
        self.limit = pagination.get("limit", 50)
        self.total = pagination.get("total", 0)
        self.total_pages = pagination.get("totalPages", 0)

        # Backward compatibility
        self.offset = (self.page - 1) * self.limit
        self.has_more = self.page < self.total_pages

        # Rate limit info from meta
        self.rate_limit = meta.get("rateLimit", {})

class WebhookPayload:
    """Webhook payload."""
    def __init__(self, data: Dict[str, Any]):
        self.event: str = data["event"]
        self.timestamp: datetime = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        self.data: Dict[str, Any] = data["data"]
        self._raw_data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._raw_data

# API Response types
ApiResponse = Dict[str, Any]
