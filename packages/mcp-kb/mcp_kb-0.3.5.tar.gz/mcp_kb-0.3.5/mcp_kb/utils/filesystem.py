"""Filesystem helpers wrapping Python's standard library primitives.

The knowledge base server performs numerous file operations. Consolidating the
logic in this module keeps the rest of the code focused on business semantics
such as validating incoming requests and shaping responses. Each helper function
is intentionally small so that callers can compose them for different workflows
without duplicating the low-level boilerplate.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Dict, Iterator


class FileLockRegistry:
    """In-memory lock registry to serialize write operations per file.

    Using per-path locks prevents concurrent writes from interleaving content
    and potentially corrupting files. The registry lazily creates locks when a
    path is first encountered. We reuse locks for subsequent operations to avoid
    unbounded memory usage.
    """

    def __init__(self) -> None:
        """Initialize the registry with an empty dictionary."""

        self._locks: Dict[Path, Lock] = {}
        self._global_lock = Lock()

    @contextmanager
    def acquire(self, path: Path) -> Iterator[None]:
        """Context manager that acquires a lock for the supplied path.

        The helper nests two locks: a global mutex to retrieve or create the
        per-path lock, and the per-path lock itself for the duration of the
        caller's critical section.

        Parameters
        ----------
        path:
            Absolute path indicating which file should be protected.
        """

        with self._global_lock:
            lock = self._locks.setdefault(path, Lock())
        lock.acquire()
        try:
            yield
        finally:
            lock.release()


def write_text(path: Path, content: str) -> None:
    """Write text content to ``path`` using UTF-8 encoding."""

    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    """Append text content to ``path`` using UTF-8 encoding."""

    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def read_text(path: Path) -> str:
    """Read UTF-8 text content from ``path`` and return it."""

    return path.read_text(encoding="utf-8")


def ensure_parent_directory(path: Path) -> None:
    """Ensure the parent directory of ``path`` exists by creating it."""

    path.parent.mkdir(parents=True, exist_ok=True)


def rename(path: Path, target: Path) -> None:
    """Rename ``path`` to ``target`` using ``Path.rename`` semantics."""

    path.rename(target)


def is_text_file(path: Path, max_bytes: int = 2048) -> bool:
    """Heuristically determine whether ``path`` contains UTF-8 text.

    The check is designed to be fast and conservative for use when iterating
    a directory tree. It reads at most ``max_bytes`` from the file in binary
    mode and applies two filters:

    - Reject files that contain NUL bytes, which are extremely uncommon in
      textual formats and a strong indicator of binary content.
    - Attempt to decode the sampled bytes as UTF-8. If decoding fails, the
      file is treated as binary.

    Parameters
    ----------
    path:
        Absolute path to the file on disk.
    max_bytes:
        Upper bound on the number of bytes to sample from the head of the
        file. A small sample keeps directory scans fast while remaining
        accurate for typical text formats such as ``.md``, ``.txt``, ``.xml``,
        and source files.

    Returns
    -------
    bool
        ``True`` if the file appears to be UTF-8 text; ``False`` otherwise.
    """

    try:
        with path.open("rb") as handle:
            sample = handle.read(max_bytes)
    except (FileNotFoundError, PermissionError):  # pragma: no cover - defensive
        return False

    if b"\x00" in sample:
        return False

    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
