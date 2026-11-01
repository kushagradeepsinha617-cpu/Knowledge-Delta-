"""Separate, snapshot-bound NumPy indexes for small corpora; no vector database."""
from dataclasses import dataclass
from hashlib import sha256

from .questions import select_applicable
from .validation import ValidationError, digest

INDEX_VERSION = "numpy-cosine-v1"


def _numpy():
    try:
        import numpy
        return numpy
    except ImportError as exc:
        raise RuntimeError("NumPy is unavailable; install the approved local dependencies explicitly") from exc


def _normalized_rows(vectors, rows, dimension):
    np = _numpy()
    try:
        array = np.asarray(vectors)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Vectors are not a rectangular numeric matrix: {exc}") from exc
    if array.ndim != 2 or array.shape != (rows, dimension):
        raise ValidationError("Vector rows/dimensions do not match the chunks/embedder")
    if array.dtype.kind not in ("f", "i", "u") or not np.isfinite(array).all():
        raise ValidationError("Vectors must contain finite real numbers")
    array = array.astype(np.float64, copy=True)
    if not np.isfinite(array).all():
        raise ValidationError("Vector conversion produced non-finite values")
    if rows:
        norms = np.linalg.norm(array, axis=1)
        if not np.isfinite(norms).all() or (norms <= 0).any():
            raise ValidationError("Vectors must have finite nonzero norms")
        array /= norms[:, None]
    # Backing bytes cannot be made writable by setting an array flag.
    return np.frombuffer(array.tobytes(), dtype=np.float64).reshape(rows, dimension)


@dataclass(frozen=True)
class RetrievalResult:
    chunks: tuple
    scores: tuple[float, ...]
    excluded: tuple
    effective_version: str | None
    version_filter: bool


@dataclass(frozen=True)
class SnapshotIndex:
    snapshot_id: str
    embedder_id: str
    embedder_mode: str
    dimension: int
    chunks: tuple
    matrix: object
    index_id: str
    chunker_configurations: tuple

    def search(self, question, snapshot, embedder, top_k=3, version_filter=False):
        if (snapshot.snapshot_id != self.snapshot_id or embedder.identity != self.embedder_id
                or embedder.mode != self.embedder_mode or embedder.dimension != self.dimension):
            raise ValidationError("Index snapshot/embedder identity does not match the requested run")
        if type(top_k) is not int or not 1 <= top_k <= 20:
            raise ValidationError("top_k must be an integer between 1 and 20")
        effective = question.effective_version(snapshot)
        eligible, excluded = select_applicable(self.chunks, effective, version_filter)
        if not eligible:
            return RetrievalResult((), (), excluded, effective, version_filter)
        query = _normalized_rows(embedder.encode([question.question]), 1, self.dimension)[0]
        scores = self.matrix @ query
        eligible_ids = {chunk.chunk_id for chunk in eligible}
        ranked = sorted(((float(scores[i]), chunk) for i, chunk in enumerate(self.chunks)
                         if chunk.chunk_id in eligible_ids), key=lambda item: (-item[0], item[1].chunk_id))[:top_k]
        return RetrievalResult(tuple(chunk for score, chunk in ranked),
                               tuple(score for score, chunk in ranked), excluded, effective, version_filter)


def validate_chunks(snapshot, chunks):
    """Check evidence integrity independently of optional numeric dependencies."""
    chunks = tuple(chunks)
    seen = set()
    for chunk in chunks:
        doc = snapshot.document(chunk.document_id)
        if (chunk.snapshot_id != snapshot.snapshot_id or chunk.chunk_id in seen
                or type(chunk.start_char) is not int or type(chunk.end_char) is not int
                or not 0 <= chunk.start_char < chunk.end_char <= len(doc.content)
                or chunk.document_content_hash != doc.content_hash
                or chunk.document_metadata_hash != doc.metadata_hash
                or chunk.software_versions != doc.software_versions
                or chunk.source_reference != doc.source_reference
                or chunk.source_revision != doc.source_revision
                or chunk.title != doc.title or chunk.provenance != snapshot.provenance
                or chunk.text != doc.content[chunk.start_char:chunk.end_char]):
            raise ValidationError("Index chunks must uniquely match the snapshot's exact evidence")
        seen.add(chunk.chunk_id)
    return chunks


def build_index(snapshot, chunks, embedder):
    chunks = validate_chunks(snapshot, chunks)
    if type(embedder.dimension) is not int or embedder.dimension < 1:
        raise ValidationError("Embedder dimension must be a positive integer")
    if not isinstance(embedder.identity, str) or not embedder.identity.strip():
        raise ValidationError("Embedder requires a versioned asset identity")
    if embedder.mode not in ("local", "test_double"):
        raise ValidationError("Embedder mode must be local or test_double")
    np = _numpy()
    vectors = embedder.encode([chunk.text for chunk in chunks]) if chunks else np.empty((0, embedder.dimension))
    matrix = _normalized_rows(vectors, len(chunks), embedder.dimension)
    chunker_configurations = tuple(sorted({(chunk.chunker_version, chunk.token_limit,
        chunk.overlap_tokens, chunk.tokenizer_id, chunk.tokenizer_mode) for chunk in chunks}))
    identity = digest({"version": INDEX_VERSION, "snapshot_id": snapshot.snapshot_id,
                       "embedder_id": embedder.identity, "embedder_mode": embedder.mode,
                       "chunks": [chunk.chunk_id for chunk in chunks],
                       "chunker_configurations": chunker_configurations,
                       "dimension": embedder.dimension, "dtype": str(matrix.dtype),
                       "vector_sha256": sha256(matrix.tobytes()).hexdigest()})
    return SnapshotIndex(snapshot.snapshot_id, embedder.identity, embedder.mode,
                         embedder.dimension, chunks, matrix, identity, chunker_configurations)
