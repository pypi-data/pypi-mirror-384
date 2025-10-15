"""UI API helpers built on top of the knowledge base.

The functions in this module provide reusable primitives for serving the web
UI. They deliberately separate data shaping from the HTTP layer, which keeps
the request handler small and easy to test in isolation.
"""

from __future__ import annotations

import json
import threading
from typing import Dict, List, Literal, Optional, TypedDict, Any

from mcp_kb.knowledge.store import KnowledgeBase, FileSegment
from mcp_kb.knowledge.search import search_text
from mcp_kb.knowledge.events import KnowledgeBaseSearchListener


class TreeNode(TypedDict):
    """JSON-serializable representation of an entry in the file tree."""

    name: str
    path: str
    type: Literal["file", "dir"]
    children: List["TreeNode"]


def build_tree_json(kb: KnowledgeBase) -> TreeNode:
    """Return a nested dictionary describing the current file tree.

    The result starts at the knowledge base root and includes all active text
    files, excluding soft-deleted files and the protected documentation folder
    to align with the server's overview semantics.
    """

    # Build a nested dict tree keyed by name for deterministic ordering
    root: Dict[str, Dict] = {}
    for path in kb.iter_active_files():
        parts = list(path.relative_to(kb.rules.root).parts)
        cursor = root
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor.setdefault(parts[-1], {})

    def _to_node(name: str, subtree: Dict, prefix: str) -> TreeNode:
        full_path = f"{prefix}/{name}" if prefix else name
        if subtree:  # directory
            children: List[TreeNode] = [
                _to_node(child, subtree[child], full_path)
                for child in sorted(subtree.keys())
            ]
            return TreeNode(name=name, path=full_path, type="dir", children=children)
        return TreeNode(name=name, path=full_path, type="file", children=[])

    # Convert to the final shape with a synthetic root
    children = [_to_node(k, v, "") for k, v in sorted(root.items())]
    return TreeNode(name="", path="", type="dir", children=children)


def read_file_json(kb: KnowledgeBase, path: str) -> FileSegment:
    """Read and return a file as a JSON-compatible dictionary."""

    segment = kb.read_file(path)
    segment.assert_path(kb.rules)
    return segment


def write_file(kb: KnowledgeBase, path: str, content: str) -> None:
    """Create or overwrite ``path`` with ``content`` using the knowledge base.

    This operation routes through :meth:`~mcp_kb.knowledge.store.KnowledgeBase.create_file`
    so that the same validation, locking, and listener notification behavior
    applies as for MCP tool invocations.
    """

    kb.create_file(path, content)


__all__ = [
    "TreeNode",
    "build_tree_json",
    "read_file_json",
    "write_file",
    "search_json",
    "vector_status_json",
    "vector_embeddings_json",
    "vector_query_embedding_json",
    "vector_reindex_json",
    "vector_refit_json",
]


def search_json(kb: KnowledgeBase, query: str, *, limit: int | None = None) -> List[Dict[str, Any]]:
    """Return JSON-compatible search results for ``query``.

    Each result includes the relative ``path`` (string), one-based ``line``
    number (int) where the match occurs, and ``context`` (list[str]) with
    surrounding lines.
    """

    # Reuse the same provider model as the MCP tool: if registered listeners
    # expose a search capability (e.g., Chroma ingestion), consult them first
    # before falling back to on-disk scans. This keeps UI and MCP semantics
    # aligned so results are consistent across entry points.
    providers: List[KnowledgeBaseSearchListener] = []
    for listener in getattr(kb, "listeners", ()):  # type: ignore[attr-defined]
        if isinstance(listener, KnowledgeBaseSearchListener):
            providers.append(listener)

   
    all_meta={}
    matches,meta = search_text(kb, query, providers=providers, n_results=limit)
    payload: List[Dict[str, Any]] = []
    for m in matches:
        payload.append(
            m.model_dump()
        )
    return {"results":payload,"meta":meta}


# ----------------------------- Vector Endpoints -----------------------------

