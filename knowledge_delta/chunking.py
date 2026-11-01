"""Exact-text chunks with an explicit tokenizer contract; no downloads or imports of ML libraries."""
from dataclasses import dataclass
from typing import Protocol

from .snapshots import Document, Snapshot
from .validation import ValidationError, digest

CHUNKER_VERSION = "offset-chunks-v1"


class Tokenizer(Protocol):
    identity: str
    mode: str

    def offsets(self, text: str) -> list[tuple[int, int]]:
        """Return non-special-token character offsets in the original text."""

    def count(self, text: str) -> int:
        """Count the actual model input, INCLUDING special tokens; never truncate."""


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    snapshot_id: str
    document_id: str
    document_content_hash: str
    document_metadata_hash: str
    software_versions: tuple[str, ...]
    source_reference: str
    source_revision: str | None
    title: str
    text: str
    start_char: int
    end_char: int
    token_count: int
    token_limit: int
    tokenizer_id: str
    tokenizer_mode: str
    provenance: str
    overlap_tokens: int
    chunker_version: str


def _count(tokenizer, text):
    count = tokenizer.count(text)
    if type(count) is not int or count < 0:
        raise ValidationError("tokenizer count must be a nonnegative integer")
    return count


def _budget(tokenizer, token_limit, overlap_tokens):
    if type(token_limit) is not int or token_limit < 1:
        raise ValidationError("token limit must be a positive integer")
    if type(overlap_tokens) is not int or not 0 <= overlap_tokens < token_limit:
        raise ValidationError("overlap must be a nonnegative integer below the token limit")
    if not isinstance(tokenizer.identity, str) or not tokenizer.identity:
        raise ValidationError("tokenizer requires a versioned asset identity")
    if tokenizer.mode not in ("local", "test_double"):
        raise ValidationError("tokenizer mode must be local or test_double")
    overhead = _count(tokenizer, "")
    budget = token_limit - overhead
    if budget <= 0:
        raise ValidationError("token limit leaves no room after special tokens")
    return budget


def chunk_document(document: Document, snapshot: Snapshot, tokenizer: Tokenizer,
                   token_limit: int, overlap_tokens: int = 24) -> tuple[Chunk, ...]:
    budget = _budget(tokenizer, token_limit, overlap_tokens)
    if snapshot.document(document.document_id) != document:
        raise ValidationError("document content/metadata does not belong to the selected snapshot")
    offsets = tokenizer.offsets(document.content)
    previous_start, previous_end = -1, -1
    for offset in offsets:
        if (not isinstance(offset, (tuple, list)) or len(offset) != 2
                or any(type(value) is not int for value in offset)):
            raise ValidationError("tokenizer offsets must be integer pairs")
        start, end = offset
        if not (0 <= start < end <= len(document.content)) or start < previous_start or end < previous_end:
            raise ValidationError("tokenizer offsets must be ordered original-text spans")
        previous_start, previous_end = start, end
    chunks, start_token = [], 0
    while start_token < len(offsets):
        end_token = min(len(offsets), start_token + budget)
        start_char = 0 if start_token == 0 else offsets[start_token][0]
        # Include whitespace before the next token and preserve the trailing text.
        while end_token > start_token:
            end_char = offsets[end_token][0] if end_token < len(offsets) else len(document.content)
            if end_char <= start_char:
                end_token -= 1
                continue
            text = document.content[start_char:end_char]
            count = _count(tokenizer, text)
            if count <= token_limit:
                break
            end_token -= 1
        if end_token <= start_token:
            raise ValidationError(f"{document.document_id}: a token span cannot fit without truncation")
        identity = {
            "version": CHUNKER_VERSION, "snapshot_id": snapshot.snapshot_id,
            "document_id": document.document_id, "content_hash": document.content_hash,
            "metadata_hash": document.metadata_hash, "tokenizer_id": tokenizer.identity,
            "tokenizer_mode": tokenizer.mode,
            "token_limit": token_limit, "overlap_tokens": overlap_tokens,
            "start_char": start_char, "end_char": end_char,
        }
        chunks.append(Chunk(
            "chunk-" + digest(identity), snapshot.snapshot_id, document.document_id,
            document.content_hash, document.metadata_hash, document.software_versions,
            document.source_reference, document.source_revision, document.title,
            text, start_char, end_char, count, token_limit, tokenizer.identity,
            tokenizer.mode, snapshot.provenance, overlap_tokens, CHUNKER_VERSION,
        ))
        if end_token == len(offsets):
            break
        start_token = max(start_token + 1, end_token - overlap_tokens)
        # Multiple tokens can map to the same original Unicode character span.
        # Advancing a token alone can repeat an identical chunk/ID; advance to
        # a later character boundary while retaining already-covered text.
        while start_token < len(offsets) and offsets[start_token][0] <= start_char:
            start_token += 1
    return tuple(chunks)


def chunk_snapshot(snapshot: Snapshot, tokenizer: Tokenizer, token_limit: int,
                   overlap_tokens: int = 24) -> tuple[Chunk, ...]:
    _budget(tokenizer, token_limit, overlap_tokens)
    return tuple(chunk for document in snapshot.documents
                 for chunk in chunk_document(document, snapshot, tokenizer, token_limit, overlap_tokens))
