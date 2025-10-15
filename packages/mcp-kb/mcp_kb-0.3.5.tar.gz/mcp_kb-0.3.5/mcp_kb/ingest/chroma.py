"""Integration layer that mirrors knowledge base updates into ChromaDB."""

from __future__ import annotations


import importlib
import json
import logging
import pickle
import threading
from pathlib import Path
from bisect import bisect_right
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Sequence,
    Tuple,
    Type,
    TypedDict,
    Literal,
)
from datetime import datetime, timezone
from threading import Timer

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from langchain_text_splitters import TokenTextSplitter
from tqdm import tqdm
from pydantic import BaseModel, model_validator

from mcp_kb.config import DATA_FOLDER_NAME
from mcp_kb.knowledge.events import (
    FileDeleteEvent,
    FileUpsertEvent,
    KnowledgeBaseListener,
    KnowledgeBaseReindexListener,
)
from mcp_kb.knowledge.store import FileSegment


if TYPE_CHECKING:  # pragma: no cover - type checking only imports
    from chromadb.api import ClientAPI, GetResult
    from chromadb.api.models.Collection import Collection
    from mcp_kb.knowledge.store import KnowledgeBase
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        SentenceTransformer = None


def _import_sentence_transformer() -> Optional[Type[SentenceTransformer]]:
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except ImportError:
        return None



logger = logging.getLogger(__name__)



SUPPORTED_CLIENTS: Tuple[str, ...] = ("off", "ephemeral", "persistent", "http", "cloud")
"""Recognised client types exposed to operators enabling Chroma ingestion."""


class SentenceTransformerEmbedder(EmbeddingFunction):
    def __init__(self, model_name: str):
        self._model_name = model_name
        if _import_sentence_transformer() is None:
            raise ValueError("SentenceTransformer is not installed")

    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents somehow
        if self._model_name not in _SENTENCE_TRANSFORMER:
            _SENTENCE_TRANSFORMER[self._model_name] = SentenceTransformer(self._model_name)
        prompt_name=None
        if "query" in _SENTENCE_TRANSFORMER[self._model_name].prompts:
            prompt_name="query"

        return _SENTENCE_TRANSFORMER[self._model_name].encode(input,
            prompt_name=prompt_name,
            # precision="int8"
            batch_size=4
        )

    def name(self) -> str:
        return f"SentenceTransformerEmbedder-{self._model_name}"

    @classmethod
    def build_from_config(cls,config: Dict[str, Any]):
        return cls(config["model_name"])

    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.name()}


class ChromaFileSegment(FileSegment):
    """Represents a snippet of file content returned to MCP clients."""
    document_id: str
    chunk_number: int
    distance: Optional[float] = None
    chunk_id: Optional[str] = None
    umap2d:Optional[List[float]]=None
    umap3d:Optional[List[float]]=None

    @model_validator(mode="before")
    @classmethod
    def check_umap(cls, values: dict) -> dict:
        nan  = float("nan")
        if "umap2d" in values:
            values["umap2d"] = json.loads(values["umap2d"])
        else:
            values["umap2d"] = [nan,nan]
        if "umap3d" in values:
            values["umap3d"] = json.loads(values["umap3d"])
        else:
            values["umap3d"] = [nan,nan,nan]
        
        if len(values["umap2d"]) > 2:
            values["umap2d"] = values["umap2d"][:2]
        if len(values["umap3d"]) > 3:
            values["umap3d"] = values["umap3d"][:3]
        while len(values["umap2d"]) < 2:
            values["umap2d"].append(nan)
        while len(values["umap3d"]) < 3:
            values["umap3d"].append(nan)
        
        if "umap2d_x" in values:
            values["umap2d"][0] = float(values["umap2d_x"])
        if "umap2d_y" in values:
            values["umap2d"][1] = float(values["umap2d_y"])
        if "umap3d_x" in values:
            values["umap3d"][0] = float(values["umap3d_x"])
        if "umap3d_y" in values:
            values["umap3d"][1] = float(values["umap3d_y"])
        if "umap3d_z" in values:
            values["umap3d"][2] = float(values["umap3d_z"])
        
        return values


_SENTENCE_TRANSFORMER:Dict[str,SentenceTransformer]={}

