#!/usr/bin/env python3
"""Small standard-library compatibility helpers for Python 3.6+ hosts."""

import io
import re
import sys
from datetime import datetime, timedelta, timezone


_OFFSET_PATTERN = re.compile(r"([+-])(\d{2}):?(\d{2})$")
_DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
)


def parse_iso_datetime(value):
    """Parse the ISO-8601 forms used by the skill without datetime.fromisoformat."""
    text = str(value).strip()
    if not text:
        raise ValueError("empty ISO timestamp")

    tzinfo = None
    if text.endswith(("Z", "z")):
        text = text[:-1]
        tzinfo = timezone.utc
    else:
        offset_match = _OFFSET_PATTERN.search(text)
        if offset_match:
            sign = 1 if offset_match.group(1) == "+" else -1
            hours = int(offset_match.group(2))
            minutes = int(offset_match.group(3))
            if hours > 23 or minutes > 59:
                raise ValueError("invalid UTC offset")
            tzinfo = timezone(sign * timedelta(hours=hours, minutes=minutes))
            text = text[:offset_match.start()]

    for pattern in _DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(text, pattern)
            return parsed.replace(tzinfo=tzinfo) if tzinfo is not None else parsed
        except ValueError:
            continue
    raise ValueError("invalid ISO timestamp: {0}".format(value))


def isoformat_seconds(value):
    """Return seconds precision on Python versions with or without timespec support."""
    return value.replace(microsecond=0).isoformat()


def configure_utf8_stdio():
    """Use UTF-8 console output while retaining compatibility with Python 3.6."""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
        elif hasattr(stream, "buffer"):
            wrapper = io.TextIOWrapper(
                stream.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            setattr(sys, name, wrapper)
