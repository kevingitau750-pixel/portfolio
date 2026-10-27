"""A tiny HTTP mock of the SysML v2 API Services, for local end-to-end runs.

It serves just enough of the real API for the validator:

* ``GET /projects``
* ``GET /projects/{id}/commits``
* ``GET /projects/{id}/commits/{cid}/elements``  (paginated with a Link header)

Run it::

    python -m sysml_validation.mock_server examples/sample_model.json --port 9000

then point the CLI at ``--api-url http://localhost:9000``. This exists so the
``RestClient`` path is exercisable without Docker; the real server replaces it
unchanged.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, List, Tuple
from urllib.parse import parse_qs, urlparse

PROJECT_ID = "mock-project"
COMMIT_ID = "mock-commit"


def _load_elements(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data["elements"] if isinstance(data, dict) else data


def make_handler(elements: List[dict]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:  # quiet
            pass

        def _send(self, payload: Any, link: str | None = None) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if link:
                self.send_header("Link", link)
            self.end_headers()
            self.wfile.write(body)

        def _not_found(self) -> None:
            self.send_response(404)
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split("/") if p]
            qs = parse_qs(parsed.query)

            if parts == ["projects"]:
                self._send([{"@id": PROJECT_ID, "name": "LunarLander"}])
            elif parts[:1] == ["projects"] and parts[2:] == ["commits"]:
                self._send([{"@id": COMMIT_ID}])
            elif (
                len(parts) == 5
                and parts[0] == "projects"
                and parts[2] == "commits"
                and parts[4] == "elements"
            ):
                page, link = self._page(elements, qs)
                self._send(page, link)
            else:
                self._not_found()

        def _page(self, items: List[dict], qs: dict) -> Tuple[List[dict], str | None]:
            size = int(qs.get("page[size]", ["500"])[0])
            after = int(qs.get("page[after]", ["0"])[0])
            chunk = items[after : after + size]
            nxt = after + size
            link = None
            if nxt < len(items):
                base = f"http://{self.headers.get('Host')}{urlparse(self.path).path}"
                link = f'<{base}?page[size]={size}&page[after]={nxt}>; rel="next"'
            return chunk, link

    return Handler


def serve(path: str, host: str = "127.0.0.1", port: int = 9000) -> None:
    elements = _load_elements(path)
    httpd = ThreadingHTTPServer((host, port), make_handler(elements))
    print(f"mock SysML v2 API on http://{host}:{port} ({len(elements)} elements)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


def main(argv: Any = None) -> int:
    p = argparse.ArgumentParser(description="Mock SysML v2 API Services")
    p.add_argument("model", help="path to a model JSON")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9000)
    args = p.parse_args(argv)
    serve(args.model, args.host, args.port)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
