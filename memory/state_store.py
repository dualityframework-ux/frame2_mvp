"""
memory/state_store.py
─────────────────────
Lightweight in-process session state store for the frame² application.
Wraps a plain dict with get/set/clear/snapshot helpers so that agents
and UI pages share a consistent interface without coupling to Streamlit's
st.session_state directly.

Usage
-----
    from memory.state_store import StateStore
    store = StateStore()
    store.set("active_season", 2004)
    season = store.get("active_season")          # 2004
    store.set("filters", {"era": "2004 era", "min_wins": 90})
    snapshot = store.snapshot()                  # dict copy
    store.clear()
"""

from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, Optional


class StateStore:
    """Simple key-value state store with optional namespace support."""

    def __init__(self, initial: Optional[Dict[str, Any]] = None) -> None:
        self._store: Dict[str, Any] = dict(initial or {})

    # ── Core API ──────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Return value for *key*, or *default* if not present."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key*."""
        self._store[key] = value

    def delete(self, key: str) -> None:
        """Remove *key* if present (no-op if missing)."""
        self._store.pop(key, None)

    def has(self, key: str) -> bool:
        """Return True if *key* exists in the store."""
        return key in self._store

    def clear(self) -> None:
        """Remove all keys."""
        self._store.clear()

    # ── Batch helpers ─────────────────────────────────────────────────────────

    def update(self, mapping: Dict[str, Any]) -> None:
        """Merge *mapping* into the store (shallow update)."""
        self._store.update(mapping)

    def snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the current state."""
        return deepcopy(self._store)

    # ── Namespace helpers ─────────────────────────────────────────────────────

    def ns_get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Get a value from a namespaced sub-dict."""
        return self._store.get(namespace, {}).get(key, default)

    def ns_set(self, namespace: str, key: str, value: Any) -> None:
        """Set a value in a namespaced sub-dict."""
        if namespace not in self._store:
            self._store[namespace] = {}
        self._store[namespace][key] = value

    def ns_clear(self, namespace: str) -> None:
        """Clear all keys in a namespace."""
        self._store.pop(namespace, None)

    # ── Dunder ────────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __repr__(self) -> str:
        keys = list(self._store.keys())
        return f"StateStore({len(keys)} keys: {keys})"


# Module-level singleton — import and use directly if you don't need isolation
_default_store = StateStore()


def get(key: str, default: Any = None) -> Any:
    return _default_store.get(key, default)


def set(key: str, value: Any) -> None:  # noqa: A001
    _default_store.set(key, value)


def delete(key: str) -> None:
    _default_store.delete(key)


def clear() -> None:
    _default_store.clear()


def snapshot() -> Dict[str, Any]:
    return _default_store.snapshot()
