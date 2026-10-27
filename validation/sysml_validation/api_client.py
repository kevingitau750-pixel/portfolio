"""Clients for the SysML v2 API Services (the authoritative reference side).

The reference workflow is: ``make spin-up`` starts the SysML v2 API Services
server, the model is published to it from the Jupyter notebook, and the model
then lives under a *project* and a *commit*. Elements are retrieved with::

    GET /projects/{projectId}/commits/{commitId}/elements

Each element is a JSON object carrying at least ``@id``, ``@type`` and (for named
elements) ``name``; containment is read from the derived ``owner`` reference.

Two clients implement the same :class:`SysMLv2Client` protocol:

* :class:`RestClient` talks to a running server over HTTP (stdlib only).
* :class:`InMemoryClient` serves a pre-loaded list of elements, so the whole
  pipeline is testable without Docker.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Protocol, Sequence, runtime_checkable

Element = Dict[str, Any]


@runtime_checkable
class SysMLv2Client(Protocol):
    """Minimal surface the validator needs from the reference implementation."""

    def list_projects(self) -> List[Element]:
        """Return the projects known to the server."""
        ...

    def list_commits(self, project_id: str) -> List[Element]:
        """Return the commits of a project, newest first where available."""
        ...

    def list_elements(self, project_id: str, commit_id: str) -> List[Element]:
        """Return every element in a commit (the full parsed model)."""
        ...


class RestClient:
    """Talk to a live SysML v2 API Services server.

    Parameters
    ----------
    base_url:
        e.g. ``http://localhost:9000``. This is the server ``make spin-up``
        brings up; run Docker on a capable machine and pass its URL here.
    page_size:
        The API paginates with ``?page[size]=`` and a ``Link`` header; we follow
        ``rel="next"`` until exhausted.
    timeout:
        Per-request timeout in seconds.
    """

    def __init__(
        self, base_url: str, *, page_size: int = 500, timeout: float = 30.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self.timeout = timeout

    # -- low level ---------------------------------------------------------
    def _get(self, path: str, query: Dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
            link = resp.headers.get("Link", "")
        return json.loads(body), link

    @staticmethod
    def _next_link(link_header: str) -> str | None:
        """Parse an RFC 5988 ``Link`` header for the ``rel="next"`` URL."""
        for part in link_header.split(","):
            segments = part.split(";")
            if len(segments) < 2:
                continue
            raw_url = segments[0].strip().strip("<>")
            if any('rel="next"' in s.replace(" ", "") or "rel=next" in s for s in segments[1:]):
                return raw_url
        return None

    def _get_all(self, path: str) -> List[Element]:
        """GET a paginated collection, following ``rel="next"`` to the end."""
        items: List[Element] = []
        data, link = self._get(path, {"page[size]": self.page_size})
        items.extend(data if isinstance(data, list) else [data])
        next_url = self._next_link(link)
        while next_url:
            req = urllib.request.Request(
                next_url, headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                page = json.loads(resp.read().decode("utf-8"))
                link = resp.headers.get("Link", "")
            items.extend(page if isinstance(page, list) else [page])
            next_url = self._next_link(link)
        return items

    # -- protocol ----------------------------------------------------------
    def list_projects(self) -> List[Element]:
        return self._get_all("/projects")

    def list_commits(self, project_id: str) -> List[Element]:
        return self._get_all(f"/projects/{project_id}/commits")

    def list_elements(self, project_id: str, commit_id: str) -> List[Element]:
        return self._get_all(
            f"/projects/{project_id}/commits/{commit_id}/elements"
        )


class InMemoryClient:
    """Serve a fixed set of elements — the mock used for local development.

    ``elements`` is the flat list of element dicts for a single commit, in the
    same JSON shape the real API returns.
    """

    def __init__(
        self,
        elements: Sequence[Element],
        *,
        project_id: str = "mock-project",
        commit_id: str = "mock-commit",
    ) -> None:
        self._elements = list(elements)
        self.project_id = project_id
        self.commit_id = commit_id

    @classmethod
    def from_json_file(cls, path: str, **kwargs: Any) -> "InMemoryClient":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # Accept either a bare list or {"elements": [...]}.
        elements = data["elements"] if isinstance(data, dict) else data
        return cls(elements, **kwargs)

    def list_projects(self) -> List[Element]:
        return [{"@id": self.project_id, "name": "mock"}]

    def list_commits(self, project_id: str) -> List[Element]:
        return [{"@id": self.commit_id}]

    def list_elements(self, project_id: str, commit_id: str) -> List[Element]:
        return list(self._elements)