def _find_chroma_listener(kb: KnowledgeBase) -> Optional[Any]:
    """Return the first Chroma-like listener attached to ``kb`` or ``None``.

    The UI exposes additional endpoints when a vector store is available. To
    avoid introducing a hard dependency on Chroma, the discovery relies on
    duck-typing: listeners that provide a ``collection`` attribute (Chroma
    collection) and a ``configuration`` with an ``embedding`` field are treated
    as vector-capable.
    """

    for listener in getattr(kb, "listeners", ()):  # type: ignore[attr-defined]
        if hasattr(listener, "collection"):
            return listener
    return None


def _to_list(x: Any) -> List[float]:
    """Return ``x`` as a JSON-serializable list of floats.

    Chroma may return embeddings as NumPy arrays. This helper converts any
    sequence-like object to a plain Python list of floats using ``tolist`` when
    available.
    """

    try:
        if isinstance(x, str):
            data = json.loads(x)
            if isinstance(data, (list, tuple)):
                return [float(v) for v in data]
        if hasattr(x, "indices") and hasattr(x, "values"):
            values = getattr(x, "values")
            indices = getattr(x, "indices")
            size = int(getattr(x, "size", len(values)))
            dense = [0.0] * size
            for idx, value in zip(indices, values):
                dense[int(idx)] = float(value)
            return dense
        if hasattr(x, "tolist"):
            return [float(v) for v in x.tolist()]
    except Exception:
        pass
    # Fallback: best-effort cast
    try:
        return [float(v) for v in x]
    except Exception:
        return []


def vector_status_json(kb: KnowledgeBase) -> Dict[str, object]:
    """Report whether a vector store is available and basic dataset stats.

    Returns a JSON-compatible dictionary with the following keys:
    - ``available`` (bool): true when a Chroma listener is attached.
    - ``dimensions`` (int | null): length of the embedding vectors when
      available; derived from a sample row.
    - ``count`` (int | null): total number of stored embedding chunks.
    """

    listener = _find_chroma_listener(kb)
    if listener is None:
        return {"available": False, "dimensions": None, "count": None}

    collection = getattr(listener, "collection")
    # Total count
    try:
        total = collection.count()  # type: ignore[no-untyped-call]
    except Exception:
        total = None

    # Sample one embedding to infer dimensions
    dims: Optional[int] = None
    try:
        sample = collection.get(limit=1, include=["embeddings"])  # type: ignore[no-untyped-call]
        embs = sample.get("embeddings") or []
        # Avoid ambiguous truth checks on NumPy arrays
        if isinstance(embs, (list, tuple)) and len(embs) > 0:
            first = _to_list(embs[0])
            if first:
                dims = len(first)
    except Exception:
        dims = None

    return {"available": True, "dimensions": dims, "count": total}


def vector_embeddings_json(
    kb: KnowledgeBase,
    *,
    limit: int = 1000,
    offset: int = 0,
    path: Optional[str] = None,
) -> List[Dict[str, object]]:
    """Return a page of embeddings with metadata for plotting.

    Parameters
    ----------
    limit:
        Maximum number of items to return (default: 1000).
    offset:
        Starting offset into the result set for paging.
    path:
        Optional relative path to filter embeddings from a specific file.

    Returns
    -------
    list[dict]
        Each item contains ``id`` (str), ``document_id`` (str|None), ``path``
        (str), ``chunk`` (int), and ``embedding`` (list[float]). When the
        backend provides precomputed UMAP projections the dictionaries also
        surface ``umap2d`` and ``umap3d`` coordinates for downstream
        visualisations.
    """

    listener = _find_chroma_listener(kb)
    if listener is None:
        return []

    collection = getattr(listener, "collection")
    where = {"path": path} if path else None
    # Chroma's `include` only accepts certain fields; `ids` are always returned
    # and must not be listed in `include`.
    payload = collection.get(  # type: ignore[no-untyped-call]
        where=where,
        include=["embeddings", "metadatas"],
        limit=limit,
        offset=offset,
    )

    ids = payload.get("ids")
    embs = payload.get("embeddings")
    metas = payload.get("metadatas")
    if ids is None:
        ids = []
    if embs is None:
        embs = []
    if metas is None:
        metas = []

    results: List[Dict[str, object]] = []
    for i, emb in enumerate(embs):
        meta: Dict[str, Any] = metas[i] if i < len(metas) else {}
        umap2d: List[float] = []
        umap3d: List[float] = []
        if isinstance(meta, dict):
            umap2d = _to_list(meta.get("umap2d", []))
            umap3d = _to_list(meta.get("umap3d", []))
        document_id = meta.get("document_id")
        results.append(
            {
                "id": ids[i] if i < len(ids) else str(i),
                "document_id": document_id if isinstance(document_id, str) else None,
                "path": meta.get("path", ""),
                "chunk": int(meta.get("chunk_number", 0)),
                "embedding": _to_list(emb),
                "umap2d": umap2d,
                "umap3d": umap3d,
            }
        )
    return results


