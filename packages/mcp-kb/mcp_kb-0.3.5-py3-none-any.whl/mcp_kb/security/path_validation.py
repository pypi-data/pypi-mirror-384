"""Path validation utilities to protect the knowledge base filesystem.

This module implements reusable helpers that ensure every file operation stays
inside the configured knowledge base root. The checks defend against directory
traversal attempts (".." components), accidental absolute paths, and writes
that target the reserved documentation folder. The helper functions are written
so they can be reused both by the server runtime and by unit tests to keep the
security rules consistent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from pydantic import BaseModel

from mcp_kb.config import DATA_FOLDER_NAME, DELETE_SENTINEL


class PathValidationError(ValueError):
    """Error raised when a path fails validation rules.

    The server treats any instance of this exception as a client error: callers
    attempted to access a disallowed path. Raising a dedicated subclass of
    ``ValueError`` enables precise error handling and cleaner unit tests.
    """


class PathRules(BaseModel):
    """Container for server-specific path constraints.

    Attributes
    ----------
    root:
        Absolute path that represents the root of the knowledge base. All file
        operations must remain inside this directory tree.
    protected_folders:
        Iterable of folder names that are protected against mutations. The
        server uses this to forbid modifications to the documentation folder
        while still allowing read operations.
    """
    root: Path
    protected_folders: Iterable[str]


def normalize_path(candidate: Union[str, Path], rules: PathRules) -> Path:
    """Normalize a relative path and ensure it stays inside the root.

    Parameters
    ----------
    candidate:
        The user-provided path, typically originating from an MCP tool request.
    rules:
        The active ``PathRules`` instance describing allowed operations.

    Returns
    -------
    Path
        A fully-resolved path that is guaranteed to be inside the root
        directory.

    Raises
    ------
    PathValidationError
        If the candidate path is absolute, attempts traversal outside the root,
        or resolves to a location that is not within the permitted tree.
    """

    path_obj = Path(candidate)
    if path_obj.is_absolute():
        raise PathValidationError(
            "Absolute paths are not permitted inside the knowledge base"
        )

    normalized = (rules.root / path_obj).resolve()
    try:
        normalized.relative_to(rules.root)
    except ValueError as exc:
        raise PathValidationError(
            "Path resolves outside the knowledge base root"
        ) from exc

    if DELETE_SENTINEL in normalized.name:
        raise PathValidationError("Operations on soft-deleted files are not permitted")

    return normalized


def ensure_write_allowed(path: Path, rules: PathRules) -> None:
    """Validate that a path resides outside protected folders before writing.

    The function raises a ``PathValidationError`` when the path is located
    inside one of the configured protected folders. Read operations can still
    access those directories by skipping this check.

    Parameters
    ----------
    path:
        The already-normalized absolute path that will be used for writing.
    rules:
        The active ``PathRules`` instance describing allowed operations.
    """

    relative_parts = path.relative_to(rules.root).parts
    if relative_parts and relative_parts[0] in set(rules.protected_folders):
        raise PathValidationError(
            f"Writes are not allowed inside the protected folder '{relative_parts[0]}'"
        )
