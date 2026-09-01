"""Small rendering helpers shared across pages. Native Streamlit only."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils import store

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def asset_path(name: str | None) -> Path | None:
    """Resolve an assets-relative path, or None if missing / not set."""
    if not name:
        return None
    p = ASSETS_DIR / name
    return p if p.exists() else None


def is_todo(value: object) -> bool:
    """True for placeholder strings that start with 'TODO'."""
    return isinstance(value, str) and value.strip().upper().startswith("TODO")


def show_image(name: str | None, *, placeholder_icon: str = ":material/image:",
               width: str | int = "stretch", caption: str | None = None) -> None:
    """Render an image if it exists, else a tidy bordered icon placeholder."""
    path = asset_path(name)
    if path is not None:
        st.image(str(path), width=width, caption=caption)
        return
    with st.container(border=True, horizontal_alignment="center"):
        st.markdown(placeholder_icon)
        st.caption("Add an image in content.py")


def level_bar(label: str, level: int, max_level: int = 5) -> None:
    """One skill row: label + a progress bar for the 1–max_level rating."""
    level = max(0, min(level, max_level))
    st.markdown(f"**{label}**")
    st.progress(level / max_level)


def badges(items, color: str = "blue") -> None:
    """Render a list of short strings as inline badges."""
    items = [str(i) for i in (items or []) if i and not is_todo(i)]
    if not items:
        return
    st.markdown(" ".join(f":{color}-badge[{i}]" for i in items))


def link_row(links: dict[str, str]) -> None:
    """Render a horizontal row of link buttons, skipping empty/TODO targets."""
    valid = {k: v for k, v in (links or {}).items() if v and not is_todo(v)}
    if not valid:
        return
    with st.container(horizontal=True):
        for text, url in valid.items():
            st.link_button(text, url)


def section_missing(msg: str) -> None:
    st.caption(f":material/edit_note: {msg}")


# ---------------------------------------------------------------------------
# Resolvers: an upload from the Manage page wins over an assets/ file, which
# wins over the generated placeholder. Public pages only ever read the public
# store, so a private document can never surface here.
# ---------------------------------------------------------------------------
def resolved_headshot(profile: dict) -> Path | None:
    record = store.latest_public("headshot")
    if record is not None:
        path = store.path_for(record)
        if path is not None:
            return path
    return asset_path(profile.get("headshot"))


def resolved_resume(profile: dict) -> tuple[Path | None, str]:
    """Return (path, download filename) for the resume, or (None, "")."""
    record = store.latest_public("resume")
    if record is not None:
        path = store.path_for(record)
        if path is not None:
            return path, record.get("original_name") or path.name
    path = asset_path(profile.get("resume_file"))
    return (path, path.name) if path is not None else (None, "")


def resolved_project_image(project: dict) -> Path | None:
    uploaded = store.project_image(project.get("title", ""))
    if uploaded is not None:
        return uploaded
    return asset_path(project.get("image"))


def resume_download_button(profile: dict, *, key: str) -> bool:
    """Render the resume download button if a resume exists. True if shown."""
    path, filename = resolved_resume(profile)
    if path is None:
        return False
    st.download_button(
        "Download resume (PDF)",
        data=path.read_bytes(),
        file_name=filename,
        icon=":material/download:",
        type="primary",
        key=key,
    )
    return True