def vector_query_embedding_json(kb: KnowledgeBase, query: str) -> Dict[str, object]:
    """Compute and return the embedding vector for ``query``.

    The implementation reuses the Chroma collection's embedding function when
    available. As a fallback it attempts to reconstruct an embedding function
    instance based on the ingestor's configuration.
    """

    listener = _find_chroma_listener(kb)
    if listener is None:
        return {"embedding": [], "used_model": None}

    collection = getattr(listener, "collection")

    # Preferred path: use the collection's configured embedding function.
    func = getattr(collection, "_embedding_function", None)
    if callable(func):
        try:
            vecs = func([query])  # type: ignore[misc]
            if isinstance(vecs, (list, tuple)) and len(vecs) > 0:
                return {
                    "embedding": _to_list(vecs[0]),
                    "used_model": getattr(func, "__class__", type(func)).__name__,
                }
        except Exception:
            pass

    # Fallback: try to build a new embedding function of the same type.
    try:
        deps = getattr(listener, "_deps", None)
        cfg = getattr(listener, "configuration", None)
        if deps is not None and cfg is not None:
            factories: Dict[str, Any] = getattr(deps, "embedding_factories", {})
            emb_name = getattr(cfg, "embedding", "default")
            factory = factories.get(emb_name)
            if factory is not None:
                inst = factory()
                vecs = inst([query])
                if isinstance(vecs, (list, tuple)) and len(vecs) > 0:
                    return {"embedding": _to_list(vecs[0]), "used_model": inst.__class__.__name__}
    except Exception:
        pass

    return {"embedding": [], "used_model": None}


def vector_reindex_json(kb: KnowledgeBase) -> Dict[str, object]:
    """Trigger a background rebuild of the Chroma index and report status."""

    listener = _find_chroma_listener(kb)
    if listener is None:
        return {"status": "unavailable"}

    starter = getattr(listener, "start_reindex_async", None)
    if callable(starter):
        started = bool(starter(kb))
        return {"status": "queued" if started else "running"}

    def _run() -> None:
        try:
            listener.reindex(kb)  # type: ignore[attr-defined]
        except Exception:
            # Fallback should never raise; swallow to keep the API robust.
            pass

    try:
        thread = threading.Thread(target=_run, name="kb-reindex", daemon=True)
        thread.start()
        return {"status": "queued"}
    except Exception:
        return {"status": "error"}


def vector_refit_json(kb: KnowledgeBase) -> Dict[str, object]:
    """Trigger an immediate background UMAP refit when supported."""

    listener = _find_chroma_listener(kb)
    if listener is None:
        return {"status": "unavailable"}

    trigger = getattr(listener, "trigger_umap_refit_async", None)
    if callable(trigger):
        started = bool(trigger())
        return {"status": "queued" if started else "error"}

    scheduler = getattr(listener, "_schedule_umap_refit", None)
    if callable(scheduler):
        try:
            scheduler(delay=0.0)
            return {"status": "queued"}
        except Exception:
            return {"status": "error"}

    return {"status": "error"}
