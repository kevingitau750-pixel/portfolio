"""Upload store for photos, the resume, certificates and private documents.

Two completely separate stores, each with its own folder and its own index:

    uploads/public/    index.json + files  -> may be rendered on the site
    uploads/private/   index.json + files  -> NEVER rendered on the site

The split is structural, not a flag on a shared list: a public page cannot
reach a private record even by mistake, because ``public_records()`` only ever
opens the public index. ``uploads/private/`` is git-ignored, so private
documents are never committed or deployed.

Stored filenames are generated (``<uuid>.<ext>``); the original name is kept in
the index as metadata only. Nothing derived from user input reaches the
filesystem, so a crafted filename cannot escape the upload folder.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
PUBLIC_DIR = UPLOAD_ROOT / "public"
PRIVATE_DIR = UPLOAD_ROOT / "private"

PUBLIC = "public"
PRIVATE = "private"

# What each upload is for. Public pages query by kind.
KINDS = ("headshot", "resume", "certificate", "project", "document")

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_SUFFIXES = IMAGE_SUFFIXES | {".pdf"}
_MB = 1024 * 1024
MAX_BYTES = 15 * _MB  # 15 MB per file


class UploadError(Exception):
    """Raised for a rejected upload; the message is safe to show the user."""


# ---------------------------------------------------------------------------
# Index handling
# ---------------------------------------------------------------------------
def _dir(visibility: str) -> Path:
    if visibility not in (PUBLIC, PRIVATE):
        raise ValueError(f"unknown visibility: {visibility!r}")
    return PUBLIC_DIR if visibility == PUBLIC else PRIVATE_DIR


def _index_path(visibility: str) -> Path:
    return _dir(visibility) / "index.json"


def _read_index(visibility: str) -> list[dict[str, Any]]:
    path = _index_path(visibility)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _write_index(visibility: str, records: list[dict[str, Any]]) -> None:
    directory = _dir(visibility)
    directory.mkdir(parents=True, exist_ok=True)
    _index_path(visibility).write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
def save_upload(
    uploaded_file,
    *,
    kind: str,
    visibility: str = PUBLIC,
    title: str = "",
    issuer: str = "",
    year: str = "",
    project: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Validate and store one ``st.file_uploader`` result. Returns its record."""
    if kind not in KINDS:
        raise UploadError(f"Unknown upload kind: {kind}")

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(s.lstrip(".") for s in ALLOWED_SUFFIXES))
        raise UploadError(f"{suffix or 'That file type'} is not allowed. Use: {allowed}.")

    data = uploaded_file.getvalue()
    if not data:
        raise UploadError("That file is empty.")
    if len(data) > MAX_BYTES:
        raise UploadError(
            f"That file is {len(data) / _MB:.1f} MB — the limit is "
            f"{MAX_BYTES / _MB:.0f} MB."
        )

    directory = _dir(visibility)
    directory.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    (directory / stored_name).write_bytes(data)

    record = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "stored_name": stored_name,
        "original_name": Path(uploaded_file.name).name,
        "title": title.strip(),
        "issuer": issuer.strip(),
        "year": str(year).strip(),
        "project": project.strip(),
        "note": note.strip(),
        "size": len(data),
        "is_image": suffix in IMAGE_SUFFIXES,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    records = _read_index(visibility)
    records.append(record)
    _write_index(visibility, records)
    return record


def delete(record_id: str, visibility: str) -> bool:
    """Remove a record and its file. Returns True if something was deleted."""
    records = _read_index(visibility)
    keep = [r for r in records if r.get("id") != record_id]
    if len(keep) == len(records):
        return False

    gone = next(r for r in records if r.get("id") == record_id)
    target = _dir(visibility) / gone["stored_name"]
    # Guard against an index entry that points outside the upload folder.
    if target.parent == _dir(visibility) and target.exists():
        target.unlink()
    _write_index(visibility, keep)
    return True


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def public_records(kind: str | None = None) -> list[dict[str, Any]]:
    """Public uploads, newest first. This is the ONLY reader public pages use."""
    records = [r for r in _read_index(PUBLIC) if kind is None or r.get("kind") == kind]
    return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)


def private_records(kind: str | None = None) -> list[dict[str, Any]]:
    """Private uploads. Only the password-gated admin page may call this."""
    records = [r for r in _read_index(PRIVATE) if kind is None or r.get("kind") == kind]
    return sorted(records, key=lambda r: r.get("uploaded_at", ""), reverse=True)


def path_for(record: dict[str, Any], visibility: str = PUBLIC) -> Path | None:
    """Absolute path of a record's file, or None if the file has gone missing."""
    path = _dir(visibility) / record["stored_name"]
    return path if path.exists() else None


def latest_public(kind: str) -> dict[str, Any] | None:
    """Most recent public upload of a kind — used for the headshot and resume."""
    found = public_records(kind)
    return found[0] if found else None


def read_bytes(record: dict[str, Any], visibility: str = PUBLIC) -> bytes | None:
    path = path_for(record, visibility)
    return path.read_bytes() if path else None


def project_image(project_title: str) -> Path | None:
    """Public image uploaded against a given project title, if any."""
    for record in public_records("project"):
        if record.get("project", "").strip().lower() == project_title.strip().lower():
            return path_for(record)
    return None
