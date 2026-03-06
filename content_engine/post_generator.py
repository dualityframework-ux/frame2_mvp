from config.settings import SETTINGS
from config.utils import to_lowercase_if_needed, clean_spaces


def obs_mech_impl(observation: str, mechanism: str, implication: str) -> str:
    text = f"{observation}\n\n{mechanism}\n\n{implication}"
    text = clean_spaces(text)
    return to_lowercase_if_needed(text, SETTINGS.lowercase_posts)


def build_post_variants(insight: dict, tone: str = "simple") -> str:
    obs  = insight.get("observation", "")
    mech = insight.get("mechanism", "")
    impl = insight.get("implication", "")
    tag  = insight.get("tag", "")

    lc = SETTINGS.lowercase_posts

    if tone == "simple":
        return obs_mech_impl(obs, mech, impl)

    if tone == "analytical":
        tag_txt = f" ({tag})" if tag else ""
        text = clean_spaces(f"{obs}\n\n{mech}\n\n{impl}{tag_txt}")
        return to_lowercase_if_needed(text, lc)

    if tone == "one-liner":
        tag_txt = f" ({tag})" if tag else ""
        text = clean_spaces(f"{obs}{tag_txt}")
        return to_lowercase_if_needed(text, lc)

    return obs_mech_impl(obs, mech, impl)


def three_ready_lines(observation: str, mechanism: str, implication: str, tag: str = ""):
    tag_txt = f" ({tag})" if tag else ""
    minimal = to_lowercase_if_needed(
        clean_spaces(observation + tag_txt), SETTINGS.lowercase_posts
    )
    mechanism_line = obs_mech_impl(observation, mechanism, implication + tag_txt)
    funny = to_lowercase_if_needed(
        clean_spaces(f"{observation}\n\n{mechanism}\n\nvariance undefeated.{tag_txt}"),
        SETTINGS.lowercase_posts,
    )
    return minimal, mechanism_line, funny


def quick_library_samples():
    posts = [
        "variance undefeated.",
        "incentives shape outcomes.",
        "systems produce behavior.",
        "pressure changes decision quality.",
        "result ≠ process.",
        "clarity is rare because noise is addictive.",
    ]
    return [to_lowercase_if_needed(p, SETTINGS.lowercase_posts) for p in posts]
