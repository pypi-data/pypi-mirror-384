"""Base alerts resource with shared logic."""
from typing import Any, Dict

from ..exceptions import ValidationError


class AlertsResourceBase:
    """Base class with shared validation logic."""

    def _validate_create_request(self, data: Dict[str, Any]) -> None:
        """Validate create alert request."""
        # Basic validation
        if not data.get("symbol"):
            raise ValidationError("Symbol is required")

        if not data.get("condition"):
            raise ValidationError("Condition is required")

        # Validate symbol format
        symbol = str(data["symbol"]).strip().upper()
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            raise ValidationError("Symbol must be 1-5 uppercase letters")

        # Normalize symbol
        data["symbol"] = symbol

        # Validate notification channel
        if "notification" in data:
            valid_channels = ["email", "sms"]
            if data["notification"] not in valid_channels:
                raise ValidationError(f"Notification must be one of: {', '.join(valid_channels)}")

        # Validate condition-specific requirements
        self._validate_condition_requirements(data)

    def _validate_condition_requirements(self, data: Dict[str, Any]) -> None:
        """Validate condition-specific requirements."""
        condition = data["condition"]
        threshold = data.get("threshold")

        # Conditions that require threshold
        requires_threshold = [
            "price_above", "price_below", "price_change_up", "price_change_down",
            "ma_touch_above", "ma_touch_below", "rsi_limit", "volume_change",
            "pe_ratio_below", "pe_ratio_above",
            "forward_pe_below", "forward_pe_above",
            "earnings_announcement", "dividend_ex_date"
        ]

        # Conditions that don't use threshold
        no_threshold = [
            "new_high", "new_low", "ma_crossover_golden", "ma_crossover_death",
            "daily_reminder", "reminder", "dividend_payment"
        ]

        if condition in requires_threshold and threshold is None:
            raise ValidationError(f"{condition} requires a threshold value")

        if condition in no_threshold and threshold is not None:
            raise ValidationError(f"{condition} does not use a threshold value")

        # Specific validations
        if condition in ["ma_touch_above", "ma_touch_below"]:
            if not data.get("parameters", {}).get("ma_period"):
                raise ValidationError(f"{condition} requires ma_period parameter (50 or 200)")

        if condition == "rsi_limit" and threshold is not None:
            if not 0 <= threshold <= 100:
                raise ValidationError("RSI threshold must be between 0 and 100")

        if condition == "reminder":
            params = data.get("parameters", {})
            if not params.get("reminder_date") or not params.get("reminder_time"):
                raise ValidationError("Reminder alerts require reminder_date and reminder_time")

        if condition == "daily_reminder":
            if not data.get("parameters", {}).get("reminder_time"):
                raise ValidationError("Daily reminder alerts require reminder_time")
