"""Search utilities that operate on the knowledge base filesystem.

The functions in this module are separate from ``KnowledgeBase`` so that they
can evolve independently. Search often benefits from dedicated caching or
indexing strategies; keeping it in its own module means the server can swap the
implementation later without changing the core file lifecycle API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Literal, Any, Tuple

from mcp_kb.config import DATA_FOLDER_NAME, DOC_FILENAME
from mcp_kb.knowledge.events import KnowledgeBaseSearchListener
from mcp_kb.knowledge.store import KnowledgeBase, FileSegment
from pydantic import BaseModel


def search_text(
    kb: KnowledgeBase,
    query: str,
    context_lines: int = 2,
    *,
    providers: Iterable[KnowledgeBaseSearchListener] | None = None,
    n_results: Optional[int] = None,
) -> Tuple[List[FileSegment], Dict[str, Any]]:
    """Search for ``query`` in all non-deleted knowledge base files.

    Parameters
    ----------
    kb:
        Active knowledge base instance used to iterate over files.
    query:
        Literal string that should be located within the files. The helper does
        not treat the query as a regular expression to avoid surprising matches
        when characters such as ``*`` appear in user input.
    context_lines:
        Number of lines to include before and after each match. Defaults to two
        lines, aligning with the PRD's requirement for contextual snippets.
    providers:
        Optional iterable of listeners capable of serving semantic search
        results. Providers are consulted in order and the first non-empty
        response is returned to the caller. When no provider produces results the
        function falls back to a filesystem scan.
    n_results:
        Maximum number of matches to return. ``None`` keeps the legacy behaviour
        of returning every match discovered on disk.

    Returns
    -------
    list[FileSegment]
        Ordered list of matches. Each match contains the absolute path, the
        one-based line number where the query was found, and the extracted
        context lines.
    """

    all_matches: List[FileSegment] = []
    all_meta: Dict[str, Any] = {}
    for provider in providers or ():
        try:
            matches,meta = provider.search(
                kb,
                query,
                context_lines=context_lines,
                limit=n_results,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            raise RuntimeError(f"Search provider {provider!r} failed: {exc}") from exc
        if matches:
            all_matches.extend(matches)
            all_meta.update(meta)

    all_matches.extend(_search_by_scanning(kb, query, context_lines, n_results))
    for match in all_matches:
        match.assert_path(kb.rules)
    return all_matches,all_meta


def _search_by_scanning(
    kb: KnowledgeBase,
    query: str,
    context_lines: int,
    n_results: Optional[int],
) -> List[FileSegment]:
    """Return search matches by scanning files on disk."""

    matches: List[FileSegment] = []
    for path in kb.iter_active_files():
        matches.extend(_extract_matches_for_path(path, query, context_lines))
        if n_results is not None and len(matches) >= n_results:
            return matches[:n_results]
    return matches


def _build_tree(paths: List[List[str]]) -> Dict[str, Dict]:
    """Construct a nested dictionary representing the directory tree."""

    tree: Dict[str, Dict] = {}
    for parts in paths:
        current = tree
        for part in parts:
            current = current.setdefault(part, {})
    return tree


def _flatten_tree(tree: Dict[str, Dict], prefix: str = "  ") -> List[str]:
    """Convert a nested dictionary tree into indented lines."""

    lines: List[str] = []
    for name in sorted(tree.keys()):
        lines.append(f"{prefix}- {name}")
        lines.extend(_flatten_tree(tree[name], prefix + "  "))
    return lines


def build_tree_overview(kb: KnowledgeBase) -> str:
    """Produce a textual tree showing the structure of the knowledge base.

    The output intentionally mirrors a simplified ``tree`` command but remains
    deterministic across operating systems by controlling ordering and
    indentation.
    """

    paths = [
        list(path.relative_to(kb.rules.root).parts) for path in kb.iter_active_files()
    ]
    tree = _build_tree(paths)
    lines =  []
    lines.extend(_flatten_tree(tree,prefix=""))
    return "\n".join(lines)

def build_tags_overview(kb: KnowledgeBase) -> str:
    """Produce a textual summary of the unique tag inventory for the knowledge base."""

    tags = []
    lines: List[str] = []
    metadata = getattr(kb, "metadata", None)
    if metadata is not None:
        try:
            tags = metadata.all_tags()
        except Exception:  # pragma: no cover - defensive safeguard
            tags = []
    if tags:
        lines.append("Tags:")
        for tag in tags:
            lines.append(f"- {tag}")
    return "\n".join(lines)

def read_documentation(kb: KnowledgeBase) -> str:
    """Return documentation content if the canonical file exists.

    The helper intentionally performs no access control checks because read
    operations are always permitted, even for the protected documentation
    folder.
    """

    doc_path = kb.rules.root / DATA_FOLDER_NAME / DOC_FILENAME
    if not doc_path.exists():
        return ""
    return doc_path.read_text(encoding="utf-8")


def _extract_matches_for_path(
    path: Path, query: str, context_lines: int
) -> List[FileSegment]:
    """Read ``path`` and return every match that contains ``query``."""

    lines = path.read_text(encoding="utf-8").splitlines()
    return _extract_matches_from_lines(path, lines, query, context_lines)


def _extract_matches_from_lines(
    path: Path,
    lines: List[str],
    query: str,
    context_lines: int,
) -> List[FileSegment]:
    """Return matches using the provided ``lines`` buffer."""

    matches: List[FileSegment] = []
    for index, line in enumerate(lines, start=1):
        if query in line:
            start = max(0, index - context_lines - 1)
            end = min(len(lines), index + context_lines)
            context = '\n'.join(lines[start:end])
            matches.append(FileSegment(
                path=path, start_line=start, end_line=end, content=context))
    return matches

__all__ = [
    "search_text",
]
