"""
agents/orchestrator.py
──────────────────────
Lightweight orchestration layer for the frame² application.
Coordinates data loading, classification, insight generation, and
post-variant formatting into a single callable pipeline.

Usage
-----
    from agents.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.run_season(2004)
    # result["tag"]       → "signal"
    # result["summary"]   → "This team was as good as it looked…"
    # result["post"]      → str (simple tone)
    # result["insight"]   → {"observation": …, "mechanism": …, …}
"""

from __future__ import annotations
import os
import sys
from typing import Any, Dict, Optional

# Make project root importable regardless of working directory
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from adapters.redsox_history_loader import load_redsox_history
from intelligence.redsox_history_engine import (
    get_season_row,
    classify_process_vs_result,
    build_plain_summary,
    build_ian_insight,
)
from content_engine.post_generator import build_post_variants
from memory.state_store import StateStore
from models.registry import get_model


_DEFAULT_CSV = os.path.join(_ROOT, "storage", "parquet", "redsox_history.csv")


class Orchestrator:
    """
    Runs the full frame² pipeline for one or many seasons.

    Parameters
    ----------
    csv_path : str, optional
        Path to redsox_history.csv.  Defaults to the project-bundled file.
    store : StateStore, optional
        State store instance.  A fresh one is created if not provided.
    """

    def __init__(
        self,
        csv_path: str = _DEFAULT_CSV,
        store: Optional[StateStore] = None,
    ) -> None:
        self.csv_path = csv_path
        self.store = store or StateStore()
        self._df = None  # lazy-loaded

    # ── Data ─────────────────────────────────────────────────────────────────

    @property
    def df(self):
        if self._df is None:
            self._df = load_redsox_history(self.csv_path)
        return self._df

    # ── Single-season pipeline ────────────────────────────────────────────────

    def run_season(self, season: int, tone: str = "simple") -> Dict[str, Any]:
        """
        Run the full pipeline for one *season*.

        Returns
        -------
        dict with keys: season, wins, losses, tag, explanation,
                        summary, insight, post
        """
        row = get_season_row(self.df, season)
        tag, explanation = classify_process_vs_result(row)
        summary = build_plain_summary(row, tag)
        insight = build_ian_insight(row)
        post = build_post_variants(insight, tone=tone)

        result: Dict[str, Any] = {
            "season": int(row["season"]),
            "wins": int(row["wins"]),
            "losses": int(row["losses"]),
            "tag": tag,
            "explanation": explanation,
            "summary": summary,
            "insight": insight,
            "post": post,
        }

        # Persist to state store so pages/agents can read without re-running
        self.store.ns_set("seasons", str(season), result)
        return result

    # ── Batch pipeline ────────────────────────────────────────────────────────

    def run_all(self, tone: str = "simple") -> Dict[int, Dict[str, Any]]:
        """Run the pipeline for every season in the dataset."""
        results = {}
        for season in sorted(self.df["season"].tolist()):
            results[season] = self.run_season(int(season), tone=tone)
        return results

    # ── Helpers ───────────────────────────────────────────────────────────────

    def model_info(self, model_id: str = "classify_process") -> Dict[str, Any]:
        """Return registry config for *model_id*."""
        return get_model(model_id)

    def reset(self) -> None:
        """Clear cached dataframe and state store."""
        self._df = None
        self.store.clear()

    def __repr__(self) -> str:
        loaded = "loaded" if self._df is not None else "not loaded"
        return f"Orchestrator(csv={os.path.basename(self.csv_path)}, df={loaded})"
