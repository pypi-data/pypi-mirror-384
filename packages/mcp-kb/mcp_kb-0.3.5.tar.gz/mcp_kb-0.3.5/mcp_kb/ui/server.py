"""Lightweight HTTP server that hosts the human UI and JSON endpoints.

The implementation uses :mod:`http.server` from the Python standard library to
avoid adding web framework dependencies. Static assets are loaded from package
resources, while dynamic endpoints call into a shared
:class:`~mcp_kb.knowledge.store.KnowledgeBase` instance.
"""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar, Optional
from urllib.parse import parse_qs, urlparse

from importlib import resources
import logging
from mcp_kb.knowledge.store import KnowledgeBase

from .api import (
    build_tree_json,
    read_file_json,
    write_file,
    search_json,
    vector_status_json,
    vector_embeddings_json,
    vector_query_embedding_json,
    vector_reindex_json,
    vector_refit_json,
)


logger = logging.getLogger(__name__)

class _UIRequestHandler(BaseHTTPRequestHandler):
    """Request handler serving the web UI and API endpoints.

    The handler reads assets from ``mcp_kb.ui.assets`` and forwards JSON API
    requests to the injected knowledge base instance. An instance is attached
    to the handler class at server startup via ``kb``.
    """

    kb: ClassVar[Optional[KnowledgeBase]] = None

    # Silence default log output; the main process already logs startup info
    def log_message(self, format: str, *args) -> None:  # pragma: no cover - noise
        return

    def do_GET(self) -> None:  # noqa: N802 - HTTP verb name
        """Serve the index page, static assets, or a JSON read endpoint."""

        assert self.kb is not None, "UI server not initialized with a KnowledgeBase"
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._serve_asset("index.html", content_type="text/html; charset=utf-8")
            return
        if parsed.path.startswith("/static/"):
            name = parsed.path.split("/static/", 1)[1]
            ctype = (
                "text/javascript; charset=utf-8" if name.endswith(".js") else
                "text/css; charset=utf-8" if name.endswith(".css") else
                "application/octet-stream"
            )
            self._serve_asset(name, content_type=ctype)
            return
        if parsed.path == "/api/tree":
            body = json.dumps(build_tree_json(self.kb)).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return
        if parsed.path == "/api/file":
            params = parse_qs(parsed.query)
            rel_path = params.get("path", [""])[0]
            try:
                payload = read_file_json(self.kb, rel_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(exc)
                self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            body = json.dumps(payload.model_dump()).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return
        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            query = params.get("query", [""])[0]
            if not query:
                body = json.dumps([]).encode("utf-8")
                self._send_response(HTTPStatus.OK, body, "application/json")
                return
            limit_raw = params.get("limit", params.get("n", [None]))[0]
            limit = None
            if limit_raw is not None:
                try:
                    limit = max(1, int(limit_raw))
                except ValueError:
                    self._send_error(HTTPStatus.BAD_REQUEST, "Invalid limit value")
                    return
            try:
                results = search_json(self.kb, query, limit=limit)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(exc)
                self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            body = json.dumps(results).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return

        if parsed.path == "/api/vector/status":
            body = json.dumps(vector_status_json(self.kb)).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return

        if parsed.path == "/api/vector/embeddings":
            params = parse_qs(parsed.query)
            try:
                raw_limit = params.get("limit", ["1000"])[0]
                raw_offset = params.get("offset", ["0"])[0]
                limit = max(1, int(raw_limit))
                offset = max(0, int(raw_offset))
            except ValueError:
                self._send_error(HTTPStatus.BAD_REQUEST, "Invalid limit/offset value")
                return
            path = params.get("path", [None])[0]
            try:
                results = vector_embeddings_json(self.kb, limit=limit, offset=offset, path=path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(exc)
                self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            body = json.dumps(results).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return

        if parsed.path == "/api/vector/query_embedding":
            params = parse_qs(parsed.query)
            query = params.get("query", [""])[0]
            if not query:
                body = json.dumps({"embedding": [], "used_model": None}).encode("utf-8")
                self._send_response(HTTPStatus.OK, body, "application/json")
                return
            result = vector_query_embedding_json(self.kb, query)
            body = json.dumps(result).encode("utf-8")
            self._send_response(HTTPStatus.OK, body, "application/json")
            return

        self._send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_PUT(self) -> None:  # noqa: N802 - HTTP verb name
        """Handle file save requests at ``/api/file`` with JSON payloads."""

        assert self.kb is not None, "UI server not initialized with a KnowledgeBase"
        parsed = urlparse(self.path)
        if parsed.path != "/api/file":
            self._send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        try:
            content_len = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error(HTTPStatus.LENGTH_REQUIRED, "Content-Length required")
            return
        raw = self.rfile.read(content_len)
        try:
            payload = json.loads(raw.decode("utf-8"))
            path = payload["path"]
            content = payload.get("content", "")
            write_file(self.kb, path, content)
        except KeyError:
            logger.exception(exc)
            self._send_error(HTTPStatus.BAD_REQUEST, "Missing 'path' in JSON body")
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(exc)
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_response(HTTPStatus.NO_CONTENT, b"", "application/json")

    def do_POST(self) -> None:  # noqa: N802 - HTTP verb name
        """Handle administrative vector actions exposed via POST endpoints."""

        assert self.kb is not None, "UI server not initialized with a KnowledgeBase"
        parsed = urlparse(self.path)
        if parsed.path == "/api/vector/reindex":
            try:
                payload = vector_reindex_json(self.kb)
                body = json.dumps(payload).encode("utf-8")
                self._send_response(HTTPStatus.OK, body, "application/json")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(exc)
                self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        if parsed.path == "/api/vector/refit":
            try:
                payload = vector_refit_json(self.kb)
                body = json.dumps(payload).encode("utf-8")
                self._send_response(HTTPStatus.OK, body, "application/json")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(exc)
                self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_DELETE(self) -> None:  # noqa: N802 - HTTP verb name
        """Soft delete the requested file using ``kb.soft_delete``.

        Endpoint: ``DELETE /api/file?path=...``
        Returns ``204 No Content`` on success or ``400`` when validation fails.
        """

        assert self.kb is not None, "UI server not initialized with a KnowledgeBase"
        parsed = urlparse(self.path)
        if parsed.path != "/api/file":
            self._send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        params = parse_qs(parsed.query)
        rel_path = params.get("path", [""])[0]
        try:
            self.kb.soft_delete(rel_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(exc)
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_response(HTTPStatus.NO_CONTENT, b"", "application/json")

    def _serve_asset(self, name: str, *, content_type: str) -> None:
        """Serve an embedded static asset by ``name`` with ``content_type``."""

        try:
            data = resources.files("mcp_kb.ui.assets").joinpath(name).read_bytes()
        except FileNotFoundError:
            self._send_error(HTTPStatus.NOT_FOUND, "Asset not found")
            return
        self._send_response(HTTPStatus.OK, data, content_type)

    def _send_response(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        """Write an HTTP response with headers and body."""

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        """Return a JSON error payload with ``status`` and ``message``."""

        payload = json.dumps({"error": message}).encode("utf-8")
        self._send_response(status, payload, "application/json")


DEFAULT_UI_PORT = 8765


class UIServer:
    """Container managing the lifecycle of the UI HTTP server.

    The server binds in a background thread so it can run alongside the MCP
    transports. Call :meth:`stop` to shut it down from tests or other code.
    By default, the server attempts to bind to :data:`DEFAULT_UI_PORT` and will
    increment by one until a free port is found. Callers can provide a
    ``port`` to override the starting point.
    """

    def __init__(self, kb: KnowledgeBase, host: str = "127.0.0.1", port: int | None = None) -> None:
        """Create a server bound to ``host:port`` serving ``kb``.

        Binding strategy
        ----------------
        - When ``port`` is ``None``, the server starts scanning from
          :data:`DEFAULT_UI_PORT`.
        - When ``port`` is provided, scanning starts from that value.
        - On conflict (address already in use), the server increments the port
          by one and retries until successful.
        """

        _UIRequestHandler.kb = kb
        start = DEFAULT_UI_PORT if port is None else port
        bound = None
        last_error: Exception | None = None
        for candidate in range(start, start + 200):
            try:
                httpd = ThreadingHTTPServer((host, candidate), _UIRequestHandler)
            except OSError as exc:  # port in use or permission error
                last_error = exc
                continue
            else:
                bound = (candidate, httpd)
                break
        if bound is None:
            raise RuntimeError(
                f"Failed to bind UI server on {host}:{start}-{start+199}: {last_error}"
            )
        self._httpd = bound[1]
        self.host = host
        self.port = bound[0]
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a daemon thread."""

        def _target() -> None:
            self._httpd.serve_forever(poll_interval=0.5)

        self._thread = threading.Thread(target=_target, name="kb-ui", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Shutdown the server and wait for the thread to exit."""

        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)


def start_ui_server(kb: KnowledgeBase, host: str = "127.0.0.1", port: int | None = None) -> UIServer:
    """Start and return a :class:`UIServer` bound to ``host:port`` for ``kb``.

    When ``port`` is ``None`` the server tries :data:`DEFAULT_UI_PORT` and
    increments until an available port is found.
    """

    srv = UIServer(kb, host=host, port=port)
    srv.start()
    return srv


__all__ = [
    "UIServer",
    "start_ui_server",
]
