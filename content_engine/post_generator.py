from __future__ import annotations

from typing import Literal

from config.settings import SETTINGS

Tone = Literal["simple", "analytical", "one-liner"]


def _clean(value: str) -> str:
    return " ".join(str(value).strip().split())


def _case(text: str) -> str:
    return text.lower() if SETTINGS.lowercase_posts else text


def build_post_variants(insight: dict, tone: Tone = "simple") -> str:
    """
    Convert an insight dict into one clean post string.

    Expected insight shape:
    {
        "observation": "...",
        "mechanism": "...",
        "implication": "...",
        "tag": "..."
    }
    """

    observation = _clean(insight.get("observation", "the game shifted."))
    mechanism = _clean(insight.get("mechanism", "one hidden edge started winning repeatedly."))
    implication = _clean(insight.get("implication", "the scoreboard usually follows the process."))
    tag = _clean(insight.get("tag", "signal"))

    if tone == "analytical":
        text = (
            f"observation: {observation}\n"
            f"mechanism: {mechanism}\n"
            f"implication: {implication}\n"
            f"tag: {tag}"
        )
    elif tone == "one-liner":
        # The short form: what happened, plus the process tag.
        text = f"{observation} frame² tag: {tag}."
    else:
        # "simple", and the fallback for any unknown tone
        text = (
            f"fans see: {observation}\n\n"
            f"frame² sees: {mechanism}\n\n"
            f"implication: {implication}"
        )
    return _case(text)


def three_ready_lines(observation: str, mechanism: str, implication: str,
                      tag: str | None = None) -> tuple[str, str, str]:
    """Three ready-to-post lines: minimal, mechanism-led, and a lighter one."""
    obs, mech, impl = _clean(observation), _clean(mechanism), _clean(implication)
    minimal = f"{obs} [{_clean(tag)}]" if tag else obs
    mechanism_line = f"{obs} the mechanism: {mech} {impl}"
    funny = f"{obs} variance tried. the process said no. {impl}"
    return _case(minimal), _case(mechanism_line), _case(funny)


def quick_library_samples() -> list[str]:
    """A few evergreen lines for the post generator's sample library."""
    samples = [
        "result = process + variance.",
        "the scoreboard is a lagging indicator. the process leads.",
        "variance is undefeated in a week. process wins the season.",
        "a lucky win and a deserved win look the same in the standings.",
    ]
    return [_case(s) for s in samples]
