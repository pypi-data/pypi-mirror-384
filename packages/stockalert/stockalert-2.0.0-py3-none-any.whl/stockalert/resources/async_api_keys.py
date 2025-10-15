"""Async API keys resource."""
from typing import Any, Dict, Optional

from ..resources.api_keys import ApiKeysResource


class AsyncApiKeysResource(ApiKeysResource):
    """Async version of API keys resource."""

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.client: Optional[Any] = None  # Set by AsyncStockAlert
