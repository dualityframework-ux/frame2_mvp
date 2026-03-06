"""
tests/test_orchestrator.py
──────────────────────────
Unit + integration tests for agents/orchestrator.py,
memory/state_store.py, and models/registry.py.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.state_store import StateStore
from models.registry import get_model, list_models, describe, register, all_configs
from agents.orchestrator import Orchestrator

CSV = os.path.join(os.path.dirname(__file__), "..", "storage", "parquet", "redsox_history.csv")


# ════════════════════════════════════════════════════════════════════════
# StateStore
# ════════════════════════════════════════════════════════════════════════

class TestStateStore:
    def test_set_and_get(self):
        s = StateStore()
        s.set("key", 42)
        assert s.get("key") == 42

    def test_get_default(self):
        s = StateStore()
        assert s.get("missing", "default") == "default"

    def test_has(self):
        s = StateStore()
        s.set("x", 1)
        assert s.has("x")
        assert not s.has("y")

    def test_delete(self):
        s = StateStore()
        s.set("k", "v")
        s.delete("k")
        assert not s.has("k")

    def test_delete_missing_noop(self):
        s = StateStore()
        s.delete("nonexistent")  # should not raise

    def test_clear(self):
        s = StateStore()
        s.set("a", 1)
        s.set("b", 2)
        s.clear()
        assert len(s) == 0

    def test_update(self):
        s = StateStore()
        s.update({"a": 1, "b": 2})
        assert s.get("a") == 1
        assert s.get("b") == 2

    def test_snapshot_is_deep_copy(self):
        s = StateStore()
        s.set("lst", [1, 2, 3])
        snap = s.snapshot()
        snap["lst"].append(99)
        assert s.get("lst") == [1, 2, 3]  # original unaffected

    def test_contains(self):
        s = StateStore({"x": 10})
        assert "x" in s
        assert "y" not in s

    def test_len(self):
        s = StateStore()
        assert len(s) == 0
        s.set("a", 1)
        assert len(s) == 1

    def test_repr(self):
        s = StateStore({"foo": "bar"})
        r = repr(s)
        assert "StateStore" in r
        assert "foo" in r

    def test_namespace_set_get(self):
        s = StateStore()
        s.ns_set("seasons", "2004", {"wins": 98})
        assert s.ns_get("seasons", "2004") == {"wins": 98}

    def test_namespace_get_default(self):
        s = StateStore()
        assert s.ns_get("seasons", "1999") is None

    def test_namespace_clear(self):
        s = StateStore()
        s.ns_set("ns", "k", "v")
        s.ns_clear("ns")
        assert not s.has("ns")

    def test_initial_dict(self):
        s = StateStore({"boot": True})
        assert s.get("boot") is True


# ════════════════════════════════════════════════════════════════════════
# Registry
# ════════════════════════════════════════════════════════════════════════

class TestRegistry:
    def test_list_models_returns_list(self):
        models = list_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_get_model_known(self):
        cfg = get_model("classify_process")
        assert cfg["id"] == "classify_process"
        assert "display_name" in cfg
        assert "description" in cfg
        assert "version" in cfg

    def test_get_model_unknown_raises(self):
        with pytest.raises(KeyError):
            get_model("nonexistent_model_xyz")

    def test_describe_returns_string(self):
        d = describe("signal_vs_noise")
        assert isinstance(d, str)
        assert "Signal vs Noise" in d

    def test_register_new_model(self):
        register("test_model_temp", {
            "display_name": "Test",
            "description": "A test model",
            "version": "0.1",
        })
        cfg = get_model("test_model_temp")
        assert cfg["id"] == "test_model_temp"
        assert cfg["display_name"] == "Test"

    def test_all_configs_is_copy(self):
        configs = all_configs()
        configs["classify_process"]["version"] = "999"
        # Original should be unaffected
        assert get_model("classify_process")["version"] != "999"

    def test_all_models_have_required_keys(self):
        for mid in list_models():
            cfg = get_model(mid)
            assert "id" in cfg, f"{mid} missing 'id'"
            assert "display_name" in cfg, f"{mid} missing 'display_name'"
            assert "description" in cfg, f"{mid} missing 'description'"


# ════════════════════════════════════════════════════════════════════════
# Orchestrator
# ════════════════════════════════════════════════════════════════════════

class TestOrchestrator:
    @pytest.fixture(scope="class")
    def orch(self):
        return Orchestrator(csv_path=CSV)

    def test_repr(self, orch):
        assert "Orchestrator" in repr(orch)

    def test_df_loads_58_rows(self, orch):
        assert len(orch.df) == 58

    def test_run_season_2004(self, orch):
        result = orch.run_season(2004)
        assert result["season"] == 2004
        assert result["wins"] == 98
        assert result["tag"] in {"signal", "underperformed process", "overperformed process", "balanced"}
        assert isinstance(result["summary"], str)
        assert isinstance(result["post"], str)
        assert isinstance(result["insight"], dict)

    def test_run_season_persists_to_store(self, orch):
        orch.run_season(2007)
        stored = orch.store.ns_get("seasons", "2007")
        assert stored is not None
        assert stored["season"] == 2007

    def test_run_season_invalid_raises(self, orch):
        with pytest.raises(Exception):
            orch.run_season(1800)

    def test_run_all_returns_58(self, orch):
        results = orch.run_all()
        assert len(results) == 58
        assert 2004 in results
        assert 1967 in results

    def test_model_info(self, orch):
        info = orch.model_info("classify_process")
        assert "display_name" in info

    def test_reset_clears_state(self, orch):
        orch.run_season(2013)
        orch.reset()
        assert len(orch.store) == 0
        assert orch._df is None

    def test_tone_variants(self, orch):
        for tone in ["simple", "analytical", "one-liner"]:
            result = orch.run_season(2018, tone=tone)
            assert isinstance(result["post"], str)
            assert len(result["post"]) > 0


# ════════════════════════════════════════════════════════════════════════
# state_store module-level API
# ════════════════════════════════════════════════════════════════════════

class TestStateStoreModuleFunctions:
    """Cover lines 97, 101, 105, 109, 113 — module-level set/get/delete/clear/snapshot."""

    def setup_method(self):
        import memory.state_store as _ss
        _ss.clear()

    def test_module_set_and_get(self):
        import memory.state_store as _ss
        _ss.set("foo", "bar")
        assert _ss.get("foo") == "bar"

    def test_module_get_default(self):
        import memory.state_store as _ss
        assert _ss.get("no_key", 99) == 99

    def test_module_delete(self):
        import memory.state_store as _ss
        _ss.set("del_key", 1)
        _ss.delete("del_key")
        assert _ss.get("del_key") is None

    def test_module_clear(self):
        import memory.state_store as _ss
        _ss.set("x", 1)
        _ss.clear()
        assert _ss.get("x") is None

    def test_module_snapshot(self):
        import memory.state_store as _ss
        _ss.set("snap", 42)
        snap = _ss.snapshot()
        assert snap.get("snap") == 42
