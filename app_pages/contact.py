"""Contact details."""

from __future__ import annotations

import streamlit as st

from content import CONTACT, PROFILE
from utils.style import hero
from utils.ui import is_todo

name = PROFILE.get("name", "")
sub = f"Reach {name} through any of the channels below." if not is_todo(name) else None
hero("Get in touch", sub, key="hero_contact")

rows = [
    (":material/mail:", "Email", CONTACT.get("email"),
     lambda v: f"mailto:{v}"),
    (":material/call:", "Phone", CONTACT.get("phone"), None),
    (":material/link:", "LinkedIn", CONTACT.get("linkedin"), lambda v: v),
    (":material/code:", "GitHub", CONTACT.get("github"), lambda v: v),
    (":material/language:", "Website", CONTACT.get("website"), lambda v: v),
]

any_shown = False
for icon, label, value, href in rows:
    if not value or is_todo(value):
        continue
    any_shown = True
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        st.markdown(icon)
        st.markdown(f"**{label}**")
        if href is not None:
            st.link_button(value, href(value), type="tertiary")
        else:
            st.write(value)

if not any_shown:
    st.caption("Add your contact links in content.py")
