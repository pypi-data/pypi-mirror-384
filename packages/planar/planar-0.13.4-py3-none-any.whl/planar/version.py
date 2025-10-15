"""Utilities for working with Planar package version information."""

from functools import lru_cache
from importlib import metadata
from typing import Final

PACKAGE_NAME: Final[str] = "planar"
FALLBACK_VERSION: Final[str] = "0.0.0.dev0"


@lru_cache(maxsize=1)
def get_version(
    fallback: str = FALLBACK_VERSION,
) -> str:
    """Return the installed Planar version or a fallback value.

    Args:
        fallback: Value returned if the package metadata is unavailable.

    Returns:
        The package version string if available, otherwise the fallback value.
    """

    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return fallback
