"""Logging configuration for StockAlert SDK."""
import logging
import os

# Create logger
logger = logging.getLogger("stockalert")

# Set default level from environment or WARNING
log_level = os.environ.get("STOCKALERT_LOG_LEVEL", "WARNING").upper()
logger.setLevel(getattr(logging, log_level, logging.WARNING))

# Add null handler by default (users can add their own)
logger.addHandler(logging.NullHandler())


def enable_debug_logging():
    """Enable debug logging for the SDK."""
    logger.setLevel(logging.DEBUG)

    # Add console handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)
