"""Experience & education."""

from __future__ import annotations

import streamlit as st

from content import CERTIFICATIONS, EDUCATION, EXPERIENCE
from utils import store
from utils.style import hero
from utils.ui import badges, is_todo

hero("Experience & education", "Roles, degree and certifications.", key="hero_experience")

work, study, certs = st.tabs(["Work", "Education", "Certifications & licences"])

with work:
    if not EXPERIENCE:
        st.caption("Add roles in content.py")
    for i, job in enumerate(EXPERIENCE):
        with st.container(border=True, key=f"card_job_{i}"):
            head = st.columns([3, 1], vertical_alignment="center")
            with head[0]:
                title = job.get("title", "")
                org = job.get("org", "")
                st.subheader(title if not is_todo(title) else "Role")
                sub = " — ".join(
                    x for x in (org, job.get("location", "")) if x and not is_todo(x)
                )
                if sub:
                    st.caption(sub)
            with head[1]:
                span = " – ".join(
                    x for x in (job.get("start", ""), job.get("end", "")) if x and not is_todo(x)
                )
                if span:
                    st.caption(span)
            for b in job.get("bullets", []):
                if not is_todo(b):
                    st.markdown(f"- {b}")
            badges(job.get("tags", []))

with study:
    if not EDUCATION:
        st.caption("Add education in content.py")
    for i, ed in enumerate(EDUCATION):
        with st.container(border=True, key=f"card_edu_{i}"):
            st.subheader(ed.get("qualification", "Qualification"))
            sub = " — ".join(
                x for x in (ed.get("org", ""), ed.get("location", "")) if x and not is_todo(x)
            )
            span = " – ".join(
                x for x in (ed.get("start", ""), ed.get("end", "")) if x and not is_todo(x)
            )
            if sub:
                st.caption(sub + (f"  ·  {span}" if span else ""))
            elif span:
                st.caption(span)
            for d in ed.get("details", []):
                if not is_todo(d):
                    st.markdown(f"- {d}")

with certs:
    rows = [c for c in CERTIFICATIONS if not is_todo(c.get("name", ""))]
    if rows:
        st.dataframe(
            rows,
            hide_index=True,
            column_config={
                "name": "Certification",
                "issuer": "Issuer",
                "year": "Year",
            },
        )
    else:
        st.caption("Add certifications, ratings or short courses in content.py")

    # Certificate files uploaded from the Manage page. Public store only.
    uploaded = store.public_records("certificate")
    if uploaded:
        st.subheader("Certificates")
        for record in uploaded:
            with st.container(border=True, key=f"card_cert_{record['id']}"):
                preview, detail = st.columns(
                    [1, 3], gap="medium", vertical_alignment="center"
                )
                path = store.path_for(record)
                with preview:
                    if path is None:
                        st.caption(":material/broken_image: file missing")
                    elif record.get("is_image"):
                        st.image(str(path), width="stretch")
                    else:
                        st.markdown("# :material/picture_as_pdf:")
                with detail:
                    st.markdown(f"**{record.get('title') or record['original_name']}**")
                    meta = " · ".join(
                        str(x) for x in (record.get("issuer"), record.get("year")) if x
                    )
                    if meta:
                        st.caption(meta)
                    if path is not None:
                        st.download_button(
                            "View certificate",
                            data=path.read_bytes(),
                            file_name=record["original_name"],
                            icon=":material/download:",
                            key=f"cert_dl_{record['id']}",
                        )
    else:
        st.caption(
            "Upload certificate files from the Manage page (`/manage`) to show "
            "them here."
        )
