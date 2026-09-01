"""Projects portfolio."""

from __future__ import annotations

import streamlit as st

from content import PROJECTS
from utils.style import hero, media_art
from utils.ui import badges, is_todo, link_row, resolved_project_image, show_image

hero("Projects", "Selected engineering, research and software work.", key="hero_projects")

projects = PROJECTS or []
all_tech = sorted({t for p in projects for t in p.get("tech", []) if not is_todo(t)})

with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
    selected = st.multiselect(
        "Filter by technology",
        all_tech,
        placeholder="Filter by technology",
        label_visibility="collapsed",
    ) if all_tech else []
    only_featured = st.toggle("Featured only", value=False)


def matches(project: dict) -> bool:
    if only_featured and not project.get("featured"):
        return False
    if selected and not set(selected).issubset(set(project.get("tech", []))):
        return False
    return True


shown = [p for p in projects if matches(p)]
if not shown:
    st.info("No projects match the current filter.", icon=":material/filter_alt_off:")
    st.stop()

st.caption(f"{len(shown)} of {len(projects)} projects")

for i, project in enumerate(shown):
    with st.container(border=True, key=f"card_project_{i}"):
        media, body = st.columns([1, 2], gap="large", vertical_alignment="top")
        with media:
            image = resolved_project_image(project)
            if image is not None:
                show_image(image)
            else:
                media_art(project.get("icon", "sat"))
        with body:
            title = project["title"]
            st.subheader(title if not is_todo(title) else "Untitled project")
            meta = " · ".join(
                str(x) for x in (project.get("period"), project.get("role"))
                if x and not is_todo(str(x))
            )
            if meta:
                st.caption(meta)
            summary = project.get("summary", "")
            if summary and not is_todo(summary):
                st.write(summary)

            highlights = [h for h in project.get("highlights", []) if not is_todo(h)]
            for h in highlights:
                st.markdown(f"- {h}")

            badges(project.get("tech", []))
            link_row(project.get("links", {}))
