"""Manage — password-gated upload area. Not linked from the public site.

Reach it at ``/manage``. The page is registered but hidden from the public
navigation. Everything here is gated on a password held in
``.streamlit/secrets.toml``; with no password configured the page refuses to
accept uploads at all rather than falling back to a default.
"""

from __future__ import annotations

import hmac

import streamlit as st

from content import PROJECTS
from utils import store
from utils.style import hero

# Keep the widget's stated limit in step with what the store actually enforces.
MAX_MB = store.MAX_BYTES // (1024 * 1024)

hero("Manage", "Upload your photo, résumé, certificates and documents.", key="hero_admin")


# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------
# Values that mean "the example file was copied but never edited".
PLACEHOLDERS = {"CHANGE-ME", "changeme", "password", "admin", ""}


def _configured_password() -> str | None:
    """The configured admin password, or None if unset or still a placeholder."""
    try:
        value = st.secrets.get("admin_password")
    except Exception:
        return None
    if value is None:
        return None
    value = str(value)
    return None if value.strip() in PLACEHOLDERS else value


password = _configured_password()

if password is None:
    st.error(
        "No admin password is configured, so uploads are disabled.",
        icon=":material/lock:",
    )
    st.markdown(
        "Create `portfolio/.streamlit/secrets.toml` with:\n\n"
        "```toml\n"
        'admin_password = "choose-a-long-random-passphrase"\n'
        "```\n\n"
        "That file is git-ignored, so it never leaves your machine. On "
        "Streamlit Community Cloud, set the same key under "
        "**App settings → Secrets** instead."
    )
    st.stop()

st.session_state.setdefault("admin_unlocked", False)

if not st.session_state.admin_unlocked:
    with st.form("admin_unlock", border=True):
        st.subheader("Sign in")
        entered = st.text_input("Password", type="password")
        if st.form_submit_button("Unlock", type="primary", icon=":material/login:"):
            if hmac.compare_digest(entered, password):
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.error("Incorrect password.", icon=":material/error:")
    st.stop()

with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button("Lock", icon=":material/logout:"):
        st.session_state.admin_unlocked = False
        st.rerun()

st.warning(
    "Uploads are written to `portfolio/uploads/`. Streamlit Community Cloud "
    "wipes the filesystem on every restart and redeploy — commit "
    "`uploads/public/` to your repo to make public files stick. "
    "`uploads/private/` is git-ignored and stays on this machine only.",
    icon=":material/info:",
)


# ---------------------------------------------------------------------------
# Shared listing widget
# ---------------------------------------------------------------------------
def show_existing(records: list[dict], visibility: str, *, empty: str) -> None:
    """List stored files with a preview, a download and a delete control."""
    if not records:
        st.caption(empty)
        return

    for record in records:
        with st.container(border=True, key=f"card_file_{record['id']}"):
            left, right = st.columns([1, 3], gap="medium", vertical_alignment="center")

            with left:
                path = store.path_for(record, visibility)
                if path is None:
                    st.caption(":material/broken_image: file missing")
                elif record.get("is_image"):
                    st.image(str(path), width="stretch")
                else:
                    st.markdown("# :material/picture_as_pdf:")

            with right:
                st.markdown(f"**{record.get('title') or record['original_name']}**")
                meta = " · ".join(
                    str(x) for x in (
                        record.get("issuer"),
                        record.get("year"),
                        record.get("project"),
                        f"{record['size'] / (1024 * 1024):.1f} MB",
                        record["uploaded_at"][:10],
                    ) if x
                )
                st.caption(meta)
                if record.get("note"):
                    st.caption(record["note"])

                data = store.read_bytes(record, visibility)
                with st.container(horizontal=True):
                    if data is not None:
                        st.download_button(
                            "Download",
                            data=data,
                            file_name=record["original_name"],
                            icon=":material/download:",
                            key=f"dl_{record['id']}",
                        )
                    if st.button(
                        "Delete", icon=":material/delete:", key=f"rm_{record['id']}"
                    ):
                        store.delete(record["id"], visibility)
                        st.rerun()


photo_tab, resume_tab, cert_tab, project_tab, private_tab = st.tabs(
    ["Photo", "Résumé", "Certificates", "Project images", "Private documents"]
)

# ---------------------------------------------------------------------------
# Profile / passport photo
# ---------------------------------------------------------------------------
with photo_tab:
    st.subheader("Profile photo")
    st.caption(
        "A passport-style headshot works best — square, head and shoulders. "
        "The newest upload is the one the About page shows."
    )
    with st.form("upload_photo", border=True, clear_on_submit=True):
        photo = st.file_uploader(
            "Photo", type=["png", "jpg", "jpeg", "webp"], max_upload_size=MAX_MB
        )
        if st.form_submit_button(
            "Upload photo", type="primary", icon=":material/upload:"
        ):
            if photo is None:
                st.error("Choose a file first.", icon=":material/error:")
            else:
                try:
                    store.save_upload(photo, kind="headshot", title="Profile photo")
                except store.UploadError as exc:
                    st.error(str(exc), icon=":material/error:")
                else:
                    st.success("Photo uploaded.", icon=":material/check_circle:")
                    st.rerun()

    show_existing(
        store.public_records("headshot"), store.PUBLIC, empty="No photo uploaded yet."
    )

