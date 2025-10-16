"""Yamllint format enum."""

from __future__ import annotations

from enum import StrEnum, auto


class YamllintFormat(StrEnum):
    """Output styles supported by Yamllint's CLI."""

    PARSABLE = auto()
    STANDARD = auto()
    COLORED = auto()
    GITHUB = auto()
    AUTO = auto()


def normalize_yamllint_format(value: str | YamllintFormat) -> YamllintFormat:
    """Normalize a value to a YamllintFormat enum member.

    Args:
        value: Existing enum member or string name of the format.

    Returns:
        YamllintFormat: Canonical enum value, defaulting to ``PARSABLE`` when
        parsing fails.
    """
    if isinstance(value, YamllintFormat):
        return value
    try:
        return YamllintFormat[value.upper()]
    except Exception:
        return YamllintFormat.PARSABLE
