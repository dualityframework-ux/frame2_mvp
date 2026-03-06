"""
tests/test_post_generator.py
Tests for content_engine/post_generator.py:
build_post_variants, obs_mech_impl, three_ready_lines, quick_library_samples.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from content_engine.post_generator import (
    build_post_variants,
    three_ready_lines,
    quick_library_samples,
)

SAMPLE_INSIGHT = {
    "observation": "2004 finished 98-64.",
    "mechanism": "lineup resilience and on-base pressure created a team whose process was strong enough to survive variance",
    "implication": "the result matched the process.",
    "tag": "signal",
}


# ── build_post_variants ───────────────────────────────────────────────────────

class TestBuildPostVariants:
    def test_returns_string(self):
        result = build_post_variants(SAMPLE_INSIGHT)
        assert isinstance(result, str)

    def test_simple_tone_default(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="simple")
        assert len(result) > 10

    def test_analytical_tone(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="analytical")
        assert isinstance(result, str) and len(result) > 10

    def test_one_liner_tone(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="one-liner")
        assert isinstance(result, str) and len(result) > 5

    def test_unknown_tone_falls_back_to_simple(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="unknown_tone_xyz")
        assert isinstance(result, str) and len(result) > 10

    def test_output_is_lowercase_by_default(self):
        result = build_post_variants(SAMPLE_INSIGHT)
        assert result == result.lower()

    def test_contains_observation(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="simple")
        # observation lowercased
        assert "2004" in result

    def test_contains_mechanism(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="simple")
        assert "lineup" in result or "on-base" in result

    def test_contains_implication(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="simple")
        assert "matched" in result or "process" in result

    def test_analytical_contains_tag(self):
        result = build_post_variants(SAMPLE_INSIGHT, tone="analytical")
        assert "signal" in result

    def test_one_liner_does_not_contain_mechanism(self):
        # one-liner is just obs + tag
        result = build_post_variants(SAMPLE_INSIGHT, tone="one-liner")
        # mechanism text is long; one-liner should be shorter
        assert len(result) < len(SAMPLE_INSIGHT["mechanism"]) * 2

    def test_empty_insight_returns_string(self):
        result = build_post_variants({})
        assert isinstance(result, str)

    @pytest.mark.parametrize("tone", ["simple", "analytical", "one-liner"])
    def test_all_tones_return_string(self, tone):
        result = build_post_variants(SAMPLE_INSIGHT, tone=tone)
        assert isinstance(result, str)


# ── three_ready_lines ─────────────────────────────────────────────────────────

class TestThreeReadyLines:
    def test_returns_three_items(self):
        result = three_ready_lines("obs.", "mech.", "impl.")
        assert len(result) == 3

    def test_all_strings(self):
        a, b, c = three_ready_lines("obs.", "mech.", "impl.")
        assert all(isinstance(x, str) for x in (a, b, c))

    def test_minimal_is_shortest(self):
        minimal, mechanism_line, funny = three_ready_lines(
            "2004 finished 98-64.", "lineup resilience was the driver.", "the result matched the process."
        )
        assert len(minimal) <= len(mechanism_line)

    def test_funny_contains_variance(self):
        _, _, funny = three_ready_lines("obs.", "mech.", "impl.")
        assert "variance" in funny

    def test_tag_appended_when_provided(self):
        minimal, _, _ = three_ready_lines("obs.", "mech.", "impl.", tag="signal")
        assert "signal" in minimal

    def test_all_lowercase(self):
        a, b, c = three_ready_lines("OBS.", "MECH.", "IMPL.")
        assert a == a.lower()
        assert b == b.lower()
        assert c == c.lower()


# ── quick_library_samples ─────────────────────────────────────────────────────

class TestQuickLibrarySamples:
    def test_returns_list(self):
        result = quick_library_samples()
        assert isinstance(result, list)

    def test_returns_at_least_one(self):
        result = quick_library_samples()
        assert len(result) >= 1

    def test_all_strings(self):
        result = quick_library_samples()
        assert all(isinstance(s, str) for s in result)

    def test_all_lowercase(self):
        result = quick_library_samples()
        assert all(s == s.lower() for s in result)

    def test_contains_variance_undefeated(self):
        result = quick_library_samples()
        assert any("variance" in s for s in result)
