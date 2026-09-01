"""Skills matrix + résumé download."""

from __future__ import annotations

import streamlit as st

from content import PROFILE, SKILLS
from utils.style import hero
from utils.ui import level_bar, resume_download_button

hero("Skills", "Self-assessed proficiency, 1 (familiar) to 5 (expert).", key="hero_skills")

groups = [(g, items) for g, items in (SKILLS or {}).items() if items]
if not groups:
    st.caption("Add skills in content.py")
else:
    cols = st.columns(min(len(groups), 3), gap="medium")
    for i, (group, items) in enumerate(groups):
        with cols[i % len(cols)].container(
            border=True, height="stretch", key=f"card_skill_{i}"
        ):
            st.subheader(group)
            for name, lvl in items:
                level_bar(name, int(lvl))

st.space("medium")
if not resume_download_button(PROFILE, key="skills_resume"):
    st.caption(
        "Upload a résumé from the Manage page (`/manage`) to add a download "
        "button here."
    )
