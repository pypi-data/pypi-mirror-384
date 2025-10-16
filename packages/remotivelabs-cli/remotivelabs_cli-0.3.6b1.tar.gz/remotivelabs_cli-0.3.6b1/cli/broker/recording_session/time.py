from __future__ import annotations

import re
from typing import Optional

import typer


class InvalidOffsetException(typer.BadParameter):  # noqa: N818
    """
    Thrown if invalid time, extends BadParameter to hook into typer validation
    """


def time_offset_to_us(value: Optional[str]) -> Optional[int]:
    """
    Parse a time string like '1s', '1ms', '1us', '1.02min' or '30' (default µs) into microseconds (int).
    For minutes: 1.02min == 1 minute 2 seconds
    """
    if value is None:
        return None

    value = value.strip().lower()

    # Check if it's a minute format with decimal or colon
    min_match = re.fullmatch(r"([+-]?\d+)[.:](\d+)min", value)
    if min_match:
        minutes = int(min_match.group(1))
        seconds = int(min_match.group(2))
        return (minutes * 60 + seconds) * 1_000_000

    # Support optional + or - sign before the number
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)(?:\s*(us|µs|ms|s|min))?", value)
    if not match:
        raise InvalidOffsetException(f"Invalid time format: '{value}'")

    amount, unit = match.groups()
    amount = float(amount)
    unit = unit or "us"  # Default to microseconds

    unit_multipliers = {
        "min": 60_000_000,
        "s": 1_000_000,
        "ms": 1_000,
        "us": 1,
        "µs": 1,
    }

    return int(amount * unit_multipliers[unit])
