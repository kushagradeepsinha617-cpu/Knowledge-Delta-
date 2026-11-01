"""Explicit NumPy integration checks, excluded from the ordinary tests/ directory.

Run with the separately installed project environment:
  .tools/envs/milestone2/Scripts/python.exe -B -m pytest scripts/integration_tests.py -q -p no:cacheprovider

These use REAL NumPy and an explicitly labeled vector-producing test double.
They do not establish Sentence Transformers, tokenizer, or Ollama integration.
Missing NumPy is an actionable setup error, never a skipped or passing check.
"""
from pathlib import Path
import re

import pytest

from knowledge_delta.chunking import chunk_snapshot
from knowledge_delta.questions import QuestionInput
from knowledge_delta.retrieval import build_index, _normalized_rows
from knowledge_delta.snapshots import parse_snapshot
from knowledge_delta.validation import ValidationError


@pytest.fixture(scope="module")
def np():
    try:
        import numpy
    except (ImportError, OSError) as exc:
        pytest.fail(f"Real NumPy integration unavailable: explicitly install the approved local dependency first: {exc}", pytrace=False)
    return numpy


class TokenizerDouble:
    mode = "test_double"
    identity = "numeric-integration-whitespace-double"

    def offsets(self, text):
        return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]

    def count(self, text):
        return len(self.offsets(text)) + 2


class VectorDouble:
    mode = "test_double"
    identity = "numeric-integration-vectors-v1"
    dimension = 2

    def encode(self, texts):
        return [[1.0, 0.0] if "old" in text else [1.0, 1.0] for text in texts]


def snapshot(changed=False, empty=False, unknown=False):
    content = {"v1.md": "old version one", "v2.md": "new version two" + (" updated" if changed else "")}
    raw = {"schema_version": 1, "name": "numeric-integration-fixture", "domain": "constructed",
           "default_version": "1", "provenance": "constructed", "documents": []}
    if not empty:
        raw["documents"] = [{"document_id": "guide-" + version, "path": path,
            "source_reference": "constructed://" + path, "source_revision": "fixture",
            "software_versions": [] if unknown and version == "2" else [version], "title": "Guide " + version}
            for version, path in (("1", "v1.md"), ("2", "v2.md"))]
    return parse_snapshot(raw, Path.cwd(), lambda path: content[path.name].encode("utf-8"))


def index_for(snap):
    return build_index(snap, chunk_snapshot(snap, TokenizerDouble(), 32, 0), VectorDouble())


def test_real_cosine_ranking_and_version_filtering(np):
    snap = snapshot()
    index = index_for(snap)
    question = QuestionInput("numeric", "old question", "explicit_version", "2")
    basic = index.search(question, snap, VectorDouble(), top_k=2, version_filter=False)
    assert basic.chunks[0].software_versions == ("1",)
    assert basic.scores == pytest.approx((1.0, 1 / np.sqrt(2)))
    filtered = index.search(question, snap, VectorDouble(), top_k=2, version_filter=True)
    assert [chunk.software_versions for chunk in filtered.chunks] == [("2",)]
    assert filtered.scores == pytest.approx((1 / np.sqrt(2),))
    assert filtered.excluded[0]["reason"] == "incompatible_version"


def test_real_indexes_are_immutable_isolated_and_snapshot_bound(np):
    before, after = snapshot(), snapshot(changed=True)
    old_index, new_index = index_for(before), index_for(after)
    assert old_index.index_id != new_index.index_id
    assert not np.shares_memory(old_index.matrix, new_index.matrix)
    old_copy = old_index.matrix.copy()
    with pytest.raises(ValueError):
        old_index.matrix.setflags(write=True)
    assert np.array_equal(old_copy, old_index.matrix)
    with pytest.raises(ValidationError, match="identity"):
        old_index.search(QuestionInput("x", "old", "explicit_version", "1"), after, VectorDouble())
    assert old_index.chunks[1].text != new_index.chunks[1].text


def test_real_ties_are_stable_and_configuration_changes_invalidate_identity(np):
    snap = snapshot()
    class EqualVectors(VectorDouble):
        def encode(self, texts):
            return [[1.0, 0.0] for text in texts]
    chunks = chunk_snapshot(snap, TokenizerDouble(), 32, 0)
    index = build_index(snap, chunks, EqualVectors())
    question = QuestionInput("x", "old", "unspecified", None)
    ranked = index.search(question, snap, EqualVectors(), top_k=2)
    assert ranked.scores == (1.0, 1.0)
    assert [chunk.chunk_id for chunk in ranked.chunks] == sorted(chunk.chunk_id for chunk in chunks)
    assert index.index_id == build_index(snap, chunks, EqualVectors()).index_id
    changed_identity = EqualVectors()
    changed_identity.identity = "different-assets"
    assert index.index_id != build_index(snap, chunks, changed_identity).index_id
    other_chunks = chunk_snapshot(snap, TokenizerDouble(), 32, 1)
    assert index.index_id != build_index(snap, other_chunks, EqualVectors()).index_id


def test_real_filter_exposes_unknown_scope_without_inventing_applicability(np):
    snap = snapshot(unknown=True)
    index = index_for(snap)
    question = QuestionInput("x", "old", "explicit_version", "2")
    assert len(index.search(question, snap, VectorDouble(), top_k=2, version_filter=False).chunks) == 2
    filtered = index.search(question, snap, VectorDouble(), version_filter=True)
    assert filtered.chunks == ()
    assert {item["reason"] for item in filtered.excluded} == {"unknown_version_scope", "incompatible_version"}


def test_real_empty_index_and_no_applicable_version(np):
    empty = snapshot(empty=True)
    index = index_for(empty)
    assert index.matrix.shape == (0, 2)
    assert index.search(QuestionInput("x", "old", "explicit_version", "1"), empty, VectorDouble()).chunks == ()
    snap = snapshot()
    result = index_for(snap).search(QuestionInput("x", "old", "explicit_version", "missing"),
                                   snap, VectorDouble(), version_filter=True)
    assert result.chunks == () and len(result.excluded) == 2


@pytest.mark.parametrize("vectors", [
    [[float("nan"), 1]], [[float("inf"), 1]], [[0, 0]], [[True, False]],
    [[1 + 2j, 0]], [["1", "2"]], [[1]], [1, 2], [[1, 0], [0, 1]],
])
def test_real_vector_validation_rejects_invalid_shapes_and_values(np, vectors):
    with pytest.raises(ValidationError):
        _normalized_rows(vectors, 1, 2)


def test_vector_output_dimension_and_configuration_identity_are_enforced(np):
    snap = snapshot()
    index = index_for(snap)
    question = QuestionInput("x", "old", "explicit_version", "1")
    for embedder in (replace_embedder(identity="other"), replace_embedder(dimension=3), replace_embedder(mode="local")):
        with pytest.raises(ValidationError, match="identity"):
            index.search(question, snap, embedder)
    class WrongShape(VectorDouble):
        def encode(self, texts):
            return [[1.0] for text in texts]
    with pytest.raises(ValidationError, match="dimensions"):
        build_index(snap, chunk_snapshot(snap, TokenizerDouble(), 32, 0), WrongShape())


def replace_embedder(**changes):
    embedder = VectorDouble()
    for name, value in changes.items():
        setattr(embedder, name, value)
    return embedder
