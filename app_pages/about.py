"""About / bio."""

from __future__ import annotations

import streamlit as st

from content import CERTIFICATIONS, CONTACT, EXPERIENCE, PROFILE, PROJECTS
from utils.style import avatar_fallback, hero
from utils.ui import (
    badges,
    is_todo,
    link_row,
    resolved_headshot,
    resume_download_button,
    show_image,
)

name = PROFILE["name"] if not is_todo(PROFILE["name"]) else "Your name"
hero(name, PROFILE["tagline"], key="hero_about")

left, right = st.columns([1, 2], vertical_alignment="top", gap="large")

with left:
    headshot = resolved_headshot(PROFILE)
    if headshot is not None:
        show_image(headshot)
    else:
        avatar_fallback()
    link_row({
        "LinkedIn": CONTACT.get("linkedin"),
        "GitHub": CONTACT.get("github"),
        "Email": f"mailto:{CONTACT['email']}" if CONTACT.get("email") else None,
    })

with right:
    if is_todo(PROFILE["summary"]):
        st.caption("Add a short professional summary in content.py")
    else:
        st.write(PROFILE["summary"])

# At-a-glance counts, derived from content.py so they can never drift.
st.space("small")
stats = [
    ("Projects & research", len(PROJECTS), ":material/rocket_launch:"),
    ("Roles held", len(EXPERIENCE), ":material/work:"),
    ("Certifications", len(CERTIFICATIONS), ":material/verified:"),
]
cols = st.columns(len(stats), gap="medium")
for i, (col, (label, value, icon)) in enumerate(zip(cols, stats)):
    with col.container(border=True, height="stretch", key=f"card_stat_{i}"):
        st.metric(label, value, icon=icon)

st.subheader("Focus areas")
focus = PROFILE.get("focus_areas") or []
if focus:
    badges(focus)
else:
    st.caption("Add focus areas in content.py")

st.space("small")
resume_download_button(PROFILE, key="about_resume")
