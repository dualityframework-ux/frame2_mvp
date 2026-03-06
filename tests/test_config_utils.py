"""
tests/test_config_utils.py
Tests for config/utils.py and config/settings.py:
to_lowercase_if_needed, clean_spaces, cache_get/set, SETTINGS.
"""
import os
import sys
import json
import time
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.utils import to_lowercase_if_needed, clean_spaces, cache_get, cache_set
from config.settings import SETTINGS


# ── to_lowercase_if_needed ────────────────────────────────────────────────────

class TestToLowercaseIfNeeded:
    def test_enabled_converts_to_lower(self):
        assert to_lowercase_if_needed("HELLO World", True) == "hello world"

    def test_disabled_preserves_case(self):
        assert to_lowercase_if_needed("HELLO World", False) == "HELLO World"

    def test_already_lower_unchanged(self):
        assert to_lowercase_if_needed("hello", True) == "hello"

    def test_default_enabled_is_true(self):
        assert to_lowercase_if_needed("ABC") == "abc"

    def test_empty_string(self):
        assert to_lowercase_if_needed("", True) == ""

    def test_numbers_not_affected(self):
        assert to_lowercase_if_needed("Season 2004 — WS", True) == "season 2004 — ws"


# ── clean_spaces ──────────────────────────────────────────────────────────────

class TestCleanSpaces:
    def test_strips_leading_trailing(self):
        assert clean_spaces("  hello  ") == "hello"

    def test_collapses_multiple_spaces(self):
        assert clean_spaces("hello   world") == "hello world"

    def test_collapses_multiple_tabs(self):
        assert clean_spaces("hello\t\tworld") == "hello world"

    def test_collapses_excess_newlines(self):
        text = "line1\n\n\n\nline2"
        result = clean_spaces(text)
        assert "\n\n\n" not in result
        assert "line1" in result and "line2" in result

    def test_preserves_double_newline(self):
        text = "line1\n\nline2"
        result = clean_spaces(text)
        assert "\n\n" in result

    def test_empty_string(self):
        assert clean_spaces("") == ""


# ── Settings ──────────────────────────────────────────────────────────────────

class TestSettings:
    def test_app_name_is_string(self):
        assert isinstance(SETTINGS.app_name, str)
        assert len(SETTINGS.app_name) > 0

    def test_app_name_contains_redsox(self):
        assert "red sox" in SETTINGS.app_name.lower() or "redsox" in SETTINGS.app_name.lower()

    def test_lowercase_posts_is_bool(self):
        assert isinstance(SETTINGS.lowercase_posts, bool)

    def test_lowercase_posts_is_true(self):
        assert SETTINGS.lowercase_posts is True

    def test_timezone_is_string(self):
        assert isinstance(SETTINGS.timezone, str)

    def test_settings_is_frozen(self):
        with pytest.raises((AttributeError, TypeError)):
            SETTINGS.app_name = "changed"

    def test_request_timeout_positive(self):
        assert SETTINGS.request_timeout_s > 0


# ── cache_get / cache_set ─────────────────────────────────────────────────────

class TestCache:
    def test_cache_miss_returns_none_for_nonexistent(self, tmp_path):
        path = os.path.join(str(tmp_path), "nonexistent.json")
        result = cache_get(path, ttl_s=60)
        assert result is None

    def test_cache_set_creates_file(self, tmp_path):
        path = os.path.join(str(tmp_path), "sub", "cache.json")
        cache_set(path, {"key": "value"})
        assert os.path.exists(path)

    def test_cache_set_then_get_returns_data(self, tmp_path):
        path = os.path.join(str(tmp_path), "cache.json")
        data = {"season": 2004, "wins": 98}
        cache_set(path, data)
        result = cache_get(path, ttl_s=60)
        assert result == data

    def test_cache_expired_returns_none(self, tmp_path):
        path = os.path.join(str(tmp_path), "cache.json")
        cache_set(path, {"value": 42})
        # Backdate the file modification time by 120s
        old_time = time.time() - 120
        os.utime(path, (old_time, old_time))
        result = cache_get(path, ttl_s=60)
        assert result is None

    def test_cache_not_expired_returns_data(self, tmp_path):
        path = os.path.join(str(tmp_path), "cache.json")
        cache_set(path, {"value": 42})
        result = cache_get(path, ttl_s=3600)
        assert result == {"value": 42}

    def test_cache_handles_list(self, tmp_path):
        path = os.path.join(str(tmp_path), "list_cache.json")
        data = [1, 2, 3, "test"]
        cache_set(path, data)
        result = cache_get(path, ttl_s=60)
        assert result == data

    def test_cache_corrupted_file_returns_none(self, tmp_path):
        path = os.path.join(str(tmp_path), "bad.json")
        with open(path, "w") as f:
            f.write("{not valid json}")
        result = cache_get(path, ttl_s=60)
        assert result is None
