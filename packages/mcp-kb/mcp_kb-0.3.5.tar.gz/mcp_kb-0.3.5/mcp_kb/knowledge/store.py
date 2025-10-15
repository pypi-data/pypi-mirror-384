"""Core knowledge base operations for file lifecycle management.

This module exposes the ``KnowledgeBase`` class, which orchestrates validated
filesystem operations for the MCP server. The class encapsulates logic for
creating, reading, appending, and modifying text files while respecting the
security constraints defined in the PRD. Each method returns plain Python data
structures so that higher-level layers (e.g., JSON-RPC handlers) can focus on
protocol serialization rather than filesystem minutiae.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional, Union, Sequence, Dict, List, Literal, Any

from mcp_kb.config import DELETE_SENTINEL, DATA_FOLDER_NAME
from mcp_kb.knowledge.events import (
    FileDeleteEvent,
    FileUpsertEvent,
    KnowledgeBaseListener,
)
from mcp_kb.knowledge.metadata import KnowledgeBaseMetadata, normalize_tags
from mcp_kb.security.path_validation import (
    PathRules,
    ensure_write_allowed,
    normalize_path,
)
from mcp_kb.utils.filesystem import (
    FileLockRegistry,
    append_text,
    ensure_parent_directory,
    read_text,
    rename,
    write_text,
)


from pydantic import BaseModel, model_validator


class FileSegment(BaseModel):
    """Represents a snippet of file content returned to MCP clients.

    The model captures a ``path``  (relative to the knowledge base root) 
    along with one-based ``start_line`` and ``end_line`` indices and the 
    extracted text ``content``. Using a Pydantic model makes structured output and
    validation consistent across API layers.
    """

    path: str
    start_line: int
    end_line: int
    content: str

    @model_validator(mode="before")
    @classmethod
    def check_path(cls, values: dict) -> dict:
        if isinstance(values["path"], Path):
            values["path"] = str(values["path"])
        return values

    def assert_path(self,rules: PathRules) -> None:
        rel_path = Path(self.path)
        if not rel_path.is_absolute():
            abspath = rules.root / rel_path
        else:
            abspath = rel_path
        # make sure the relative path is inside the knowledge base root
        if not abspath.is_relative_to(rules.root):
            raise ValueError(f"Relative path {rel_path} is not in the knowledge base root")
        # make sure the relative path is not in the protected folders
        self.path = str(abspath.relative_to(rules.root))


class KnowledgeBase:
    """High-level API that executes validated knowledge base operations.

    The class is intentionally stateless aside from the path rules and lock
    registry. Stateless methods make this component easy to reuse across tests
    and potential future transports. Locking responsibilities are scoped to the
    knowledge base to keep write safety consistent across entry points.
    """

    def __init__(
        self,
        rules: PathRules,
        lock_registry: FileLockRegistry | None = None,
        listeners: Iterable[KnowledgeBaseListener] | None = None,
        metadata: KnowledgeBaseMetadata | None = None,
    ) -> None:
        """Initialize the knowledge base with path rules and optional locks.

        Parameters
        ----------
        rules:
            Active path rules that govern which paths are safe to touch.
        lock_registry:
            Optional ``FileLockRegistry`` allowing tests to inject deterministic
            locking behavior. A new registry is created when omitted.
        listeners:
            Optional iterable of callback objects that subscribe to change
            events. Each listener must implement the
            :class:`~mcp_kb.knowledge.events.KnowledgeBaseListener` protocol.
            Events are dispatched synchronously after filesystem operations
            succeed, which allows callers to maintain eventual consistency with
            external systems such as vector databases.
        metadata:
            Optional metadata catalogue that should mirror the knowledge base
            contents. A default :class:`~mcp_kb.knowledge.metadata.KnowledgeBaseMetadata`
            instance is created when omitted. The catalogue is synchronised with
            the current filesystem state during initialization.
        """

        self.rules = rules
        self.locks = lock_registry or FileLockRegistry()
        self.listeners = tuple(listeners or ())
        self.metadata = metadata or KnowledgeBaseMetadata(self.rules.root)
        self._synchronise_metadata()

    def _synchronise_metadata(self) -> None:
        """Rebuild the metadata index so it mirrors the on-disk documents.

        The method enumerates every active document that falls outside the
        protected folders, reads its content, and updates the metadata catalogue
        with the latest structural information.  Stale entries for deleted files
        are purged during the same pass, which keeps ``database.json`` aligned
        with the canonical filesystem state even when the server restarts.
        """

        files: dict[str, Path] = {}
        for path in self.iter_active_files(include_docs=False):
            files[self._path(path)] = path
        self.metadata.sync_with_files(files)

    def create_file(
        self,
        path: Union[str, Path],
        content: str,
        *,
        tags: Optional[Iterable[str]] = None,
    ) -> Path:
        """Create or overwrite a text file at ``path`` and persist metadata.

        Parameters
        ----------
        path:
            Relative or absolute path identifying the document within the
            knowledge base root.
        content:
            UTF-8 text that should replace the document contents.
        tags:
            Optional iterable of explicit metadata tags that will be stored in
            ``database.json`` alongside heuristically extracted tags. Omitted
            values reuse any prior explicit tags for the file.
        """

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        ensure_parent_directory(normalized)
        with self.locks.acquire(normalized):
            write_text(normalized, content)
        self._notify_upsert(self._path(normalized), content, tags=tags,clear_tags=True)
        return normalized

    def read_file(
        self,
        path: Union[str, Path],
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> FileSegment:
        """Read content from ``path`` optionally constraining lines.

        Parameters
        ----------
        path:
            Target file path relative to the knowledge base root.
        start_line:
            Zero-   based index for the first line to include. ``None`` means start
            from the beginning of the file.
        end_line:
            Zero-based index signaling the last line to include. ``None`` means
            include content through the end of the file.
        """

        normalized = normalize_path(path, self.rules)
        full_content = read_text(normalized)
        lines = full_content.splitlines()

        if start_line is None and end_line is None:
            segment_content = full_content
            actual_start = 0
            actual_end = len(lines)-1
        else:
            actual_start = start_line or 0
            actual_end = end_line or len(lines)-1
            if actual_start < 0 or actual_end < actual_start:
                raise ValueError("Invalid line interval requested")
            selected = lines[actual_start : actual_end + 1]
            segment_content = "\n".join(selected)

        return FileSegment(
            path=normalized,
            start_line=actual_start,
            end_line=actual_end,
            content=segment_content,
        )

    def append_file(
        self,
        path: Union[str, Path],
        content: str,
        *,
        tags: Optional[Iterable[str]] = None,
    ) -> Path:
        """Append ``content`` to ``path`` and refresh metadata.

        Parameters
        ----------
        path:
            Relative or absolute path of the target document.
        content:
            UTF-8 payload that should be appended to the file.
        tags:
            Optional iterable extending the explicit tag list stored in
            ``database.json``. Passing ``None`` preserves any existing explicit
            tags while recomputing derived tags from the new content.
        """

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        ensure_parent_directory(normalized)
        with self.locks.acquire(normalized):
            if not normalized.exists():
                write_text(normalized, content)
            else:
                append_text(normalized, content)
        updated_text = read_text(normalized)
        self._notify_upsert(self._path(normalized), updated_text, tags=tags,clear_tags=False)
        return normalized

    def regex_replace(self, path: Union[str, Path], pattern: str, replacement: str) -> int:
        """Perform regex replacement and return the number of substitutions."""

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        with self.locks.acquire(normalized):
            text = read_text(normalized)
            new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
            write_text(normalized, new_text)
        self._notify_upsert(self._path(normalized), new_text,clear_tags=False)
        return count

    def soft_delete(self, path: Union[str, Path]) -> Path:
        """Apply soft deletion semantics by appending the deletion sentinel."""

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        if not normalized.exists():
            raise FileNotFoundError(f"File '{path}' does not exist")

        target_name = f"{normalized.stem}{DELETE_SENTINEL}{normalized.suffix}"
        target = normalized.with_name(target_name)
        ensure_write_allowed(target, self.rules)
        with self.locks.acquire(normalized):
            rename(normalized, target)
        original_relative = self._path(normalized)
        self._notify_delete(original_relative)
        return target

    def total_active_files(self, include_docs: bool = False) -> int:
        """Return the total number of non-deleted UTF-8 text files under the root directory."""
        return sum(1 for _ in self.iter_active_files(include_docs=include_docs))

    def iter_active_files(self, include_docs: bool = False) -> Iterable[Path]:
        """Yield non-deleted UTF-8 text files under the root directory.

        Parameters
        ----------
        include_docs:
            When ``True`` the generator includes files located in the protected
            documentation folder. By default those files are skipped to match
            the search and overview requirements from the PRD.
        """

        from mcp_kb.utils.filesystem import is_text_file

        for path in self.rules.root.rglob("*"):
            if not path.is_file():
                continue
            if DELETE_SENTINEL in path.name:
                continue
            parts = path.relative_to(self.rules.root).parts
            if parts and parts[0] == DATA_FOLDER_NAME and not include_docs:
                continue
            if is_text_file(path):
                yield path

    def _path(self, absolute: Path) -> str:
        """Return ``absolute`` rewritten relative to the knowledge base root."""

        return str(absolute.relative_to(self.rules.root))

    def _notify_upsert(
        self,
        relative: str,
        content: str,
        *,
        tags: Optional[Iterable[str]] = None,
        clear_tags: bool = False,
    ) -> None:
        """Dispatch an upsert event and persist metadata for ``relative``.

        Parameters
        ----------
        relative:
            Path relative to the knowledge base root that was modified.
        content:
            Normalised document text written to disk.
        tags:
            Optional iterable of explicit tags extending the previous explicit tag list. ``None``
            preserves the previous explicit tag list, whereas an empty iterable
            clears it.
        """

        explicit_tags = normalize_tags(tags) if tags is not None else None
        self.metadata.update_document(relative, content, explicit_tags=explicit_tags,clear_tags=clear_tags)

        if not self.listeners:
            return

        event = FileUpsertEvent(
            path=relative,
            content=content,
        )
        self._dispatch("handle_upsert", event)

    def _notify_delete(self,relative: str) -> None:
        """Dispatch a delete event to registered listeners."""

        self.metadata.remove_document(relative)

        if not self.listeners:
            return

        event = FileDeleteEvent(path=relative)
        self._dispatch("handle_delete", event)

    def add_tags(self, path: Union[str, Path], tags: Sequence[str]) -> Path:
        """Attach additional explicit tags to the document at ``path``.

        Parameters
        ----------
        path:
            Relative or absolute path identifying the document to enrich.
        tags:
            Sequence of tag strings that should be merged with the existing
            explicit tag list. Blank strings are ignored and duplicates are
            removed. At least one non-empty tag is required.
        """

        if not tags:
            raise ValueError("tags must contain at least one value")

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        if not normalized.exists():
            raise FileNotFoundError(f"File '{path}' does not exist")

        with self.locks.acquire(normalized):
            content = read_text(normalized)

        relative = self._path(normalized)
        existing = self.metadata.get_entry(relative) or {}
        current_explicit = normalize_tags(existing.get("explicit_tags", []))
        merged = normalize_tags(list(current_explicit) + list(tags))
        self.metadata.update_document(relative, content, explicit_tags=merged,clear_tags=False)
        return normalized

    def remove_tags(self, path: Union[str, Path], tags: Sequence[str]) -> Path:
        """Remove explicit tags from the document at ``path`` when present.

        Parameters
        ----------
        path:
            Relative or absolute path identifying the document to update.
        tags:
            Sequence of tag labels to delete from the explicit tag list. Missing
            labels are ignored. All supplied values must be non-empty strings.
        """

        if not tags:
            raise ValueError("tags must contain at least one value")

        normalized = normalize_path(path, self.rules)
        ensure_write_allowed(normalized, self.rules)
        if not normalized.exists():
            raise FileNotFoundError(f"File '{path}' does not exist")

        with self.locks.acquire(normalized):
            content = read_text(normalized)

        relative = self._path(normalized)
        existing = self.metadata.get_entry(relative) or {}
        current_explicit = normalize_tags(existing.get("explicit_tags", []))
        removal = set(normalize_tags(tags))
        updated_explicit = [tag for tag in current_explicit if tag not in removal]
        self.metadata.update_document(relative, content, explicit_tags=updated_explicit,clear_tags=True)
        return normalized

    def list_files_by_tags(
        self,
        tags: Sequence[str],
        *,
        match_mode: Literal["any", "all"] = "any",
    ) -> List[Dict[str, Any]]:
        """Return metadata describing files that match ``tags``."""

        if not isinstance(tags, Sequence) or isinstance(tags, (str, bytes)):
            raise ValueError("tags must be a sequence of tag strings")
        cleaned = [str(tag) for tag in tags]
        return self.metadata.find_files_by_tags(cleaned, match_mode=match_mode)


    def _dispatch(
        self, method_name: str, event: FileUpsertEvent | FileDeleteEvent
    ) -> None:
        """Call ``method_name`` on every listener and wrap failures for clarity."""

        for listener in self.listeners:
            handler = getattr(listener, method_name)
            try:
                handler(event)  # type: ignore[misc]
            except Exception as exc:  # pragma: no cover - defensive logging path
                raise RuntimeError(
                    f"Knowledge base listener {listener!r} failed during {method_name}: {exc}"
                ) from exc