class ChromaConfiguration(BaseModel):
    """Runtime configuration controlling how Chroma ingestion behaves.

    Each attribute corresponds to either a CLI flag or an environment variable
    so that deployments can toggle Chroma synchronisation without changing the
    application code. The configuration intentionally stores already-normalised
    values (e.g., resolved paths and lowercase enums) so downstream components
    can rely on consistent semantics regardless of where the data originated.
    The resolved knowledge base root is kept in ``kb_root`` for features that
    need deterministic access to the filesystem layout.
    """

    client_type: str
    collection_name: str
    embedding: str
    data_directory: Optional[Path]
    kb_root: Path
    host: Optional[str]
    port: Optional[int]
    ssl: bool
    tenant: Optional[str]
    database: Optional[str]
    api_key: Optional[str]
    custom_auth_credentials: Optional[str]
    id_prefix: str
    sentence_transformer: Optional[str] = None
    chunk_size: int = 200
    chunk_overlap: int = 20

    @model_validator(mode="after")
    def check_sentence_transformer(self) -> "ChromaConfiguration":
        if self.sentence_transformer:
            if _import_sentence_transformer() is not None:
                if self.sentence_transformer not in _SENTENCE_TRANSFORMER:
                    from sentence_transformers.util import is_sentence_transformer_model
                    if not is_sentence_transformer_model(self.sentence_transformer):
                        raise ValueError(f"Invalid sentence transformer model: {self.sentence_transformer}")



        return self
            

    @property
    def enabled(self) -> bool:
        """Return ``True`` when ingestion should be activated."""

        return self.client_type != "off"

    @classmethod
    def from_options(
        cls,
        *,
        root: Path,
        client_type: str,
        collection_name: str,
        embedding: str,
        data_directory: Optional[str],
        host: Optional[str],
        port: Optional[int],
        ssl: bool,
        tenant: Optional[str],
        database: Optional[str],
        api_key: Optional[str],
        custom_auth_credentials: Optional[str],
        id_prefix: Optional[str],
        sentence_transformer: Optional[str] = None,
        chunk_size: int = 200,
        chunk_overlap: int = 20,
    ) -> "ChromaConfiguration":
        """Normalise CLI and environment inputs into a configuration object.

        Parameters
        ----------
        root:
            Absolute knowledge base root used to derive default directories. The
            resolved path is stored on the resulting configuration as
            ``kb_root`` for downstream components that need filesystem access.
        client_type:
            One of :data:`SUPPORTED_CLIENTS`. ``"off"`` disables ingestion.
        collection_name:
            Target Chroma collection that will store knowledge base documents.
        embedding:
            Name of the embedding function to instantiate. Values are matched
            case-insensitively to the functions exported by Chroma.
        data_directory:
            Optional directory for the persistent client. When omitted and the
            client type is ``"persistent"`` the function creates a ``chroma``
            sub-directory next to the knowledge base.
        host / port / ssl / tenant / database / api_key / custom_auth_credentials:
            Transport-specific settings passed directly to the Chroma client
            constructors.
        id_prefix:
            Optional prefix prepended to every document ID stored in Chroma.
            Defaults to ``"kb::"`` for readability.
        sentence_transformer:
            Optional name of a sentence transformer model to load when the
            ``sentence-transformers`` extra is installed. ``None`` keeps the
            default embedding factory untouched.
        """

        normalized_type = (client_type or "off").lower()
        if normalized_type not in SUPPORTED_CLIENTS:
            raise ValueError(f"Unsupported Chroma client type: {client_type}")

        resolved_directory: Optional[Path]
        if data_directory:
            resolved_directory = Path(data_directory).expanduser().resolve()
        elif normalized_type == "persistent":
            resolved_directory = (root / DATA_FOLDER_NAME / "chroma").resolve()
        else:
            resolved_directory = None

        if resolved_directory is not None:
            resolved_directory.mkdir(parents=True, exist_ok=True)

        prefix = id_prefix or "kb::"

        normalized_embedding = (embedding or "default").lower()

        config = cls(
            kb_root=root,
            client_type=normalized_type,
            collection_name=collection_name,
            embedding=normalized_embedding,
            data_directory=resolved_directory,
            host=host,
            port=port,
            ssl=ssl,
            tenant=tenant,
            database=database,
            api_key=api_key,
            custom_auth_credentials=custom_auth_credentials,
            id_prefix=prefix,
            sentence_transformer=sentence_transformer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        config._validate()
        return config

    def _validate(self) -> None:
        """Validate the configuration and raise descriptive errors when invalid."""

        if not self.enabled:
            return

        if self.client_type == "persistent" and self.data_directory is None:
            raise ValueError("Persistent Chroma client requires a data directory")

        if self.client_type == "http" and not self.host:
            raise ValueError(
                "HTTP Chroma client requires --chroma-host or MCP_KB_CHROMA_HOST"
            )

        if self.client_type == "cloud":
            missing = [
                name
                for name, value in (
                    ("tenant", self.tenant),
                    ("database", self.database),
                    ("api_key", self.api_key),
                )
                if not value
            ]
            if missing:
                pretty = ", ".join(missing)
                raise ValueError(f"Cloud Chroma client requires values for: {pretty}")

        if not self.collection_name:
            raise ValueError("Collection name must be provided")

        if not self.embedding:
            raise ValueError("Embedding function name must be provided")


class _ChromaDependencies(BaseModel):
    """Lazy import bundle containing the pieces needed to talk to ChromaDB."""

    chroma_module: Any
    settings_cls: Type[Any]
    embedding_factories: Mapping[str, Type[Any]]


def _load_dependencies() -> _ChromaDependencies:
    """Import ChromaDB lazily so the base server works without the dependency."""

    try:
        chroma_module = importlib.import_module("chromadb")
    except ModuleNotFoundError as exc:  # pragma: no cover - dependent on environment
        raise RuntimeError(
            "Chroma integration requested but the 'chromadb' package is not installed. "
            "Install chromadb via 'uv add chromadb' or disable ingestion."
        ) from exc

    config_module = importlib.import_module("chromadb.config")
    embedding_module = importlib.import_module("chromadb.utils.embedding_functions")

    factories: Dict[str, Type[Any]] = {}
    fallback_map = {
        "default": "DefaultEmbeddingFunction",
        "cohere": "CohereEmbeddingFunction",
        "openai": "OpenAIEmbeddingFunction",
        "jina": "JinaEmbeddingFunction",
        "voyageai": "VoyageAIEmbeddingFunction",
        "roboflow": "RoboflowEmbeddingFunction",
    }
    for alias, attr in fallback_map.items():
        if hasattr(embedding_module, attr):
            factories[alias] = getattr(embedding_module, attr)
    if not factories:
        raise RuntimeError(
            "No embedding functions were found in chromadb.utils.embedding_functions"
        )

    

    factories["sentence_transformer"] = SentenceTransformerEmbedder

    return _ChromaDependencies(
        chroma_module=chroma_module,
        settings_cls=getattr(config_module, "Settings"),
        embedding_factories=factories,
    )




def line_starts(s: str):
    """Return a list of 0-based character offsets where each line starts."""
    starts = []
    pos = 0
    for line in s.splitlines(keepends=True):  # handles \n, \r\n, \r
        starts.append(pos)
        pos += len(line)
    if not s.endswith(('\n', '\r')):  # last line without newline
        starts.append(pos)  # sentinel for bisect
    else:
        starts.append(pos)  # still add sentinel
    return starts

def char_to_line(char_idx: int, starts: list[int]) -> int:
    """Map a 0-based char index to a 0-based line number."""
    # bisect_right gives index of first start > char_idx
    return bisect_right(starts, char_idx)-1  # already 1-based because starts[0] is line 1

def find_start_char(subtext:str,full_text:str) -> int:
    """Find the start character of a subtext in a fulltext."""
    return full_text.find(subtext)

class ChromaIngestor(KnowledgeBaseListener, KnowledgeBaseReindexListener):
    """Listener that mirrors knowledge base writes into a Chroma collection.

    The listener adheres to the :class:`KnowledgeBaseListener` protocol so it
    can be registered alongside other observers without coupling. Events are
    written synchronously to guarantee that indexing stays consistent with the
    underlying filesystem operations.
    """

    def __init__(self, configuration: ChromaConfiguration) -> None:
        """Create an ingestor bound to ``configuration``.

        Parameters
        ----------
        configuration:
            Sanitised :class:`ChromaConfiguration` describing how to connect to
            Chroma and which collection to mirror.
        """

        self.configuration = configuration
        self._deps = _load_dependencies()
        self._client = self._create_client()
        self._collection = self._ensure_collection()
        self.textsplitter = TokenTextSplitter(
            chunk_size=self.configuration.chunk_size, chunk_overlap=self.configuration.chunk_overlap, add_start_index=True,strip_whitespace=False
        )
        # Optional UMAP integration is initialised lazily because the dependency
        # may be absent in environments such as Python 3.13 where wheels are not
        # yet available. The attributes are cached on the instance to avoid
        # repetitively loading models from disk.
        try:
            import umap  # type: ignore

            self._umap_mod = umap
        except Exception:
            self._umap_mod = None
        self._umap_dir = (
            self.configuration.kb_root / DATA_FOLDER_NAME / "umap"
        ).resolve()
        try:
            self._umap_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Directory creation failures should not break ingestion; training
            # simply becomes a no-op.
            pass
        self._umap_2d = None
        self._umap_3d = None
        self._umap_timer: Optional[Timer] = None
        self._umap_fit_lock = threading.Lock()
        self._reindex_lock = threading.Lock()
        if self._umap_mod:
            self._load_umap_models()

    def get_document_chunks(
        self, document_id: str, include: List[str] = ["metadatas", "documents"]
    ) -> GetResult:
        """Get a document from the Chroma index."""
        return self._collection.get(where={"document_id": document_id}, include=include)

    def handle_upsert(self, event: FileUpsertEvent) -> None:
        """Upsert ``event`` into the configured Chroma collection.

        Every invocation removes any existing Chroma entry before inserting the
        fresh payload so that the embedding engine recomputes vectors using the
        latest markdown. The stored metadata keeps both absolute and relative
        paths, enabling downstream semantic search tools to surface references
        that point straight back into the knowledge base.
        """

        document_id = f"{self.configuration.id_prefix}{event.path}"
        relative = Path(event.path)
        self._reindex_document(document_id, event.content, relative)
        self._schedule_umap_refit()

    def delete_document(self, document_id: str) -> None:
        """Delete a document from the Chroma index."""
        self._collection.delete(
            ids=self.get_document_chunks(document_id, include=[])["ids"]
        )

    def handle_delete(self, event: FileDeleteEvent) -> None:
        """Remove documents associated with ``event`` from the Chroma index.

        Soft deletions translate to a straight removal because the PRD treats
        files carrying the delete sentinel as hidden from client tooling.
        """

        document_id = f"{self.configuration.id_prefix}{event.path}"
        try:
            self.delete_document(document_id)
        except Exception:  # pragma: no cover - depends on Chroma exceptions
            # Chroma raises a custom error when the ID is missing. Deletion should
            # be idempotent so we swallow those errors silently.
            pass
        self._schedule_umap_refit()

    @property
    def collection(self) -> "Collection":
        """Return the underlying Chroma collection for diagnostics and tests."""

        return self._collection

    # UMAP helpers -------------------------------------------------------------

    def _umap_paths(self) -> Tuple[Path, Path, Path]:
        """Return the filesystem locations backing persisted UMAP state.

        The tuple contains the pickled 2D model, the pickled 3D model, and a
        companion JSON metadata file stored alongside them inside the knowledge
        base's ``.data/umap`` directory.
        """

        base = self.configuration.collection_name
        two_path = self._umap_dir / f"{base}-umap-2d.pkl"
        three_path = self._umap_dir / f"{base}-umap-3d.pkl"
        meta_path = self._umap_dir / f"{base}-umap-meta.json"
        return two_path, three_path, meta_path

    def _load_umap_models(self) -> bool:
        """Load persisted UMAP transformers into memory when present.

        Returns ``True`` when both the 2D and 3D models were unpickled
        successfully, otherwise leaves the cached attributes set to ``None`` so
        callers can fall back to on-demand refits.
        """

        if not self._umap_mod:
            return False
        two_path, three_path, _ = self._umap_paths()
        if not two_path.exists() or not three_path.exists():
            return False
        try:
            with two_path.open("rb") as fh:
                self._umap_2d = pickle.load(fh)
            with three_path.open("rb") as fh:
                self._umap_3d = pickle.load(fh)
            return True
        except Exception:
            self._umap_2d = None
            self._umap_3d = None
            return False

    def _save_umap_models(
        self,
        umap2d: Any,
        umap3d: Any,
        *,
        sample_count: int,
        dimensions: int,
        neighbors: int,
    ) -> None:
        """Persist trained UMAP models alongside a JSON metadata descriptor.

        The helper writes both pickles plus a human-readable JSON file so
        operators can audit when the layout was last refreshed and which
        hyperparameters were used during training.
        """

        two_path, three_path, meta_path = self._umap_paths()
        payload = {
            "trained_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "n_samples": sample_count,
            "n_dims": dimensions,
            "metric": "cosine",
            "neighbors": neighbors,
            "min_dist": 0.1,
        }
        try:
            with two_path.open("wb") as fh:
                pickle.dump(umap2d, fh)
            with three_path.open("wb") as fh:
                pickle.dump(umap3d, fh)
            meta_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # pragma: no cover - persistence is best effort
            logger.exception("Failed to persist UMAP models", exc_info=exc)

    def _transform_umap(
        self,
        embeddings: List[List[float]],
    ) -> Tuple[Optional[List[List[float]]], Optional[List[List[float]]]]:
        """Project ``embeddings`` using cached models when available.

        The function returns coordinate lists for each embedding when both model
        instances are loaded; otherwise it yields ``(None, None)`` to signal that
        the caller should skip annotating metadata.
        """

        if embeddings is None or len(embeddings) == 0 or len(embeddings[0]) == 0:
            return None, None
        if self._umap_2d is None or self._umap_3d is None:
            self._load_umap_models()
        if self._umap_2d is None or self._umap_3d is None:
            return None, None
        try:
            raw2d = self._umap_2d.transform(embeddings)
            raw3d = self._umap_3d.transform(embeddings)
            coords2d = self._coerce_projection(raw2d)
            coords3d = self._coerce_projection(raw3d)
            return coords2d, coords3d
        except Exception:
            return None, None

    def _fetch_all_embeddings(
        self,
        batch_size: int = 256,
    ) -> Tuple[
        List[List[float]],
        List[str],
        List[str],
        List[Dict[str, Any]],
    ]:
        """Return embeddings, IDs, documents, and metadata from the collection.

        Chroma's pagination is consumed in batches to avoid overwhelming memory
        usage on large corpora while still returning native Python structures
        that are convenient for subsequent processing.
        """

        embeddings: List[List[float]] = []
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        offset = 0
        while True:
            payload = self._collection.get(  # type: ignore[no-untyped-call]
                include=["embeddings", "documents", "metadatas"],
                limit=batch_size,
                offset=offset,
            )
            got_ids = payload.get("ids")
            got_embs = payload.get("embeddings")
            got_docs = payload.get("documents")
            got_metas = payload.get("metadatas")
            if got_ids is None:
                got_ids = []
            if got_embs is None:
                got_embs = []
            if got_docs is None:
                got_docs = []
            if got_metas is None:
                got_metas = []
            if not got_ids:
                break
            for doc_id, emb, doc, meta in zip(
                got_ids,
                got_embs,
                got_docs,
                got_metas,
            ):
                try:
                    vector = (
                        [float(x) for x in emb.tolist()]
                        if hasattr(emb, "tolist")
                        else [float(x) for x in emb]
                    )
                except Exception:
                    continue
                embeddings.append(vector)
                ids.append(doc_id)
                documents.append(doc)
                metadatas.append(dict(meta or {}))
            offset += len(got_ids)
        return embeddings, ids, documents, metadatas

    def _coerce_projection(self, value: Any) -> List[List[float]]:
        """Return ``value`` materialised as a ``list[list[float]]`` structure.

        Numpy arrays, nested sequences, and other iterable containers are
        normalised by iterating over rows and coercing each element to a float.
        Invalid rows are skipped to keep the caller's downstream processing
        trivial.
        """

        if value is None:
            return []
        try:
            if hasattr(value, "tolist"):
                value = value.tolist()
        except Exception:
            pass
        result: List[List[float]] = []
        for row in value:
            try:
                if hasattr(row, "tolist"):
                    row = row.tolist()
                result.append([float(x) for x in row])
            except Exception:
                continue
        return result

    def _prepare_umap_metadata(
        self,
        coords2d: Sequence[float],
        coords3d: Sequence[float],
    ) -> Dict[str, Any]:
        """Build a metadata payload that satisfies Chroma's type constraints.

        The coordinates are stored as JSON-encoded strings (``"[x, y]"`` and
        ``"[x, y, z]"``) alongside individual scalar components for
        convenience. This keeps metadata values within Chroma's supported types
        while allowing downstream consumers to reconstruct dense vectors.
        """

        values2 = [float(v) for v in coords2d]
        values3 = [float(v) for v in coords3d]
        payload: Dict[str, Any] = {
            "umap2d": json.dumps(values2, separators=(",", ":")),
            "umap3d": json.dumps(values3, separators=(",", ":")),
        }
        if values2:
            payload["umap2d_x"] = values2[0]
        if len(values2) > 1:
            payload["umap2d_y"] = values2[1]
        if values3:
            payload["umap3d_x"] = values3[0]
        if len(values3) > 1:
            payload["umap3d_y"] = values3[1]
        if len(values3) > 2:
            payload["umap3d_z"] = values3[2]

        return payload

    def _refit_umap_and_update_all(self) -> None:
        """Train fresh UMAP models on the entire dataset and update metadata.

        The refit process acquires a short-lived lock so only one fit runs at a
        time, retrains both the 2D and 3D manifolds, persists the models, and
        finally propagates the coordinates back into the Chroma collection.
        """

        if not self._umap_mod:
            return
        if not self._umap_fit_lock.acquire(blocking=False):
            return
        try:
            embeddings, ids, documents, metadatas = self._fetch_all_embeddings()
            if len(embeddings) < 5:
                return
            neighbor_count = max(2, min(15, len(embeddings) - 1))
            umap_class = self._umap_mod.UMAP
            umap2d = umap_class(
                n_components=2,
                metric="cosine",
                n_neighbors=neighbor_count,
                min_dist=0.1,
                random_state=42,
            )
            umap3d = umap_class(
                n_components=3,
                metric="cosine",
                n_neighbors=neighbor_count,
                min_dist=0.1,
                random_state=42,
            )
            umap2d.fit(embeddings)
            umap3d.fit(embeddings)
            coords2d = self._coerce_projection(getattr(umap2d, "embedding_", []))
            coords3d = self._coerce_projection(getattr(umap3d, "embedding_", []))
            self._umap_2d = umap2d
            self._umap_3d = umap3d
            self._save_umap_models(
                umap2d,
                umap3d,
                sample_count=len(embeddings),
                dimensions=len(embeddings[0]),
                neighbors=neighbor_count,
            )
            batch = 128
            for start in range(0, len(ids), batch):
                end = start + batch
                batch_ids = ids[start:end]
                batch_coords2d = coords2d[start:end]
                batch_coords3d = coords3d[start:end]
                batch_documents = documents[start:end]
                batch_metas: List[Dict[str, Any]] = []
                for idx, meta in enumerate(metadatas[start:end]):
                    updated = dict(meta or {})
                    c2 = batch_coords2d[idx]
                    c3 = batch_coords3d[idx]
                    updated.update(self._prepare_umap_metadata(c2, c3))
                    batch_metas.append(updated)
                try:
                    self._collection.update(  # type: ignore[no-untyped-call]
                        ids=batch_ids,
                        metadatas=batch_metas,
                    )
                except Exception:
                    try:
                        self._collection.delete(ids=batch_ids)  # type: ignore[no-untyped-call]
                        self._collection.add(  # type: ignore[no-untyped-call]
                            ids=batch_ids,
                            documents=batch_documents,
                            metadatas=batch_metas,
                        )
                    except Exception as exc:  # pragma: no cover - chroma variant specific
                        logger.exception("Failed to update UMAP metadata", exc_info=exc)
        finally:
            self._umap_fit_lock.release()

    def _schedule_umap_refit(self, delay: float = 3.0) -> None:
        """Debounce refits to avoid repeated fits during rapid edit bursts.

        Each call cancels any pending timer and schedules a new daemon thread,
        ensuring background fits eventually run without blocking foreground
        ingestion work.
        """

        if not self._umap_mod:
            return
        if self._umap_timer is not None:
            try:
                self._umap_timer.cancel()
            except Exception:
                pass
        self._umap_timer = Timer(delay, self._refit_umap_and_update_all)
        self._umap_timer.daemon = True
        self._umap_timer.start()

    def start_reindex_async(self, kb: "KnowledgeBase") -> bool:
        """Spawn a background thread that reindexes ``kb`` without blocking.

        The method acquires an internal lock to ensure only one reindex task
        runs at a time. It returns ``True`` when a new task was scheduled and
        ``False`` when another invocation is still processing documents.
        """

        if not self._reindex_lock.acquire(blocking=False):
            return False

        def _run() -> None:
            try:
                self.reindex(kb)
            finally:
                try:
                    self._reindex_lock.release()
                except RuntimeError:
                    # The lock should always be held, but guard against edge cases.
                    pass

        thread = threading.Thread(target=_run, name="kb-reindex", daemon=True)
        thread.start()
        return True

    def trigger_umap_refit_async(self) -> bool:
        """Schedule an immediate background UMAP refit when the dependency is available."""

        if not self._umap_mod:
            return False
        if self._umap_timer is not None:
            try:
                self._umap_timer.cancel()
            except Exception:
                pass
            self._umap_timer = None

        thread = threading.Thread(
            target=self._refit_umap_and_update_all,
            name="kb-umap-refit",
            daemon=True,
        )
        thread.start()
        return True

    @staticmethod
    def _convert_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata keys to match the ChromaFileSegment model (backwards compatibility)"""
        if "relative_path" in metadata:
            metadata["path"] = metadata.pop("relative_path")
        if "startline" in metadata:
            metadata["start_line"] = metadata.pop("startline")
        if "endline" in metadata:
            metadata["end_line"] = metadata.pop("endline")
        return metadata

    def query(self, query: str, *, n_results: int = 5) -> List[ChromaFileSegment]:
        """Return structured query results from the configured collection.

        Parameters
        ----------
        query:
            Natural language string used to compute the semantic embedding.
        n_results:
            Maximum number of results to return. Defaults to five to mirror the
            behaviour surfaced through the MCP search tool.

        Returns
        -------
        list[dict[str, Any]]
            Each dictionary contains the ``document`` text, associated
            ``metadata`` payload, and a floating-point ``distance`` score if
            provided by Chroma.
        """

        query_meta={}
        embs=self._collection._embedding_function([query])


        payload = self._collection.query(
            query_embeddings=embs,
            n_results=n_results,
            include=["metadatas", "documents", "distances"],
        )

        query_embeddings = [float(x) for x in embs[0]]
        # transform query_embeddings to 2d and 3d
        query_embeddings2d, query_embeddings3d = self._transform_umap([query_embeddings])
        if query_embeddings2d is not None:
            query_meta["query_embeddings_umap2d"] = query_embeddings2d[0] if query_embeddings2d is not None else None
        if query_embeddings3d is not None:
            query_meta["query_embeddings_umap3d"] = query_embeddings3d[0] if query_embeddings3d is not None else None
        query_meta["query_embeddings"] = query_embeddings
        

        docids = payload.get("ids", [[]])[0]
        documents = payload.get("documents", [[]])[0]
        metadatas = payload.get("metadatas", [[]])[0]
        distances = payload.get("distances", [[]])[0]

        

        if not documents or not documents[0]:
            return [],query_meta

        results: List[ChromaFileSegment] = []
        
        for docid, metadata, document, distance in zip(docids, metadatas, documents, distances):
            metadata = self._convert_metadata(metadata)

            results.append(
                ChromaFileSegment(
                    **metadata,
                    content=document,
                    distance=distance,
                    chunk_id=docid,
                )
            )

        return results,query_meta

    # Optional search extension -------------------------------------------------

    def search(
        self,
        kb: "KnowledgeBase",
        query: str,
        *,
        context_lines: int = 2,
        limit: Optional[int] = None,
    ) -> List[ChromaFileSegment]:
        """Translate semantic query results into :class:`ChromaFileSegment` objects."""

        max_results = limit or 5
        records,query_meta = self.query(query, n_results=max_results)
        matches: List[ChromaFileSegment] = []
       


        to_delete = set()

        for record in records:

            candidate = self._resolve_candidate_path(
                kb,
                record.path,
            )

            if candidate is None:
                to_delete.add(record.chunk_id)
                continue

            matches.append(record)
           
            if limit is not None and len(matches) >= limit:
                break

        if to_delete:
            self._find_orphaned_documents(kb,remove=True)

            return self.search(kb, query, context_lines=context_lines, limit=limit)    

        return matches,query_meta

    # Internal helpers ----------------------------------------------------------

    def _find_orphaned_documents(self,kb: "KnowledgeBase",remove: bool = True) -> Set[str]:
        """Find documents in the Chroma collection that are not in the knowledge base."""
        
        try:
            count = self._collection.count()
            to_delete = set()
            with tqdm(total=count, desc="Finding orphaned documents") as pbar:
                for i in range(0, count, 10):
                    batch = self._collection.get(include=["metadatas"], limit=10, offset=i)
                    for ids,metadata in zip(batch.get("ids", []), batch.get("metadatas", [])):
                        path = metadata.get("path")
                        if path and not kb.rules.root.joinpath(path).exists():
                            to_delete.add(ids)
                    pbar.update(10)
            if remove:
                for ids in to_delete:
                    self.collection.delete(ids=ids)
            return to_delete
        except Exception as e:
            logger.exception(e)   
            return set()
       

    def _reindex_document(
        self,
        document_id: str,
        content: str,
        path: Path,
    ) -> None:
        """Replace the stored document so embeddings are recomputed.

        Reindexing involves removing any stale record before inserting the new
        payload. Some Chroma backends keep historical data around when ``add``
        is invoked with an existing ID, so the deletion step ensures the stored
        embedding always reflects the latest markdown contents. ``metadata`` is
        copied to break accidental references held by callers.
        """

        try:
            # filter by document_id in metadata
            self.delete_document(document_id)
        except Exception:  # pragma: no cover - depends on Chroma exception types
            # Missing IDs are not an error; most clients raise when attempting to
            # delete a non-existent record. We swallow those errors to keep the
            # reindexing path idempotent.
            pass


        
        # Empty documents should not be added to Chroma. After the delete above
        # there is nothing else to do for empty payloads.
        if not content.strip():
            return

        # Split content into chunks suitable for embedding. When the splitter
        # returns no chunks (e.g., content is whitespace), skip the add call to
        # avoid Chroma errors about empty lists.
        split_docs = self.textsplitter.create_documents([content])
        if not split_docs:
            return

        starts = line_starts(content)

        chunks: List[ChromaFileSegment] = []
        chunk_texts: List[str] = []
        for i, d in enumerate(split_docs):
            start_char = d.metadata["start_index"]  # 0-based char offset in original content
            if start_char <0:
                start_char = find_start_char(d.page_content,content)
            start_line = char_to_line(start_char, starts)

            end_char_excl = start_char + len(d.page_content)  # exclusive end
            end_line = char_to_line(max(0, end_char_excl - 1), starts)
            

            file_segment = ChromaFileSegment(
                document_id=document_id,
                path=str(path),
                start_line=start_line,
                end_line=end_line,
                content=d.page_content,
                chunk_number=i,
            )
            chunks.append(file_segment)
            chunk_texts.append(d.page_content)




        ids: List[str] = []
        contents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        for idx, d in enumerate(chunks):
            # Use Pydantic's exclude_none to drop optional fields (e.g. distance)
            # because Chroma's metadata schema rejects None values.
            dump = d.model_dump(exclude_none=True)
            dump.pop("umap2d", None)
            dump.pop("umap3d", None)
            dump.pop("umap2d_x", None)
            dump.pop("umap2d_y", None)
            dump.pop("umap3d_x", None)
            dump.pop("umap3d_y", None)
            dump.pop("umap3d_z", None)
            id = f"{d.document_id}-{d.chunk_number}"
            ids.append(id)
            contents.append(dump.pop("content"))
            
            metadatas.append(dump)

        self._collection.add(
            documents=contents,
            metadatas=metadatas,
            ids=ids,
        )

        payload = self._collection.get(ids=ids, include=["embeddings"])
        chunk_embeddings = payload.get("embeddings", [])
        coords2d, coords3d = self._transform_umap(chunk_embeddings)
        if coords2d is not None and coords3d is not None:
            for idx, (c2,c3) in enumerate(zip(coords2d, coords3d)):
                metadatas[idx].update(self._prepare_umap_metadata(c2, c3))
        self._collection.update(ids=ids, metadatas=metadatas)



    # Optional full reindex -----------------------------------------------------

    def reindex(self, kb: "KnowledgeBase") -> int:
        """Rebuild the Chroma index from the current knowledge base state.

        The method iterates over all active markdown files visible to the
        provided knowledge base instance, computing a deterministic document ID
        for each path using the configured ``id_prefix``. Each file is read from
        disk and upserted into the underlying Chroma collection by delegating to
        :meth:`_reindex_document`, ensuring embeddings are recomputed.

        Parameters
        ----------
        kb:
            The :class:`~mcp_kb.knowledge.store.KnowledgeBase` providing access
            to the validated filesystem and utility methods.

        Returns
        -------
        int
            The number of documents processed during the reindex run.
        """

        count = 0
        root = kb.rules.root

        # Clear previous KB documents from the collection. Some Chroma backends
        # do not support regex filters; use substring containment on our stable
        # metadata field instead.
        try:
            self._collection.delete(  # type: ignore[no-untyped-call]
                where={"document_id": {"$contains": f"{self.configuration.id_prefix}"}}
            )
        except Exception:
            # As a fallback, attempt a two-step delete by IDs when supported.
            try:
                payload = self._collection.get(  # type: ignore[no-untyped-call]
                    where={"document_id": {"$contains": f"{self.configuration.id_prefix}"}},
                    include=[],
                )
                ids = payload.get("ids", []) or []
                if ids:
                    self._collection.delete(ids=ids)  # type: ignore[no-untyped-call]
            except Exception:
                # If clearing fails, proceed with reindexing; upserts are idempotent.
                pass

        with tqdm(
            kb.iter_active_files(include_docs=False),
            desc="Reindexing Chroma",
            total=kb.total_active_files(include_docs=False),
        ) as pbar:
            for path in pbar:
                pbar.set_description(f"Reindexing Chroma {path.name}")
                try:
                    content = path.read_text(encoding="utf-8")
                except FileNotFoundError:  # pragma: no cover - race with external edits
                    continue

                relative = path.relative_to(root)
                document_id = f"{self.configuration.id_prefix}{relative}"
                
                self._reindex_document(document_id, content, relative)
                count += 1

        try:
            self._refit_umap_and_update_all()
        except Exception as exc:  # pragma: no cover - refit is best effort
            logger.exception("Failed to refit UMAP models after reindex", exc_info=exc)
        return count

    

    def _resolve_candidate_path(
        self,
        kb: "KnowledgeBase",
        relative: Optional[str],
    ) -> Optional[Path]:
        """Translate metadata hints into a validated path inside ``kb``."""

        
        if not relative:
            return None

        
        candidate = (kb.rules.root / relative).resolve()

        try:
            candidate.relative_to(kb.rules.root)
        except ValueError:
            return None

        if not candidate.exists():
            return None

        return candidate


    def _create_client(self) -> "ClientAPI":
        """Instantiate the proper Chroma client based on configuration.

        The method supports all transport modes referenced in the user
        requirements. It constructs the minimal set of keyword arguments for the
        chosen backend and lets Chroma's client validate the final configuration.
        """

        chroma = self._deps.chroma_module
        config = self.configuration

        if not config.enabled:
            raise RuntimeError(
                "ChromaIngestor cannot be constructed when ingestion is disabled"
            )
        
        settings = chroma.Settings(anonymized_telemetry=False)

        if config.client_type == "ephemeral":
            return chroma.EphemeralClient(settings=settings)

        if config.client_type == "persistent":
            return chroma.PersistentClient(path=str(config.data_directory),settings=settings)

        if config.client_type in {"http", "cloud"}:
            kwargs: Dict[str, Any] = {
                "ssl": config.ssl if config.client_type == "http" else True,
            }
            if config.client_type == "http":
                kwargs["host"] = config.host
                if config.port is not None:
                    kwargs["port"] = config.ports
                if config.custom_auth_credentials:
                    kwargs["settings"] = self._deps.settings_cls(
                        chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                        chroma_client_auth_credentials=config.custom_auth_credentials,
                    )
            else:  # cloud
                kwargs["host"] = config.host or "api.trychroma.com"
                kwargs["tenant"] = config.tenant
                kwargs["database"] = config.database
                kwargs.setdefault("headers", {})
                kwargs["headers"]["x-chroma-token"] = config.api_key

            return chroma.HttpClient(**kwargs)

        raise ValueError(f"Unsupported client type: {config.client_type}")

    def _ensure_collection(self) -> "Collection":
        """Create or return the configured Chroma collection."""

        factory = self._deps.embedding_factories.get(self.configuration.embedding)
        if factory is None:
            available = ", ".join(sorted(self._deps.embedding_factories))
            raise ValueError(
                f"Unknown embedding function '{self.configuration.embedding}'. "
                f"Available options: {available}"
            )
        if issubclass(factory, SentenceTransformerEmbedder):
            embedding_function = factory(self.configuration.sentence_transformer)
        else:
            embedding_function = factory()
        metadata = {"source": "mcp-knowledge-base"}
        client = self._client
        try:
            return client.get_or_create_collection(
                name=self.configuration.collection_name,
                metadata=metadata,
                embedding_function=embedding_function,
            )
        except TypeError:
            # Older Chroma versions expect CreateCollectionConfiguration. Fall back
            # to create_collection for compatibility.
            return client.get_or_create_collection(
                name=self.configuration.collection_name,
                embedding_function=embedding_function,
            )
