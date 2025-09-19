"""Geographic utility functions."""

import logging

from sqlalchemy import select

from ..core.database import get_async_session_local
from ..models.zip_code import ZipCode

logger = logging.getLogger(__name__)


async def get_zip_coordinates(zip_code: str) -> tuple[float, float]:
    """
    Get coordinates for a ZIP code from the database.

    Args:
        zip_code: ZIP code string

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If ZIP code not found in database
    """
    async with get_async_session_local()() as session:
        result = await session.execute(select(ZipCode.latitude, ZipCode.longitude).where(ZipCode.zip_code == zip_code))
        row = result.first()

        if row:
            logger.debug(f"Found coordinates for ZIP {zip_code}: {row.latitude}, {row.longitude}")
            return row.latitude, row.longitude

        logger.warning(f"ZIP code {zip_code} not found in database")
        raise ValueError(f"ZIP code {zip_code} not found in database")


def get_zip_coordinates_sync(zip_code: str) -> tuple[float, float]:
    """
    Synchronous fallback for ZIP coordinates (mock implementation).

    This is a fallback for when async context is not available.
    In production, this should be replaced with a proper geocoding service.

    Args:
        zip_code: ZIP code string

    Returns:
        Tuple of (latitude, longitude)
    """
    logger.warning(f"Using fallback geocoding for ZIP {zip_code}")

    # Mock implementation for demonstration
    zip_num = int(zip_code[:5]) if zip_code.isdigit() else 10001

    # Rough approximation for NY area ZIP codes
    if 10000 <= zip_num <= 14999:  # NYC area
        lat = 40.7128 + (zip_num - 10000) * 0.001
        lon = -74.0060 + (zip_num - 10000) * 0.001
    elif 10001 <= zip_num <= 10099:  # Manhattan
        lat = 40.7831
        lon = -73.9712
    else:  # Default to NYC
        lat = 40.7128
        lon = -74.0060

    return lat, lon