# ---------------------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------------------
with resume_tab:
    st.subheader("Résumé")
    st.caption(
        "Uploading a résumé turns on the download button on the About and "
        "Skills pages. Publish a copy with your referees' phone numbers and "
        "e-mail addresses removed — replace that section with "
        "“References available on request”."
    )
    with st.form("upload_resume", border=True, clear_on_submit=True):
        resume = st.file_uploader("Résumé (PDF)", type=["pdf"], max_upload_size=MAX_MB)
        confirmed = st.checkbox(
            "This copy contains no third-party personal contact details"
        )
        if st.form_submit_button(
            "Upload résumé", type="primary", icon=":material/upload:"
        ):
            if resume is None:
                st.error("Choose a file first.", icon=":material/error:")
            elif not confirmed:
                st.error(
                    "Tick the confirmation — the résumé becomes publicly "
                    "downloadable.",
                    icon=":material/error:",
                )
            else:
                try:
                    store.save_upload(resume, kind="resume", title="Résumé")
                except store.UploadError as exc:
                    st.error(str(exc), icon=":material/error:")
                else:
                    st.success("Résumé uploaded.", icon=":material/check_circle:")
                    st.rerun()

    show_existing(
        store.public_records("resume"), store.PUBLIC, empty="No résumé uploaded yet."
    )

# ---------------------------------------------------------------------------
# Certificates
# ---------------------------------------------------------------------------
with cert_tab:
    st.subheader("Certificates & licences")
    st.caption(
        "These appear on the Experience page, under Certifications & licences, "
        "as viewable and downloadable files."
    )
    with st.form("upload_cert", border=True, clear_on_submit=True):
        cert = st.file_uploader(
            "Certificate (PDF or image)",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            max_upload_size=MAX_MB,
        )
        cert_title = st.text_input(
            "Certificate name", placeholder="Ansys Associate — Stress Analysis"
        )
        cols = st.columns(2)
        cert_issuer = cols[0].text_input("Issuer", placeholder="Ansys")
        cert_year = cols[1].text_input("Year", placeholder="2025")
        if st.form_submit_button(
            "Upload certificate", type="primary", icon=":material/upload:"
        ):
            if cert is None:
                st.error("Choose a file first.", icon=":material/error:")
            elif not cert_title.strip():
                st.error("Give the certificate a name.", icon=":material/error:")
            else:
                try:
                    store.save_upload(
                        cert,
                        kind="certificate",
                        title=cert_title,
                        issuer=cert_issuer,
                        year=cert_year,
                    )
                except store.UploadError as exc:
                    st.error(str(exc), icon=":material/error:")
                else:
                    st.success("Certificate uploaded.", icon=":material/check_circle:")
                    st.rerun()

    show_existing(
        store.public_records("certificate"),
        store.PUBLIC,
        empty="No certificates uploaded yet.",
    )

# ---------------------------------------------------------------------------
# Project images
# ---------------------------------------------------------------------------
with project_tab:
    st.subheader("Project images")
    st.caption(
        "A screenshot or photo replaces the illustrated tile on that project's "
        "card. The newest upload per project wins."
    )
    titles = [p["title"] for p in PROJECTS]
    with st.form("upload_project", border=True, clear_on_submit=True):
        which = st.selectbox("Project", titles)
        shot = st.file_uploader(
            "Image", type=["png", "jpg", "jpeg", "webp"], max_upload_size=MAX_MB
        )
        if st.form_submit_button(
            "Upload image", type="primary", icon=":material/upload:"
        ):
            if shot is None:
                st.error("Choose a file first.", icon=":material/error:")
            else:
                try:
                    store.save_upload(
                        shot, kind="project", project=which, title=which
                    )
                except store.UploadError as exc:
                    st.error(str(exc), icon=":material/error:")
                else:
                    st.success("Image uploaded.", icon=":material/check_circle:")
                    st.rerun()

    show_existing(
        store.public_records("project"),
        store.PUBLIC,
        empty="No project images uploaded yet.",
    )

# ---------------------------------------------------------------------------
# Private documents
# ---------------------------------------------------------------------------
with private_tab:
    st.subheader("Private documents")
    st.error(
        "Never published. Files here go to `uploads/private/`, which is "
        "git-ignored, and no public page can read them. Use this for your "
        "passport, national ID, transcripts and originals you need to hand but "
        "must not put on a public site.",
        icon=":material/shield_lock:",
    )
    with st.form("upload_private", border=True, clear_on_submit=True):
        doc = st.file_uploader(
            "Document (PDF or image)",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            max_upload_size=MAX_MB,
        )
        doc_title = st.text_input("What is it?", placeholder="Passport")
        doc_note = st.text_input("Note (optional)", placeholder="Expires 2031")
        if st.form_submit_button(
            "Upload privately", type="primary", icon=":material/lock:"
        ):
            if doc is None:
                st.error("Choose a file first.", icon=":material/error:")
            elif not doc_title.strip():
                st.error("Give the document a name.", icon=":material/error:")
            else:
                try:
                    store.save_upload(
                        doc,
                        kind="document",
                        visibility=store.PRIVATE,
                        title=doc_title,
                        note=doc_note,
                    )
                except store.UploadError as exc:
                    st.error(str(exc), icon=":material/error:")
                else:
                    st.success("Stored privately.", icon=":material/check_circle:")
                    st.rerun()

    show_existing(
        store.private_records(), store.PRIVATE, empty="No private documents stored."
    )
