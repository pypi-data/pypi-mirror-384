"""
Utility functions for parsing period/duration strings into minutes.

Supports formats like:
- "1h" -> 60 minutes
- "30m" -> 30 minutes
- "1h 30m" -> 90 minutes
- "2d" -> 2880 minutes (2 days * 24 hours * 60 minutes)
- "1w" -> 10080 minutes (1 week * 7 days * 24 hours * 60 minutes)
- "1w 2d 3h 30m" -> complex calculation
"""

import logging
import re

logger = logging.getLogger(__name__)


def parse_period_to_minutes(period_string: str | int) -> int:
    """
    Parse a human-readable period string into minutes.

    Supported units:
    - w: weeks (7 days)
    - d: days (24 hours)
    - h: hours (60 minutes)
    - m: minutes

    Examples:
        >>> parse_period_to_minutes("1h")
        60
        >>> parse_period_to_minutes("1h 30m")
        90
        >>> parse_period_to_minutes("2d")
        2880
        >>> parse_period_to_minutes("1w 2d 3h 30m")
        13650

    Args:
        period_string: The period string to parse (e.g., "1h 30m") or integer minutes

    Returns:
        Total minutes as an integer

    Raises:
        ValueError: If the period string format is invalid
    """
    # If it's already an integer, return it
    if isinstance(period_string, int):
        return period_string

    if not period_string or not isinstance(period_string, str):
        raise ValueError(f'Invalid period string: {period_string}')

    # Remove extra whitespace and convert to lowercase
    period_string = period_string.strip().lower()

    # If it's a number string, treat it as minutes
    if period_string.isdigit():
        return int(period_string)

    # Define conversion factors to minutes
    units = {
        'w': 7 * 24 * 60,  # weeks to minutes
        'd': 24 * 60,  # days to minutes
        'h': 60,  # hours to minutes
        'm': 1,  # minutes to minutes
    }

    # Pattern to match numbers followed by unit letters
    # Matches: "1h", "30m", "1.5h", etc.
    pattern = r'(\d+(?:\.\d+)?)\s*([wdhm])'

    matches = re.findall(pattern, period_string)

    if not matches:
        raise ValueError(
            f"Invalid period format: '{period_string}'. "
            "Expected format like '1h', '30m', '1h 30m', '2d', '1w 2d 3h 30m'"
        )

    total_minutes = 0.0

    for value_str, unit in matches:
        value = float(value_str)
        if unit not in units:
            msg = f'Unknown unit: {unit}'
            raise ValueError(msg)

        total_minutes += value * units[unit]

    # Return as integer (YouTrack expects integer minutes)
    return int(total_minutes)


def format_minutes_to_period(minutes: int | float) -> str:
    """
    Format minutes into a human-readable period string.

    Args:
        minutes: Number of minutes

    Returns:
        Human-readable period string (e.g., "1h 30m")

    Examples:
        >>> format_minutes_to_period(60)
        "1h"
        >>> format_minutes_to_period(90)
        "1h 30m"
        >>> format_minutes_to_period(2880)
        "2d"
    """
    if not isinstance(minutes, int | float) or minutes < 0:
        raise ValueError(f'Invalid minutes value: {minutes}')

    minutes = int(minutes)

    if minutes == 0:
        return '0m'

    # Calculate components
    weeks = minutes // (7 * 24 * 60)
    minutes %= 7 * 24 * 60

    days = minutes // (24 * 60)
    minutes %= 24 * 60

    hours = minutes // 60
    mins = minutes % 60

    # Build the result string
    parts = []
    if weeks > 0:
        parts.append(f'{weeks}w')
    if days > 0:
        parts.append(f'{days}d')
    if hours > 0:
        parts.append(f'{hours}h')
    if mins > 0:
        parts.append(f'{mins}m')

    return ' '.join(parts)
