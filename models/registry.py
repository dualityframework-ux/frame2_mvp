"""
models/registry.py
──────────────────
Central registry for named model configurations used across the frame²
application. Provides a thin lookup layer so that agents and pages can
reference models by name without hardcoding display strings everywhere.

Usage
-----
    from models.registry import get_model, list_models

    cfg = get_model("classify_process")
    print(cfg["display_name"])   # "Process vs Result Classifier"
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


# ── Model definitions ─────────────────────────────────────────────────────────
# Each entry is a dict with at minimum: id, display_name, description, version.
# Additional keys (e.g. thresholds) are model-specific config.

_REGISTRY: Dict[str, Dict[str, Any]] = {
    "classify_process": {
        "id": "classify_process",
        "display_name": "Process vs Result Classifier",
        "description": (
            "Classifies each season as signal, underperformed process, "
            "overperformed process, or balanced using wins and run differential."
        ),
        "version": "1.0",
        "thresholds": {
            "signal_wins": 92,
            "signal_run_diff": 120,
            "underperform_run_diff": 80,
            "overperform_wins": 92,
        },
    },
    "signal_vs_noise": {
        "id": "signal_vs_noise",
        "display_name": "Signal vs Noise Classifier",
        "description": (
            "Classifies a multi-season trend as signal, lean, or variance "
            "based on efficiency, quality, and volume shift thresholds."
        ),
        "version": "1.0",
        "thresholds": {
            "signal_floor": 3,
            "lean_floor": 2,
            "shift_magnitude": 0.3,
            "pressure_weight": 0.7,
            "min_sample_size": 3,
        },
    },
    "plain_summary": {
        "id": "plain_summary",
        "display_name": "Plain-English Season Summarizer",
        "description": (
            "Generates a one-sentence fan-facing summary for each season "
            "based on wins, run differential, and process tag."
        ),
        "version": "1.0",
    },
    "ian_insight": {
        "id": "ian_insight",
        "display_name": "Ian Insight Builder",
        "description": (
            "Assembles a structured observation / mechanism / implication "
            "insight dict from a season row for use in post generation."
        ),
        "version": "1.0",
    },
    "post_generator": {
        "id": "post_generator",
        "display_name": "Post Variant Generator",
        "description": (
            "Formats an insight dict into simple, analytical, or one-liner "
            "post variants suitable for social media or internal reports."
        ),
        "version": "1.0",
        "tones": ["simple", "analytical", "one-liner"],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_model(model_id: str) -> Dict[str, Any]:
    """Return config dict for *model_id*. Raises KeyError if not found."""
    if model_id not in _REGISTRY:
        raise KeyError(
            f"Model '{model_id}' not in registry. "
            f"Available: {list(_REGISTRY.keys())}"
        )
    return dict(_REGISTRY[model_id])


def list_models() -> List[str]:
    """Return sorted list of registered model IDs."""
    return sorted(_REGISTRY.keys())


def describe(model_id: str) -> str:
    """Return a human-readable description for *model_id*."""
    cfg = get_model(model_id)
    return (
        f"{cfg['display_name']} (v{cfg.get('version','?')}): "
        f"{cfg['description']}"
    )


def register(model_id: str, config: Dict[str, Any]) -> None:
    """Register or overwrite a model config at runtime."""
    if "id" not in config:
        config["id"] = model_id
    _REGISTRY[model_id] = config


def all_configs() -> Dict[str, Dict[str, Any]]:
    """Return a copy of the full registry."""
    return {k: dict(v) for k, v in _REGISTRY.items()}
