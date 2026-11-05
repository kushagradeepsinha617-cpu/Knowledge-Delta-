"""Pydantic batch provenance and isolation checks; no downloads or inference."""
import copy
import json
from pathlib import Path
import shutil

import pytest

from scripts.prepare_pydantic import build_artifacts, draft_relations, extract, verify_bundle, verify_sources
from knowledge_delta.cases import validate_dataset
from knowledge_delta.snapshots import load_snapshot
from knowledge_delta.validation import ValidationError

BASE = Path(__file__).resolve().parents[1] / "examples/pydantic"


@pytest.fixture
def bundle(tmp_path):
    target = tmp_path / "pydantic"
    shutil.copytree(BASE, target)
    return target


def test_pinned_real_sources_and_constructed_version_addition():
    result = verify_bundle(BASE)
    assert result["dataset"]["case_count"] == 10
    assert result["dataset"]["human_reviewed"] + result["dataset"]["draft"] == 10
    assert result["kind"] == "constructed_pydantic_corpus_assembly"
    assert result["downloads_performed"] is False
    assert result["generation_performed"] is False
    assert [item["document_id"] for item in result["changes"]["document_changes"]] == ["pydantic.v1.models"]
    before = load_snapshot(BASE / "before/manifest.json")
    after = load_snapshot(BASE / "after/manifest.json")
    for doc in before.documents:
        other = after.document(doc.document_id)
        assert (doc.content_hash, doc.metadata_hash) == (other.content_hash, other.metadata_hash)
        assert doc.software_versions == ("2.10.6",)
    assert after.document("pydantic.v1.models").software_versions == ("1.10.21",)


def test_source_corruption_and_inventory_revision_tampering_rejected(bundle):
    source = bundle / "sources/v2-migration.md"
    source.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(ValidationError, match="Pinned source changed"):
        verify_sources(bundle)
    shutil.copyfile(BASE / "sources/v2-migration.md", source)
    path = bundle / "sources.json"
    inventory = json.loads(path.read_text(encoding="utf-8"))
    inventory["sources"][0]["revision"] = "fabricated"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(ValidationError, match="verified upstream pin"):
        verify_sources(bundle)


def test_case_keys_never_become_source_documents_and_questions_retain_version():
    _, snapshots, dataset = build_artifacts(BASE)
    for snapshot in snapshots.values():
        assert snapshot.provenance == "constructed"
        assert all(doc.path not in ("cases.json", "recipe.json") for doc in snapshot.documents)
    for case in dataset["cases"]:
        assert case["requested_version"] == "2.10.6"
        assert case["split"] == "development"
        assert case["expectations"]["before"] == case["expectations"]["after"]
        assert case["review"]["status"] == "draft"
        assert case["provenance"] == "constructed"
    assert len({case["family_id"] for case in dataset["cases"]}) == 10


def test_write_refuses_changed_artifacts_before_creating_missing_files(bundle):
    missing = bundle / "before/serialization.md"
    missing.unlink()
    changed = bundle / "after/orm.md"
    changed.write_text("changed work to preserve", encoding="utf-8")
    with pytest.raises(ValidationError, match="Existing artifact differs"):
        verify_bundle(bundle, write=True)
    assert not missing.exists()
    assert changed.read_text(encoding="utf-8") == "changed work to preserve"


def test_write_preserves_explicit_test_only_human_review_on_copied_dataset(bundle):
    path = bundle / "cases.json"
    dataset = json.loads(path.read_text(encoding="utf-8"))
    review = {"status": "human_reviewed", "reviewer": "TEST ONLY reviewer",
              "scope": "Synthetic test metadata, not a project review"}
    dataset["cases"][0]["review"] = review
    path.write_text(json.dumps(dataset), encoding="utf-8")
    (bundle / "relations.json").write_text(json.dumps(draft_relations(dataset)), encoding="utf-8")
    original = path.read_bytes()
    verify_bundle(bundle, write=True)
    assert path.read_bytes() == original


def test_changed_expectation_cannot_be_hidden_as_review_metadata(bundle):
    path = bundle / "cases.json"
    dataset = json.loads(path.read_text(encoding="utf-8"))
    dataset["cases"][0]["expectations"]["after"]["answer"] = "dict() is removed"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    with pytest.raises(ValidationError, match="Case definitions differ"):
        verify_bundle(bundle)


def test_extraction_and_write_reject_ambiguous_or_unsafe_recipe(bundle):
    with pytest.raises(ValidationError, match="exactly once"):
        extract("same same", "same")
    with pytest.raises(ValidationError, match="end not found"):
        extract("start value", "start", "absent")
    path = bundle / "recipe.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data[0]["id"] = "../../escape"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError, match="Unsafe"):
        verify_bundle(bundle, write=True)


def test_supporting_quotes_and_applicability_are_validated():
    _, snapshots, dataset = build_artifacts(BASE)
    invalid = copy.deepcopy(dataset)
    invalid["cases"][0]["requested_version"] = "1.10.21"
    with pytest.raises(ValidationError, match="incompatible"):
        validate_dataset(invalid, snapshots["before"], snapshots["after"])
    invalid = copy.deepcopy(dataset)
    invalid["cases"][0]["expectations"]["after"]["evidence"][0]["quote"] = "fabricated quote"
    with pytest.raises(ValidationError, match="quote not found"):
        validate_dataset(invalid, snapshots["before"], snapshots["after"])


def test_large_source_fixture_preview_is_bounded_and_never_live():
    from knowledge_delta.workflow import fixture_report
    evaluation = fixture_report(BASE / "before/manifest.json", BASE / "after/manifest.json",
                                BASE / "cases.json", BASE / "relations.json")
    assert evaluation["origin"] == "fixture"
    assert len(evaluation["rows"]) == 20
    run = evaluation["raw_run"]
    assert len(run["results"]) == 40
    assert all(trace["generation_performed"] is False for trace in run["results"])
    assert any(p["context_selection"] == "fixture_gold_quote_window"
               for trace in run["results"] for p in trace["retrieved_passages"])
    for trace in run["results"]:
        snapshot = load_snapshot(BASE / trace["snapshot_slot"] / "manifest.json")
        for passage in trace["retrieved_passages"]:
            doc = snapshot.document(passage["document_id"])
            assert passage["text"] == doc.content[passage["start_char"]:passage["end_char"]]
