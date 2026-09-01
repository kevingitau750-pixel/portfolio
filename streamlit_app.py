"""Personal portfolio — entry point and navigation.

Run from the `portfolio/` directory:

    streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from content import PROFILE
from utils.style import inject_global_style
from utils.ui import is_todo, resolved_headshot

name = PROFILE["name"]
page_title = "Portfolio" if is_todo(name) else name

st.set_page_config(
    page_title=page_title,
    page_icon=":material/flight_takeoff:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_style()

logo = resolved_headshot(PROFILE)
if logo is not None:
    st.logo(str(logo))

pages = [
    st.Page("app_pages/about.py", title="About", icon=":material/person:", default=True),
    st.Page("app_pages/projects.py", title="Projects", icon=":material/rocket_launch:"),
    st.Page("app_pages/experience.py", title="Experience", icon=":material/work:"),
    st.Page("app_pages/skills.py", title="Skills", icon=":material/insights:"),
    st.Page("app_pages/memberships.py", title="Memberships", icon=":material/groups:"),
    st.Page("app_pages/contact.py", title="Contact", icon=":material/mail:"),
]

# The upload area is registered but hidden from the public navigation: its URL
# (/manage) always resolves, it just is not advertised. Once this session signs
# in, it joins the nav so you can move between it and the site. The password
# gate on the page itself is what actually protects it.
pages.append(
    st.Page(
        "app_pages/admin.py",
        title="Manage",
        icon=":material/upload_file:",
        url_path="manage",
        visibility="visible" if st.session_state.get("admin_unlocked") else "hidden",
    )
)

nav = st.navigation(pages, position="top")
nav.run()

st.divider()
foot = " · ".join(
    x for x in (
        None if is_todo(name) else name,
        PROFILE.get("tagline"),
        None if is_todo(PROFILE.get("location", "")) else PROFILE.get("location"),
    ) if x
)
st.caption(foot)
