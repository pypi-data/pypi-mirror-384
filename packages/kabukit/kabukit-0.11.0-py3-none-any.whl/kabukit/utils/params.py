from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator


def iter_items(kwargs: dict[str, Any]) -> Iterator[tuple[str, Any]]:
    for key, value in kwargs.items():
        if value is None:
            continue

        if key == "from_":
            yield "from", value
        else:
            yield key, value


def get_params(**kwargs: Any) -> dict[str, Any]:
    params: dict[str, Any] = {}

    for key, value in iter_items(kwargs):
        if isinstance(value, datetime.date):
            params[key] = date_to_str(value)
        elif isinstance(value, str | int | float | bool):
            params[key] = value
        else:
            params[key] = str(value)

    return params


def date_to_str(date: str | datetime.date) -> str:
    """Convert a date object or string to a YYYY-MM-DD string.

    Args:
        date: The date to convert.

    Returns:
        The date as a YYYY-MM-DD string.
    """
    if isinstance(date, datetime.date):
        return date.strftime("%Y-%m-%d")

    return date
