"""Async webhooks resource."""
from typing import Any, Dict, Optional

from ..resources.webhooks import WebhooksResource


class AsyncWebhooksResource(WebhooksResource):
    """Async version of webhooks resource."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.client: Optional[Any] = None  # Set by AsyncStockAlert
