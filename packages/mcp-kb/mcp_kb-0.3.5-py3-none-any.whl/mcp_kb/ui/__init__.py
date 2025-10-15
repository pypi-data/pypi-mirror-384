"""Human-accessible UI for browsing and editing the knowledge base.

This package exposes a tiny HTTP server using Python's standard library so we
avoid introducing new runtime dependencies. The server mounts a minimal web UI
with a menu bar and a "Browse" view that renders a file tree and a simple text
editor. Changes are persisted via the same :class:`~mcp_kb.knowledge.store.KnowledgeBase`
instance as the MCP server, ensuring that all registered listeners and
triggers execute uniformly regardless of the entry point.
"""

from __future__ import annotations

__all__ = [
    "start_ui_server",
]

from .server import start_ui_server
