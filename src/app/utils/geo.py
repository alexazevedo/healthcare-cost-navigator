"""Geographic utility functions."""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def get_zip_coordinates(zip_code: str) -> tuple[float, float]:
    """
    Get coordinates for a ZIP code.

    Note: This is a simplified implementation. In production, you would use
    a proper geocoding service like Google Maps API, US Census API, or similar.

    Args:
        zip_code: ZIP code string

    Returns:
        Tuple of (latitude, longitude)
    """
    # This is a mock implementation for demonstration
    # In production, you would use a real geocoding service
    # For now, we'll use approximate coordinates for New York area ZIP codes

    # Convert ZIP to approximate coordinates (very rough approximation)
    # This is just for demo purposes - real implementation would use geocoding API
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
