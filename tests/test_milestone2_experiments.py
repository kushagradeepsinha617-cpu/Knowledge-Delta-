"""Experiment orchestration with explicitly labeled doubles; no vector/model benchmark."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge_delta.experiments import run_dataset
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError, read_json

ROOT = Path(__file__).resolve().parents[1]


class TokenizerDouble:
    identity = "fixture-character-tokenizer"
    mode = "test_double"

    def offsets(self, text):
        return [(i, i + 1) for i in range(len(text))]

    def count(self, text):
        return len(text) + 2


class EmptyIndexDouble:
    embedder_mode = "test_double"
    chunker_configurations = (("fixture", 128, 16, "fixture-character-tokenizer", "test_double"),)
    chunks = ()

    def __init__(self, snapshot, chunks, embedder):
        self.index_id = "fixture-index-" + snapshot.snapshot_id

    def search(self, question, snapshot, embedder, **settings):
        return SimpleNamespace(chunks=(), scores=(), excluded=(),
                               effective_version=question.effective_version(snapshot))


def inputs():
    directory = ROOT / "examples/constructed"
    return (read_json(directory / "cases.json"), load_snapshot(directory / "before/manifest.json"),
            load_snapshot(directory / "after/manifest.json"))


def doubles():
    embedder = SimpleNamespace(mode="test_double", identity="fixture-embedder", tokenizer=TokenizerDouble())
    client = SimpleNamespace(model="fixture-model", transport=SimpleNamespace(mode="test_double"))
    return embedder, client


def test_full_experiment_preserves_versions_drafts_controls_and_repetitions():
    dataset, before, after = inputs()
    embedder, client = doubles()
    result = run_dataset(dataset, before, after, embedder, client, repeats=2, index_factory=EmptyIndexDouble)
    assert result["counts"] == {"planned": 56, "recorded": 56, "run_errors": 0, "awaiting_semantic_review": 56}
    assert result["origin"] == "test_double" and result["correctness_measured"] is False
    assert result["answer_cache_used"] is False
    basic, filtered = result["configurations"].values()
    assert {key for key in basic if basic[key] != filtered[key]} == {"version_filter"}
    for case in dataset["cases"]:
        records = [item for item in result["results"] if item["case_id"] == case["case_id"]]
        assert len(records) == 8
        assert {item["requested_version"] for item in records} == {case["requested_version"]}
        assert all(item["case_review_status"] == "draft" and item["judgment"] == "needs_human_review" for item in records)
        assert all(item["generation_performed"] is False for item in records)


def test_index_failure_keeps_every_planned_case_as_error_instead_of_excluding_it():
    dataset, before, after = inputs()
    embedder, client = doubles()
    def failing_index(*args):
        raise ValidationError("injected index failure")
    result = run_dataset(dataset, before, after, embedder, client, index_factory=failing_index)
    assert result["counts"] == {"planned": 28, "recorded": 28, "run_errors": 28, "awaiting_semantic_review": 0}
    assert result["status"] == "completed_with_run_errors" and len(result["errors"]) == 2
    assert all(item["error_phase"] == "index" for item in result["results"])
    assert all(item["case_review_status"] == "draft" and item["case_provenance"] == "constructed"
               and item["case_split"] == "development" for item in result["results"])


def test_dataset_snapshot_mismatch_is_rejected_before_index_construction():
    dataset, before, after = inputs()
    dataset = deepcopy(dataset)
    dataset["snapshot_ids"]["before"] = "wrong"
    embedder, client = doubles()
    def forbidden_index(*args):
        raise AssertionError("must validate dataset first")
    with pytest.raises(ValidationError):
        run_dataset(dataset, before, after, embedder, client, index_factory=forbidden_index)
