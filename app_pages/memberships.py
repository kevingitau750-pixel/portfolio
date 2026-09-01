"""Professional memberships."""

from __future__ import annotations

import streamlit as st

from content import MEMBERSHIPS
from utils.style import hero
from utils.ui import is_todo

hero("Professional memberships", "Professional bodies and learned societies.",
     key="hero_memberships")

rows = [m for m in (MEMBERSHIPS or []) if not is_todo(m.get("body", ""))]
if not rows:
    st.caption("Add memberships in content.py")
    st.stop()

for i, m in enumerate(rows):
    with st.container(border=True, key=f"card_member_{i}"):
        top = st.columns([3, 1], vertical_alignment="center")
        with top[0]:
            st.subheader(m["body"])
            grade = m.get("grade")
            if grade and not is_todo(grade):
                st.markdown(f":blue-badge[{grade}]")
        with top[1]:
            since = m.get("since")
            if since and not is_todo(since):
                st.caption(f"Since {since}")
        details = []
        if m.get("number") and not is_todo(str(m["number"])):
            details.append(f"Membership no. {m['number']}")
        if m.get("note") and not is_todo(m["note"]):
            details.append(m["note"])
        if details:
            st.write("  \n".join(details))
