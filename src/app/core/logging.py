"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path

from ..core.config import settings


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Set up root logger
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log"),
        ],
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)
