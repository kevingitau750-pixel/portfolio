"""Visual layer: page artwork, hero banners, card media.

This is the ONE place the app uses custom CSS. It stays deliberately scoped:
colours, fonts and radius still come from ``.streamlit/config.toml`` (native
theming). This module only adds what Streamlit has no equivalent for — a
full-page illustrated background, the gradient hero banner, and illustrated
media tiles for cards.

All artwork is generated SVG in ``assets/backgrounds/``, embedded as data URIs
so the app makes no external requests and works offline and on Streamlit Cloud.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

_BG_DIR = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"

# Per-page hero: (gradient start, gradient end, artwork file).
# All three artworks are white-on-transparent, so they sit over any gradient.
HEROES = {
    "hero_about":       ("#0a2036", "#14618f", "hero-horizon.svg"),
    "hero_projects":    ("#0a3330", "#12766e", "hero-orbit.svg"),
    "hero_experience":  ("#111f38", "#1f5480", "hero-network.svg"),
    "hero_skills":      ("#161f45", "#3a53a8", "hero-network.svg"),
    "hero_memberships": ("#0e1f3a", "#2a4e8a", "hero-orbit.svg"),
    "hero_contact":     ("#082a36", "#0f6f7e", "hero-horizon.svg"),
    "hero_admin":       ("#1d2430", "#3d4a5c", "hero-network.svg"),
}

# Illustrated media tiles available to cards via `media_art("<name>")`.
CARD_ART = ("sat", "globe", "hub", "rocket", "flight")


@lru_cache(maxsize=32)
def _data_uri(filename: str) -> str:
    """Embed an SVG from assets/backgrounds as a base64 data URI."""
    raw = (_BG_DIR / filename).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode("ascii")


def _theme_type() -> str:
    try:
        return st.context.theme.type or "light"
    except Exception:
        return "light"


def inject_global_style() -> None:
    """Inject page artwork and component styles. Call once per run, from
    ``streamlit_app.py``, before any page content."""
    dark = _theme_type() == "dark"

    art = _data_uri("page-dark.svg" if dark else "page-light.svg")
    grid = _data_uri("grid-dark.svg" if dark else "grid-light.svg")

    if dark:
        sky = "linear-gradient(180deg, #0a121d 0%, #0e1826 45%, #0b1622 100%)"
        header_bg = "rgba(12, 20, 30, 0.72)"
        header_line = "rgba(124, 192, 240, 0.14)"
        card_bg = "rgba(19, 29, 41, 0.86)"
        card_shadow = "0 1px 2px rgba(0, 0, 0, 0.35)"
        card_hover = "0 12px 30px rgba(0, 0, 0, 0.48)"
    else:
        sky = "linear-gradient(180deg, #eef4fb 0%, #fbfcfe 45%, #f4f8fd 100%)"
        header_bg = "rgba(255, 255, 255, 0.74)"
        header_line = "rgba(11, 95, 165, 0.10)"
        card_bg = "rgba(255, 255, 255, 0.90)"
        card_shadow = "0 1px 2px rgba(16, 40, 70, 0.07)"
        card_hover = "0 12px 30px rgba(16, 40, 70, 0.15)"

    hero_rules = "\n".join(
        f'.st-key-{key} {{ background-image: url("{_data_uri(f)}"), '
        f"linear-gradient(118deg, {a} 0%, {b} 100%); }}"
        for key, (a, b, f) in HEROES.items()
    )
    art_rules = "\n".join(
        f'.portfolio-media.pm-{name} {{ background-image: url("{_data_uri(f"card-{name}.svg")}"); }}'
        for name in CARD_ART
    )

    st.html(
        f"""
<style>
/* ---------- Page canvas ---------- */
[data-testid="stAppViewContainer"] {{
    background-image: url("{art}"), url("{grid}"), {sky};
    background-size: cover, 44px 44px, cover;
    background-position: center top, top left, center;
    background-repeat: no-repeat, repeat, no-repeat;
    background-attachment: fixed, fixed, fixed;
}}

/* Wide layout, held to a comfortable measure and centred like a real site */
[data-testid="stMainBlockContainer"] {{
    max-width: 1080px;
    padding-top: 2.6rem;
    padding-bottom: 4rem;
}}

/* Sticky, frosted top bar so content scrolls cleanly underneath */
[data-testid="stHeader"] {{
    background: {header_bg};
    backdrop-filter: saturate(180%) blur(12px);
    -webkit-backdrop-filter: saturate(180%) blur(12px);
    border-bottom: 1px solid {header_line};
}}

/* ---------- Hero banner ---------- */
[class*="st-key-hero_"] {{
    position: relative;
    padding: 2.4rem 2.2rem 2rem;
    border-radius: 18px;
    margin-bottom: 1.75rem;
    background-repeat: no-repeat, no-repeat;
    background-size: cover, cover;
    background-position: center right, center;
    box-shadow: 0 14px 40px rgba(8, 28, 56, 0.28),
                inset 0 0 0 1px rgba(255, 255, 255, 0.13);
    overflow: hidden;
}}
[class*="st-key-hero_"] * {{ color: #ffffff !important; }}
[class*="st-key-hero_"] h1 {{
    margin: 0 0 0.3rem 0;
    font-weight: 700;
    letter-spacing: -0.018em;
    line-height: 1.12;
    text-shadow: 0 2px 18px rgba(0, 0, 0, 0.28);
}}
[class*="st-key-hero_"] p {{
    margin: 0;
    font-size: 1.03rem;
    font-weight: 400;
    opacity: 0.9;
    max-width: 46rem;
    text-shadow: 0 1px 10px rgba(0, 0, 0, 0.25);
}}
{hero_rules}

/* ---------- Card media tiles ---------- */
.portfolio-media {{
    height: 172px;
    border-radius: 12px;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16),
                0 2px 10px rgba(8, 28, 56, 0.16);
}}
{art_rules}

/* ---------- Headshot placeholder ---------- */
.portfolio-avatar {{
    aspect-ratio: 1 / 1;
    width: 100%;
    border-radius: 16px;
    background-image: url("{_data_uri("card-avatar.svg")}");
    background-size: cover;
    background-position: center;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16),
                0 4px 16px rgba(8, 28, 56, 0.18);
}}

/* ---------- Cards ----------
   Every bordered card carries a `card_` key, so it reads as a solid frosted
   panel over the page artwork instead of letting it show through the text. */
[class*="st-key-card_"] {{
    background: {card_bg};
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 14px;
    box-shadow: {card_shadow};
    transition: box-shadow 170ms ease, transform 170ms ease;
}}
[class*="st-key-card_"]:hover {{
    box-shadow: {card_hover};
    transform: translateY(-2px);
}}
</style>
""",
    )


def hero(title: str, subtitle: str | None = None, *, key: str) -> None:
    """Full-width banner: page gradient + aerospace artwork + title."""
    with st.container(key=key):
        st.markdown(f"# {title}")
        if subtitle:
            st.markdown(f"<p>{subtitle}</p>", unsafe_allow_html=True)


def avatar_fallback() -> None:
    """Illustrated square placeholder shown when no headshot is set."""
    st.html('<div class="portfolio-avatar"></div>')


def media_art(name: str = "sat") -> None:
    """Illustrated media tile for a card that has no photo yet."""
    slug = name if name in CARD_ART else "sat"
    st.html(f'<div class="portfolio-media pm-{slug}"></div>')
