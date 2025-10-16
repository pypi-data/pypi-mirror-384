"""Lightweight client accessors with safe fallbacks.

This module provides optional clients that might not be available or
initialized in all environments (e.g., CI, local tests). We guard their
initialization to avoid import-time side effects and allow the rest of
the package to function with sensible fallbacks.
"""

from typing import Any


def _safe_get_langfuse() -> Any | None:
    try:
        from langfuse._client.get_client import get_client  # type: ignore

        return get_client()
    except Exception:
        # SDK not installed or not initialized; use None so callers can guard usage
        return None


langfuse = _safe_get_langfuse()
