"""Configuration helpers for the MCP Knowledge Base server.

This module centralizes configuration lookups so that the rest of the codebase
only interacts with well-defined helper functions rather than environment
variables or default literals. Keeping configuration isolated makes the server
logic more reusable across different deployment environments because callers can
swap configurations programmatically or via environment variables without
modifying the core modules.
"""

from __future__ import annotations

from pathlib import Path
import os


DEFAULT_KNOWLEDGE_BASE_DIR = ".knowledgebase"
"""str: Default relative directory for persisting knowledge base documents."""

DATA_FOLDER_NAME = ".data"
"""str: Name of the documentation folder inside the knowledge base tree."""

DOC_FILENAME = "KNOWLEDBASE_DOC.md"
"""str: Name of the canonical documentation file advertised in the PRD."""

DELETE_SENTINEL = "_DELETE_"
"""str: Marker appended to filenames to implement soft deletion semantics."""

ENV_ROOT_KEY = "MCP_KB_ROOT"
"""str: Environment variable that overrides the knowledge base root path."""


def resolve_knowledge_base_root(provided_path: str | None = None) -> Path:
    """Return the absolute knowledge base root directory for the server.

    The function applies the following precedence order when choosing a
    directory:

    1. An explicit ``provided_path`` argument, if supplied by the caller.
    2. The ``MCP_KB_ROOT`` environment variable supplied by the host process.
    3. The default relative ``.knowledgebase`` directory.

    The returned path is always absolute and resolved, which makes subsequent
    filesystem operations robust against relative path confusion. The function
    also ensures that the directory exists by calling ``mkdir`` with
    ``parents=True`` and ``exist_ok=True`` so that repeated initializations are
    idempotent.

    Parameters
    ----------
    provided_path:
        A string path explicitly supplied by the caller. ``None`` indicates
        that the caller prefers environment or default resolution.

    Returns
    -------
    Path
        The resolved absolute path that should be used as the knowledge base
        root directory.
    """

    candidate = (
        provided_path
        or os.getenv(ENV_ROOT_KEY)
        or Path(os.getenv("WORKSPACE_FOLDER_PATHS") or Path.cwd())
        / DEFAULT_KNOWLEDGE_BASE_DIR
    )
    root_path = Path(candidate).expanduser().resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    return root_path
