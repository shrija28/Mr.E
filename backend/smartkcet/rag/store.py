"""FAISS vector stores for the RAG pipeline.

Per-subject isolation contract (REQ-5.1, REQ-8.5, design.md §2 / §2.1 / §2.2):

    Uploads scoped to a subject MUST never disturb any other subject's
    FAISS index or chunk list.  ``SubjectVectorStores`` enforces this by
    keeping a separate :class:`VectorStore` per :class:`~smartkcet.db.models.Subject`
    and persisting each one to its own pair of files under
    ``backend/data/faiss/{subject}.index`` (FAISS binary) and
    ``backend/data/faiss/{subject}.chunks.json`` (JSON list of chunk
    strings).

The ``embedder`` (``sentence-transformers`` MiniLM) is shared across all
subjects since it is a stateless encoder.  Only the FAISS index and the
parallel ``chunks`` list are per-subject.

NOTE: Python 3.14 compatibility
-------

``sentence-transformers`` hangs on import with Python 3.14 (model loading issues).
We defer embedder initialization until first use via a lazy loader.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import faiss

from ..db.models import Subject

# Lazy embedder initialization to avoid hang on Python 3.14
# The model is not loaded until first use
_embedder: Optional[object] = None
_embedder_loading_attempted = False


def _get_embedder():
    """Lazy load the SentenceTransformer embedder on first use."""
    global _embedder, _embedder_loading_attempted
    
    if _embedder is not None:
        return _embedder
    
    if _embedder_loading_attempted and _embedder is None:
        # Already tried to load and failed - don't retry
        raise RuntimeError(
            "sentence-transformers not available. "
            "Embedding/FAISS functionality will not work."
        )
    
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _embedder_loading_attempted = True
        return _embedder
    except Exception as e:
        _embedder_loading_attempted = True
        raise RuntimeError(f"Failed to load sentence-transformers: {e}")


# For backward compatibility, provide an embedder property that lazy-loads
class _EmbedderProxy:
    """Proxy that lazy-loads the embedder on first access."""
    def encode(self, *args, **kwargs):
        embedder = _get_embedder()
        return embedder.encode(*args, **kwargs)


embedder = _EmbedderProxy()

# ``backend/data/faiss/`` resolved relative to the backend root, mirroring
# the path-resolution pattern used by ``smartkcet.db.session``.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_FAISS_DIR = _BACKEND_ROOT / "data" / "faiss"

# Type alias for inputs that select a subject.  Callers may pass either a
# ``Subject`` enum value or its string name; both are normalised internally.
SubjectLike = Union[Subject, str]


class VectorStore:
    """In-memory FAISS L2 index plus the original chunk text.

    This class is the per-subject building block used by
    :class:`SubjectVectorStores`.  It carries no knowledge of which
    subject it represents — that mapping is owned by the parent store.
    """

    def __init__(self) -> None:
        self.index = None  # ``faiss.IndexFlatL2`` once initialised
        self.chunks: List[str] = []
        self.dim = 384

    def reset(self) -> None:
        self.index = faiss.IndexFlatL2(self.dim)
        self.chunks = []

    def add(self, texts: Iterable[str]) -> None:
        if self.index is None:
            self.reset()
        texts = list(texts)
        if not texts:
            return
        vecs = embedder.encode(texts, show_progress_bar=False).astype("float32")
        self.index.add(vecs)
        self.chunks.extend(texts)

    def search(self, query: str, k: int = 20) -> List[str]:
        if not self.chunks:
            return []
        vec = embedder.encode([query]).astype("float32")
        k = min(k, len(self.chunks))
        _, ids = self.index.search(vec, k)
        return [self.chunks[i] for i in ids[0] if i < len(self.chunks)]


class SubjectVectorStores:
    """Per-subject FAISS stores with lazy load + on-write persistence.

    Each :class:`Subject` gets its own :class:`VectorStore`.  Mutations
    (``add``/``reset``) are scoped strictly to the requested subject; no
    code path here ever touches another subject's index or chunk list,
    which preserves the isolation contract from REQ-5.1.

    Persistence layout under ``self.data_dir`` (default
    ``backend/data/faiss/``):

        Biology.index, Biology.chunks.json
        Physics.index, Physics.chunks.json
        Chemistry.index, Chemistry.chunks.json
        Mathematics.index, Mathematics.chunks.json
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir: Path = Path(data_dir) if data_dir is not None else _DEFAULT_FAISS_DIR
        self._stores: Dict[Subject, VectorStore] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(subject: SubjectLike) -> Subject:
        """Accept a ``Subject`` enum or its string name, return the enum."""

        if isinstance(subject, Subject):
            return subject
        if isinstance(subject, str):
            try:
                return Subject(subject)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError(
                    f"Unknown subject {subject!r}; expected one of "
                    f"{[s.value for s in Subject]}"
                ) from exc
        raise TypeError(
            f"subject must be Subject or str, got {type(subject).__name__}"
        )

    def _index_path(self, subject: Subject) -> Path:
        return self.data_dir / f"{subject.value}.index"

    def _chunks_path(self, subject: Subject) -> Path:
        return self.data_dir / f"{subject.value}.chunks.json"

    def _ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load(self, subject: Subject) -> VectorStore:
        """Read the persisted index + chunks for ``subject`` from disk.

        Returns a fresh :class:`VectorStore` populated from disk if both
        files exist; otherwise returns a fresh empty store.
        """

        vs = VectorStore()
        idx_path = self._index_path(subject)
        chunks_path = self._chunks_path(subject)
        if idx_path.exists() and chunks_path.exists():
            try:
                vs.index = faiss.read_index(str(idx_path))
                with chunks_path.open("r", encoding="utf-8") as fp:
                    chunks = json.load(fp)
                if isinstance(chunks, list):
                    vs.chunks = [str(c) for c in chunks]
            except (OSError, ValueError, RuntimeError):
                # Corrupt or unreadable persisted state — start clean
                # rather than crash the whole RAG service.
                vs = VectorStore()
        return vs

    def _persist(self, subject: Subject, vs: VectorStore) -> None:
        """Write the in-memory state for ``subject`` to disk."""

        self._ensure_data_dir()
        if vs.index is not None:
            faiss.write_index(vs.index, str(self._index_path(subject)))
        with self._chunks_path(subject).open("w", encoding="utf-8") as fp:
            json.dump(vs.chunks, fp, ensure_ascii=False)

    def _get(self, subject: Subject) -> VectorStore:
        """Return the cached store for ``subject``, lazy-loading on miss."""

        vs = self._stores.get(subject)
        if vs is None:
            vs = self._load(subject)
            self._stores[subject] = vs
        return vs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, subject: SubjectLike, texts: Iterable[str]) -> None:
        """Append ``texts`` to ``subject``'s index. Other subjects untouched."""

        s = self._normalize(subject)
        vs = self._get(s)
        before = len(vs.chunks)
        vs.add(texts)
        # Skip the disk write if nothing changed (empty ``texts``) so we
        # don't churn timestamps on no-op calls.
        if len(vs.chunks) != before:
            self._persist(s, vs)

    def search(self, subject: SubjectLike, query: str, k: int = 20) -> List[str]:
        """Search only ``subject``'s index; never reads other subjects."""

        s = self._normalize(subject)
        return self._get(s).search(query, k)

    def reset(self, subject: SubjectLike) -> None:
        """Clear ``subject``'s in-memory state and remove its persisted files."""

        s = self._normalize(subject)
        vs = self._get(s)
        vs.reset()
        for path in (self._index_path(s), self._chunks_path(s)):
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def reset_all(self) -> None:
        """Clear every subject's state. Useful for tests and admin reset."""

        for s in Subject:
            self.reset(s)

    def chunk_count(self, subject: SubjectLike) -> int:
        """Return the number of indexed chunks for ``subject``."""

        s = self._normalize(subject)
        return len(self._get(s).chunks)


# Module-level singleton used by the per-subject upload/generate routes
# introduced in tasks 4.3 and 4.5.
stores = SubjectVectorStores()

# Backwards-compat alias for the legacy single-store routes in
# ``smartkcet.routes.legacy``.  Those endpoints predate per-subject
# isolation and operate on a single, in-memory vector store; they will be
# retired in later tasks (5.x / 7.x) when the new admin upload/generate
# endpoints replace them.  Keeping ``store`` as a separate
# :class:`VectorStore` instance is the simplest way to leave that legacy
# path untouched while the new ``stores`` singleton owns all
# subject-scoped state.
store = VectorStore()


__all__ = [
    "embedder",
    "VectorStore",
    "SubjectVectorStores",
    "SubjectLike",
    "stores",
    "store",
]
