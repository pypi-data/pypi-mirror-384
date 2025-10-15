"""Change event types and listener contracts for knowledge base updates.

The knowledge base emits high-level events whenever a markdown document is
created, updated, or soft deleted. Downstream components can subscribe to these
notifications to implement side effects such as vector database ingestion without
coupling the core filesystem logic to specific backends. Each event captures both
absolute and knowledge-base-relative paths so that listeners can decide which
identifier best fits their storage requirements.
"""

from __future__ import annotations

from ast import Tuple
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable, TYPE_CHECKING, Dict, Any
from pydantic import BaseModel, model_validator

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from typing import List

    from mcp_kb.knowledge.store import KnowledgeBase


class FileUpsertEvent(BaseModel):
    """Describes a document that was created or updated inside the knowledge base.

    Attributes
    ----------
    path:
        Path relative to the configured knowledge base root. This identifier is
        stable across restarts and makes for concise IDs in downstream systems.
    content:
        Full markdown content of the updated document at the time the event was
        emitted. Listeners can avoid re-reading the file when they only need the
        text payload.
    """
    path: str
    content: str

    # make sure path is a string
    @model_validator(mode="before")
    @classmethod
    def check_path(cls, values: dict) -> dict:
        if isinstance(values["path"], Path):
            values["path"] = str(values["path"])
        return values


class FileDeleteEvent(BaseModel):
    """Signals that a document has been soft deleted according to PRD semantics.

    Attributes
    ----------
    path:
        Original knowledge-base-relative path before soft deletion. Downstream
        systems should remove entries keyed by this relative path to stay in
        sync with the knowledge base state.
    """
    path: str

    # make sure path is a string
    @model_validator(mode="before")
    @classmethod
    def check_path(cls, values: dict) -> dict:
        if isinstance(values["path"], Path):
            values["path"] = str(values["path"])
        return values


class KnowledgeBaseListener(Protocol):
    """Interface for components that react to knowledge base change events."""

    def handle_upsert(self, event: FileUpsertEvent) -> None:
        """Persist changes triggered by a document creation or update event."""

    def handle_delete(self, event: FileDeleteEvent) -> None:
        """Process the removal of a previously ingested document."""


@runtime_checkable
class KnowledgeBaseSearchListener(Protocol):
    """Optional extension that allows listeners to service search requests."""

    def search(
        self,
        kb: "KnowledgeBase",
        query: str,
        *,
        context_lines: int = 2, 
        limit: Optional[int] = None,
    ) -> "Tuple[List[FileSegment], Dict[str, Any]]":
        """Return semantic search matches for ``query`` or an empty list."""


@runtime_checkable
class KnowledgeBaseReindexListener(Protocol):
    """Optional extension that allows listeners to perform full reindexing.

    Implementations can expose a ``reindex`` method to rebuild any external
    indexes from the current state of the knowledge base. The method should be
    idempotent and safe to run multiple times.
    """

    def reindex(self, kb: "KnowledgeBase") -> int:
        """Rebuild indexes, returning the number of documents processed."""
